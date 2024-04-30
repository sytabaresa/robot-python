import unittest
import asyncio

from core.machine import createMachine, state, transition, reduce, interpret, invoke, state as final, immediate

class TestInvokeAsync(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestInvokeAsync, self).__init__(*args, **kwargs)
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
    async def dummy():
            pass
    
    async def test_done(self):
        '''
        Goes to the "done" event when complete
        '''
        async def promise():
            return 13
        machine = createMachine({
            'one': state(
                transition('click', 'two')
            ),
            'two': invoke(promise,
                          transition('done', 'three',
                                     reduce(lambda ctx, ev: ctx | {'age': ev.data}))),
            'three': state()
        }, lambda : {'age': 0})

        service = interpret(machine, lambda : {})
        service.send('click')
        self.loop.run_until_complete(self.dummy)
        await asyncio.sleep(1)
        self.assertEqual(service.machine.current, 'three', 'now in the next state')
        self.assertEqual(service.context['age'], 13, 'Invoked')
        
    async def test_error(self):
        '''
        Goes to the "error" event when there is an error
        '''
        async def promise():
            raise Exception('oh no')
        machine = createMachine({
            'one': state(
                transition('click', 'two')
            ),
            'two': invoke(promise,
                          transition('error', 'three',
                                     reduce(lambda ctx, ev: ctx | {'error': ev.error}))),
            'three': state()
        }, lambda : {'age': 0})
        
        service = interpret(machine, lambda : {})
        service.send('click')
        self.loop.run_until_complete(self.dummy)
        await asyncio.sleep(1)
        self.assertEqual(service.machine.current, 'three', 'now in the next state')
        self.assertEqual(service.context['age'], 13, 'Invoked')
   
    async def test_invoke_initial(self):
        '''
        The initial state can be an invoke
        '''
        async def promise():
            return 2
        machine = createMachine({
            'one': invoke(promise,
                          transition('done', 'two', reduce(lambda ctx, ev: ctx | {'age': ev.data}))),
            'two': state()
        }, lambda : {'age': 0})

        service = interpret(machine, lambda : {})
        self.loop.run_until_complete(self.dummy)
        await asyncio.sleep(1)
        self.assertEqual(service.context['age'], 2, 'Invoked immediately')
        self.assertEqual(service.machine.current, 'two', 'in the new state')    
    
    
