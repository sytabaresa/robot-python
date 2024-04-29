import unittest

from core.machine import createMachine, state, transition, reduce, interpret, d

class TestLogging(unittest.TestCase):
        
    def test_onEnter(self):
        '''
        Calls the onEnter function if the state is changed
        '''
        machine = createMachine({
            'one': state(
                transition('go', 'two', 
                           reduce(lambda ctx: ctx | {'x':1})
                           )
            ),
            'two': state()
        }, lambda : {'x': 0, 'y': 0})

        service = interpret(machine, lambda : {})
        def enterFN(m, to, state, prevState, event):
            self.assertEqual(m, machine, 'Machines equal')
            self.assertDictEqual(state, {'x': 1, 'y': 0}, 'Changed state passed')
            self.assertDictEqual(prevState, {'x': 0, 'y': 0}, 'Previus state passed')
            self.assertEqual(to, 'two', 'To state passed')
            self.assertEqual(event, 'go', 'Send event passed')
        
        d._onEnter = enterFN
        service.send('go')
        del d._onEnter
        
if __name__ == '__main__':
    unittest.main()