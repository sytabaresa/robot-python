import unittest

from core import createMachine, state, transition, immediate, interpret


class TestImmediate(unittest.TestCase):

    def test_immediate(self):
        '''
        Will immediately transition
        '''
        machine = createMachine({
            'one': state(
                transition('ping', 'two')
            ),
            'two': state(
                immediate('three')
            ),
            'three': state()
        })

        service = interpret(machine, lambda: {})
        service.send('ping')
        self.assertEqual(service.machine.current, 'three')


if __name__ == '__main__':
    unittest.main()