class TestInvokeMachine(unittest.TestCase): 
    def test_child_machine(self):
        '''
        Can invoke a child machine
        '''
        one = createMachine({
            'nestedOne': state(
                transition('go', 'nestedTwo')
            ),
            'nestedTwo': final()
        })
        two = createMachine({
            'one': state(
                transition('go', 'two')
            ),
            'two': invoke(one, 
                          transition('done', 'three')),
            'three': final()
        })
        c = 0
        
        def aux(thisService):
            nonlocal c
            match c:
                case 0:
                    self.assertEqual(service.machine.current, 'two')
                case 1:
                    self.assertNotEqual(thisService, service, 'second time a different service')
                case 2:
                    self.assertEqual(service.machine.current, 'three', 'now in three state')
            c += 1
        service = interpret(two,aux)
        service.send('go')
        service.child.send('go')
        self.assertEqual(c, 3, 'there were 3 transitions')
      
    def test_dynamic_child_machine(self):
        '''
        Can invoke a dynamic child machine
        '''
        dynamicMachines = [
            createMachine({
                'nestedOne': state(
                    transition('go', 'nestedTwo')
                ),
                'nestedTwo': final()
            }),
            createMachine({
                'nestedThree': state(
                    transition('go', 'nestedFour')
                ),
                'nestedFour': final()
            })
        ]
        
        root = createMachine({
            'one': state(
                transition('go', 'two')
            ),
            'two': invoke(lambda : dynamicMachines[0], 
                          transition('done', 'three')),
            'three': state(
                transition('go', 'four')
            ),
            'four': invoke(lambda : dynamicMachines[1], 
                          transition('done', 'five')),
            'five': final()
        })
        c = 0 
        def aux(thisService):
            nonlocal c
            match c:
                case 0:
                    self.assertEqual(service.machine.current, 'two')
                case 1:
                    self.assertNotEqual(thisService, service, 'second time a different service')
                    self.assertEqual(thisService.machine.current, 'nestedTwo')
                case 2:
                    self.assertEqual(thisService, service, 'equal service')
                    self.assertEqual(thisService.machine.current, 'three', 'now in three state')
                case 3:
                    self.assertEqual(service.machine.current, 'four')
                case 4:
                    self.assertNotEqual(thisService, service, 'third time a different service')
                    self.assertEqual(thisService.machine.current, 'nestedFour')
                case 5:
                    self.assertEqual(service.machine.current, 'five', 'now in five state')
            c += 1
        service = interpret(root,aux)
        service.send('go')
        service.child.send('go')
        service.send('go')
        service.child.send('go')
        self.assertEqual(c, 6, 'there were 6 transitions')    
        
    async def test_child_receive_events(self):
        '''
        Child machines receive events from their parents
        '''
        def action(fn):
            def ret(ctx, ev):
                fn(ctx, ev)
                return ctx
            return reduce(ret)
                
            
        child = createMachine({
            'init': state(
                immediate('waiting', action(lambda ctx: ctx['stuff'].append(1)))
            ),
            'waiting': invoke(asyncio.sleep(5),
                              transition('done' 'fin', 
                                         action(lambda ctx: ctx['stuff'].append(2)))
            ),
            'fin': final()
        }, lambda ctx: ctx)
        
        machine = createMachine({
            'idle': state(transition('next', 'child')),
            'child': invoke(child, transition('done', 'end')),
            'end': final()
        }, lambda : {'stuff': []})
       
        service = interpret(machine, lambda : {})
        service.send('next')
        
        await asyncio.sleep(5)
        
        self.assertListEqual(service.context['stuff'], [1,2])   
    
    def test_no_child(self):
        '''
        Service does not have a child when not in an invoked state
        '''
        child = createMachine({
            'nestedOne': state(transition('next', 'nestedTwo')),
            'nestedTwo': state()
        })
        parent = createMachine({
            'one': invoke(child, 
                          transition('done', 'two')),
            'two': state()
        })
        
        service = interpret(parent, lambda : {})
        self.assertNotEqual(service.child, None, 'there is a child service')
        
        service.child.send('next')
        self.assertEqual(service.child, None, 'No longer a child')
        
    def test_multi_level(self):
        '''
        Multi level nested machines resolve in correct order
        '''
        four = createMachine({
          'init': state(
              transition('START', 'start')
          ),
          'start': state(
              transition('DONE', 'done')
          ),
          'done': final()
        })
        
        three = createMachine({
          'init': state(
              transition('START', 'start')
          ),
          'start': invoke(four,
                          transition('done', 'done')),
          'done': final()
        })
        
        two = createMachine({
          'init': state(
              transition('START', 'start')
          ),
          'start': invoke(three,
                          transition('done', 'done')),
          'done': final()
        })
        
        one = createMachine({
          'init': state(
              transition('START', 'start')
          ),
          'start': invoke(two,
                          transition('done', 'done')),
          'done': final()
        })
        c = 0
        def aux(thisService):
            nonlocal c
            match c:
                case 0:
                    self.assertEqual(service.machine.current, 'start', 'initial state')
                case 1:
                    self.assertNotEqual(thisService.machine.states, service.machine.states, 'second time a different service')
                    self.assertNotEqual(service.child, None, 'has child')
                    self.assertEqual(service.child.machine.current, 'start')
                case 2:
                    self.assertNotEqual(service.child.child, None, 'has grand child')
                    self.assertEqual(service.child.machine.current, 'start')
                    self.assertEqual(service.child.child.machine.current, 'start')
                case 3:
                    self.assertNotEqual(service.child.child.child, None, 'has grand grand child')
                    self.assertEqual(service.child.child.machine.current, 'start')
                    self.assertEqual(service.child.child.child.machine.current, 'start')
                case 4:
                    self.assertEqual(service.child.child.child.machine.current, 'done')
                case 5:
                    self.assertEqual(service.child.child.machine.current, 'done')
                    self.assertEqual(service.child.child.child, None, 'child is removed when resolved')
                case 6:
                    self.assertEqual(service.child.machine.current, 'done')
                    self.assertEqual(service.child.child, None, 'child is removed when resolved')
                case 7:
                    self.assertEqual(service.machine.current, 'done')
                    self.assertEqual(service.child, None, 'child is removed when resolved')
          
            c += 1
        service = interpret(one, aux)
        service.send('START') # machine one
        service.child.send('START') # machine two
        service.child.child.send('START') # machine three
        service.child.child.child.send('START') # machine four
        service.child.child.child.send('DONE') # machine four
        self.assertEqual(c, 8, 'there were 8 transitions')   
        
    def test_immediate_finish(self):
        '''
        Invoking a machine that immediately finishes
        '''
        expectations = ['two', 'nestedTwo', 'three']
        
        child = createMachine({
            'nestedOne': state(
                immediate('nestedTwo')
            ),
            'nestedTwo': final()
        })
        
        parent = createMachine({
            'one': state(
                transition('next', 'two')
            ),
            'two': invoke(child,
                          transition('done', 'three')
            ),
            'three': final()
        })
        
        def aux(s):
            nonlocal expectations
            # TODO not totally sure if this is correct, but I think it should
            # hit this only once and be equal to three
            self.assertEqual(s.machine.current, expectations[0])
            expectations = expectations[1:] 
        service = interpret(parent,aux)
        service.send('next')
        
if __name__ == '__main__':
    unittest.main()