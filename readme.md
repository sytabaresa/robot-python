# Robot-python

<p align="center">
  <img 
    alt="The Robot logo, with green background."
    src="https://github.com/matthewp/robot-logo/raw/master/logo/robot-green.png"
    width="40%"
  />
</p>

A small functional and immutable Finite State Machine library implemented in Python. Using state machines for your components brings the declarative programming approach to application state.

**This is a python port of the popular JavaScript library [robot](https://thisrobot.life/)** with nearly identical API, still in testing and optimization and with emphasis in MicroPython support.

Tasks:
- [x] Python port
- [x] Same tests of JavaScript ported 
- [x] Test passed
- [x] MicroPython execution (RP2040 tested)
- [ ] Extensive documentation (meanwhile check [oficial robot documentation](https://thisrobot.life/), has the same API)
- [ ] General optimizations
- [ ] [MicroPython optimizations](https://docs.micropython.org/en/latest/reference/speed_python.html#the-native-code-emitter)
- [ ] More python tests
- [ ] Create [native machine code](https://docs.micropython.org/en/latest/develop/natmod.html) (_.mpy_) from MicroPython
- [ ] ...

See [thisrobot.life](https://thisrobot.life/) for documentation, but take in account that is in JavaScript. 
The API is nearly the same of the JS library, with some changes:
- JS objects were replaced with Python dictionaries
- Some helpers were implemented as classes, exact use that original functions
- Debug and logging helpers work identically
- ...

## Examples

Miniman example:
```python
from robot import createMachine, state, transition, interpret

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

```

Nearly all features
```python
from robot import createMachine, guard, immediate, invoke, state, transition, reduce, action
import debug
import logging

def titleIsValid(ctx, ev):
    return len(ctx.title) > 5


async def saveTitle():
    id = await do_db_stuff()
    return id

childMachine = createMachine({
    # ...
})

machine = createMachine({
    'preview': state(
        transition('edit', 'editMode',
                   # Save the current title as oldTitle so we can reset later.
                   reduce(lambda ctx: ctx | {'oldTitle': ctx.title})
                   action(lambda : print('side effect action'))
                   )
    ),
    'editMode': state(
        transition('input', 'editMode',
                   reduce(lambda ctx, ev: ctx | {'title': ev.target.value})
                   ),
        transition('cancel', 'cancel'),
        transition('save', 'validate')
    ),
    'cancel': state(
        immediate('preview',
                  # Reset the title back to oldTitle
                  reduce(lambda ctx: ctx | {'title': ctx.oldTitle})
                  )
    ),
    'validate': state(
        # Check if the title is valid. If so go
        # to the save state, otherwise go back to editMode
        immediate('save', guard(titleIsValid), action(lambda ctx: print(ctx.title, ' is in validation'))),
        immediate('editMode')
    ),
    'save': invoke(saveTitle,
                   transition('done',                    action(lambda : print('side effect action'))
'preview'),
                   transition('error', 'error')
                   ),
    'error': state(
        # Should we provide a retry or...?
    ),
    'child': invoke(childMachine,
                    transition('done', 'preview'),
                    )
})

service = interpret(machine, lambda x: print(x))
service.send('edit')
service.child.send('toggle')
```


## 📚 [Documentation (meanwhile)](https://thisrobot.life/)

* Please star [the repository](https://github.com/sytabaresa/robot-python) on GitHub.
* [File an issue](https://github.com/sytabaresa/robot-python/issues) if you find a bug. Or better yet...
* [Submit a pull request](https://github.com/sytabaresa/robot-python/compare) to contribute.

## Testing

Tests are located in the `tests/` folder, using _unittest_ standard library.
Run with this command or equivalent:
```bash
$ python -m unittest -v tests/*   
```

## License

BSD-2-Clause, same of the original library :D