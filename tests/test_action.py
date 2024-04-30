import unittest

from core import createMachine, state, transition, action, interpret


class TestAction(unittest.TestCase):

    def test_side_effects(self):
        '''
        Can be used to do side-effects
        '''
        count = 0
        orig = {}

        def a():
            nonlocal count
            count += 1
        machine = createMachine({
            'one': state(
                transition('ping', 'two', action(a))
            ),
            'two': state()
        }, lambda: orig)

        service = interpret(machine, lambda: {})
        service.send('ping')

        self.assertEqual(service.context, orig, 'context stays the same')
        self.assertEqual(count, 1, 'side-effect performed')


if __name__ == '__main__':
    unittest.main()
