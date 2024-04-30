from core import createMachine, state, transition, interpret

machine = createMachine({
    'off': state(
        transition('toggle', 'on')
    ),
    'on': state(
        transition('toggle', 'off')
    )
})

service = interpret(machine, lambda x: print(x))
print(service.machine.current)  # off
service.send('toggle')
print(service.machine.current)  # on