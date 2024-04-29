import unittest

from core.machine import createMachine, state, transition, guard, interpret

class TestGuards(unittest.TestCase):

    def test_changing_states(self):
        '''
        Can prevent changing states
        '''
        canProceed = False
        machine = createMachine({
            'one': state(
                transition('ping', 'two', guard(lambda : canProceed))
            ),
            'two': state()
        })

        service = interpret(machine, lambda : {})
        service.send('ping')
        self.assertEqual(service.machine.current, 'one')
        canProceed = True
        service.send('ping')
        self.assertEqual(service.machine.current, 'two')
        
if __name__ == '__main__':
    unittest.main()