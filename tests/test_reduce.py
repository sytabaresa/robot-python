import unittest

from core.machine import createMachine, state, transition, reduce, interpret

class TestReduce(unittest.TestCase):

    def test_basic_state_change(self):
        '''
        Basic state change
        '''
        machine = createMachine({
            'one': state(
                transition('ping', 'two', 
                           reduce(lambda ctx: ctx | {'one': 1}),
                           reduce(lambda ctx: ctx | {'two': 2})
                           )
            ),
            'two': state()
        })

        service = interpret(machine, lambda : {})
        service.send('ping')
        
        self.assertEqual(service.context['one'], 1, 'first reducer ran')
        self.assertEqual(service.context['two'], 2, 'second reducer ran')
        
    def test_context_remains(self):
        '''
        If no reducers, the context remains
        '''
        machine = createMachine({
            'one': state(
                transition('go', 'two')
            ),
            'two': state()
        }, lambda : {'one': 1, 'two': 2})
        
        service = interpret(machine, lambda : {})
        service.send('go')
        self.assertDictEqual(service.context, {'one': 1, 'two': 2}, 'context remains')

    def test_event_second_argument(self):
        '''
        Event is the second argument
        '''
        def fn(ctx, ev):
            self.assertEqual(ev, 'go')
            return ctx | {'worked': True}
        machine = createMachine({
            'one': state(
                transition('go', 'two', reduce(fn))
            ),
            'two': state()
        })

        service = interpret(machine, lambda : {})
        service.send('go')
        self.assertEqual(service.context['worked'], True, 'changed the context')

if __name__ == '__main__':
    unittest.main()