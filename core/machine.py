from typing import Any, Callable, List, Dict, Union
import sys
import asyncio


class Debugger:
    _onEnter: Callable
    _create: Callable
    _send: Callable


d = Debugger()
def empty(): return dict()


identity: Callable = lambda *x: x[0]


def filter(Type, arr):
    return [x for x in arr if isinstance(x, Type)]


class Fn:
    def __init__(self, fn: Callable):
        self.fn = fn

    def __call__(self, context: Dict, event: Dict) -> Dict:
        try:
            return self.fn(context, event)
        except TypeError:
            try:
                return self.fn(context)
            except TypeError:
                return self.fn()


def stackGuards(fns: List[Fn]):
    def retFn(ctx, ev):
        accu = True
        for fn in fns:
            accu = accu and fn(ctx, ev)
        return accu
    return retFn


def stackReducers(fns: List[Fn]):
    def retFn(s, ctx, ev):
        accu = ctx
        for fn in fns:
            accu = fn(accu, ev)
        return accu
    return retFn


class reduce(Fn):
    pass


class action(reduce):
    def __call__(self, context: Dict, event: Dict) -> Dict:
        super().__call__(context, event)
        return context


class guard(Fn):
    pass


class Transition:
    def __init__(self, from_: str, to: str, guards: List[guard], reducers: List[reduce]):
        self.from_ = from_
        self.to = to
        self.guards = guards
        self.reducers = reducers


def makeTransition(Type, from_, to, *args):
    guards = stackGuards([t for t in filter(guard, args)])
    reducers = stackReducers([t for t in filter(reduce, args)])

    return Type(from_=from_,
                to=to,
                guards=guards,
                reducers=reducers)


class Immediate(Transition):
    pass


def transition(*args):
    return makeTransition(Transition, *args)


def immediate(*args):
    return makeTransition(Immediate, None, *args)


class State:
    def __init__(self, enter: Callable = identity, transitions: Dict[str, List[Transition]] = {}, final: bool = False, immediates: List[Immediate] = []):
        self.enter = enter
        self.transitions = transitions
        self.final = final
        self.immediates = immediates


def state(*args: Transition):
    transitions = filter(Transition, args)
    immediates = filter(Immediate, args)
    desc = State(final=len(args) == 0,
                 transitions=transitionToMap(transitions))
    if len(immediates) > 0:
        desc.immediates = immediates
        desc.enter = lambda *args: enterImmediate(desc, *args)
    return desc


class MachineDef:
    def __init__(self, name: str, value: State):
        self.name = name
        self.value = value


class Machine:
    def __init__(self, current: str, states: List[State], context: Callable, original: dict = None):
        self.current = current
        self.states = states
        self.context = context
        self.original = original

    @property
    def state(self):
        return MachineDef(self.current, self.states[self.current])


def createMachine(current: Union[str, Dict], states: Union[Dict[str, State], Callable] = None, contextFn: Callable = empty):
    if sys.implementation.name == 'micropython' and type(current) is not str:
        raise Exception('current (initial state) must be provided')
    if type(current) is not str:
        contextFn = states or empty
        states = current
        current = list(states.keys())[0]
    if hasattr(d, '_create'):
        d._create(current, states)
    return Machine(current=current,
                   states=states,
                   context=contextFn)


class Service:
    def __init__(self, machine: Machine, context: Dict, onChange: Callable, child=None):
        self.machine = machine
        self.context = context
        self.onChange = onChange
        self.child = None

    def send(self, event):
        send(self, event)


def interpret(machine: Machine, onChange: Callable, initialContext: Dict = {}, event=None):
    try:
        context = machine.context(initialContext, event)
    except TypeError:
        try:
            context = machine.context(initialContext)
        except TypeError:
            context = machine.context()
    s = Service(
        machine=machine,
        context=context,
        onChange=onChange
    )
    s.machine = s.machine.state.value.enter(s.machine, s, event)
    return s


def send(service: Service, event):
    if hasattr(event, 'type'):
        eventName = event.type
    elif hasattr(event, '__getitem__'):
        eventName = event['type']
    else:
        eventName = event
    machine = service.machine
    state = machine.state.value
    currentStateName = machine.state.name

    if eventName in state.transitions:
        return transitionTo(service, machine, event, state.transitions.get(eventName)) or machine
    else:
        if hasattr(d, '_send'):
            d._send(eventName, currentStateName)
    return machine


def transitionToMap(transitions: List[Transition]) -> Dict[str, Transition]:
    m = dict()
    for t in transitions:
        if not t.from_ in m:
            m[t.from_] = []
        m[t.from_].append(t)
    return m


def enterImmediate(self, machine: Machine, service: Service, event: Dict):
    return transitionTo(service, machine, event, self.immediates) or machine


class Invoke:
    def __init__(self, transitions: Dict):
        self.transitions = transitions


class InvokeFn(Fn, Invoke):

    def __init__(self, fn: Callable, transitions: Dict, ):
        Fn.__init__(self, fn=fn)
        Invoke.__init__(self, transitions=transitions)

    def enter(self, machine2: Machine, service: Service, event):
        try:
            rn = self.fn(service, service.context, event)
        except TypeError:
            try:
                rn = self.fn(service, service.context)
            except TypeError:
                rn = self.fn()
        if isinstance(rn, Machine):
            return InvokeMachine(machine=rn,
                                 transitions=self.transitions
                                 ).enter(machine2, service, event)

        async def doneCallback(fn):
            try:
                data = await fn(service.context, event)
                service.send({'type': 'done', 'data': data})
            except Exception as error:
                service.send({'type': 'error', 'error': error})

        loop = asyncio.get_event_loop()
        loop.run_until_complete(doneCallback(self.fn))

        return machine2


class InvokeMachine(Invoke):
    def __init__(self, transitions: Dict, machine: Machine):
        super().__init__(transitions=transitions)
        self.machine = machine

    def enter(self, machine: Machine, service: Service, event):
        def onChange(s: Service):
            try:
                service.onChange(s)
            except TypeError:
                service.onChange()
            if service.child == s and isinstance(s.machine.state.value, State) and s.machine.state.value.final:
                service.child = None
                service.send({'type': 'done', 'data': s.context})
        service.child = interpret(
            self.machine, onChange, service.context, event)
        if isinstance(service.child.machine.state.value, State) and service.child.machine.state.value.final:
            data = service.child.context
            service.child = None
            return transitionTo(service, machine, {'type': 'done', 'data': data}, self.transitions['done'])
        return machine


def invoke(fn, *transitions):
    t = transitionToMap(transitions)
    if isinstance(fn, Machine):
        return InvokeMachine(
            machine=fn,
            transitions=t
        )
    else:
        return InvokeFn(
            fn=fn,
            transitions=t
        )


def transitionTo(service: Service, machine: Machine, fromEvent, candidates: List[Transition]):
    context = service.context
    for c in candidates:
        if c.guards(service.context, fromEvent):
            service.context = c.reducers(service, service.context, fromEvent)

            original = machine.original or machine
            newMachine = Machine(current=c.to,
                                 states=original.states,
                                 context=original.context,
                                 original=original)

            if hasattr(d, '_onEnter'):
                d._onEnter(machine, c.to, service.context, context, fromEvent)
            state = newMachine.state.value
            service.machine = newMachine
            try:
                service.onChange(service)
            except TypeError:
                service.onChange()
            return state.enter(newMachine, service, fromEvent)
