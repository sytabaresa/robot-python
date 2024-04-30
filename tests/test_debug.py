from core import createMachine, state, transition, interpret, d
import unittest
unittest.TestLoader.sortTestMethodsUsing = None


class TestDebug(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import core.debug

    @classmethod
    def tearDownClass(cls):
        del d._create
        del d._send

    def test_state_inexistent(self):
        '''
        Errors for transitions to states that don\'t exist
        '''
        with self.assertRaises(Exception) as context:
            createMachine({
                'one': state(
                    transition('go', 'two')
                )
            })

        self.assertTrue("unknown state" in str(context.exception),
                        'Gets an error about unknown states')

    def test_state_existent(self):
        '''
        Does not error for transitions to states when state does exist
        '''
        try:
            with self.assertRaises(Exception, msg='Created a valid machine!') as context:
                createMachine({
                    'one': state(
                        transition('go', 'two')
                    ),
                    'two': state()
                })
        except AssertionError:
            self.assertTrue(True, msg='Created a valid machine!')
        self.assertFalse(hasattr(context, 'exception'),
                         'Should not have errored')

    def test_invalid_initial_context(self):
        '''
        Errors if an invalid initial state is provided
        '''
        with self.assertRaises(Exception, msg='should have failed') as context:
            createMachine('oops', {
                'one': state()
            })

        self.assertTrue("known state" in str(context.exception),
                        'Gets an error about unknown state')

    def test_no_transition(self):
        '''
        Errors when no transitions for event from the current state
        '''
        with self.assertRaises(Exception, msg='should have failed') as context:
            machine = createMachine('one', {
                'one': state()
            })
            service = interpret(machine, lambda: {})
            service.send('go')

        self.assertTrue("transitions for event" in str(
            context.exception), 'it is errored')


if __name__ == '__main__':
    unittest.main()
