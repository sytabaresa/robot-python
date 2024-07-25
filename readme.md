# robot-python

<p align="center">
  <img 
    alt="The Robot logo, with green background."
    src="https://github.com/matthewp/robot-logo/raw/master/logo/robot-green.png"
    width="40%"
  />
</p>

A small, blazing fast, functional zero-dependency and immutable Finite State Machine (StateCharts) library implemented in Python. Using state machines for your components brings the declarative programming approach to application state.

**This is a python port of the popular JavaScript library [robot](https://thisrobot.life/)** with nearly identical API, still in optimization and with emphasis in general Python and MicroPython support.
Tasks:
- [x] Python port, tested in MicroPython and python 3.6 as minimal version, older versions may don't work because ordered dicts requirement (see below for a workaround)
- [x] Same tests of JavaScript ported 
- [x] Test passed
- [x] MicroPython support (RP2040 and Unix platform tested)
- [x] Used in a DIY Raspberry Pi Pico W project for a energy meter for a business :wink:
- [ ] Extensive documentation (meanwhile check [oficial robot documentation](https://thisrobot.life/), has the same API)
- [ ] General optimizations
- [ ] [MicroPython optimizations](https://docs.micropython.org/en/latest/reference/speed_python.html#the-native-code-emitter)
- [ ] More python tests
- [ ] Create [native machine code](https://docs.micropython.org/en/latest/develop/natmod.html) (_.mpy_) for MicroPython
- [ ] (maybe) less dynamic, more performant API for constrained devices in MicroPython
- [ ] ...

See [thisrobot.life](https://thisrobot.life/) for documentation, but take in account that is in JavaScript. 

## Why Finite State Machines / StateCharts?
It is a robust paradigm for general purpose programming, but also recommended for high availability, performance and modeling sw/hw applications, is in use in so many applications such as software, embedded applications, hardware, electronics and many things that keep us alive. 
From an 8-bit microcontroller to a large application, the use of FSM/StateCharts can be useful to understand, model (and implement) solutions for complex logic and interactions environments. 


Historically StateCharts were associated with a Graphical Modeling, but StateCharts don't limit to modeling and fancy drawings, libraries like this can be used to implement fsm/statechart as it in code! Even you don’t need to draw something when you can start to program a FSM (see examples).

If only the [Apollo 11 assembler programmers](https://github.com/chrislgarry/Apollo-11) (1969) had known this [paradigm](https://www.inf.ed.ac.uk/teaching/courses/seoc/2005_2006/resources/statecharts.pdf) (1984) before designing their electronic and user interface systems :smiling_face_with_tear:	

### Useful resources

- [Welcome to the world of StateCharts](https://statecharts.dev/)
- Highly recommended conference (UI conference, but the explanations can be applied in general): [State of the Art Web User Interfaces with State Machines - David Khourshid](https://www.youtube.com/watch?v=OVS9cKNK00U) and his [slides](https://slides.com/davidkhourshid/statecharts-fsf)
- Another conference from the same author, I like the analogy of Pacman: [David Khourshid - Infinitely Better UIs with Finite Automata](https://www.youtube.com/watch?v=VU1NKX6Qkxc) and his [slides](https://slides.com/davidkhourshid/finite-state-machines)
- Wikipedia article about [StateCharts](https://en.wikipedia.org/wiki/State_diagram) and [FSMs](https://en.wikipedia.org/wiki/Finite-state_machine#Mathematical_model) (Mathematical Model)
- Original paper: [STATECHARTS: A VISUAL FORMALISM FOR COMPLEX SYSTEMS](https://www.inf.ed.ac.uk/teaching/courses/seoc/2005_2006/resources/statecharts.pdf)
- [StateChart Autocoding for Curiosity Rover](https://blog.nomagic.com/statechart-autocoding-curiosity-rover/)
- Spanish conference: [This is how Apollo 11 was programmed in 1969](https://www.youtube.com/watch?v=tP0XQYC4rjI) about curiosities and complexities of Apollo 11 (and its errors), English subtitles with auto CC  
- [Apollo Guidance Computer (AGC)](https://www.ibiblio.org/apollo/#gsc.tab=0) and [github code](https://github.com/chrislgarry/Apollo-11), will be interesting if all AGC can be programmed in StateCharts :stuck_out_tongue:

# Changes from original library

The API is nearly the same of the JS library, with some changes/gotchas:
- JS objects are replaced with Python equivalents: 
    - state definitions need to be dictionaries or objects with `__getitem__` method
    - events can be strings (equal as in the original library), objects with property _type_, dictionaries or objects with `__getitem__` method and _type_ key
    - context doesn't has restrictions.
- Some helpers were implemented as classes, more robust in type checking and with exact API that JS functions
- JS Promises are implemented with async/await Python feature
- Debug and logging helpers work as expected importing them
- In MicroPython, you need to install [typing stub package](https://micropython-stubs.readthedocs.io/en/stable/_typing_mpy.html) to support type annotations (zero runtime overhead)
- In MicroPython or python version prior 3.6, you must provide initialState (first argument) in _createMachine_, because un-ordered dicts doesn't guarantee deduction of first state as initialState.

## Examples

Minimal example:
```python
from robot import createMachine, state, transition, interpret

machine = createMachine('off', {
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

Nearly all features:
```python
from robot import createMachine, guard, immediate, invoke, state, transition, reduce, action, state as final, interpret, Service
import robot.debug
import robot.logging


def titleIsValid(ctx, ev):
    return len(ctx['title']) > 5


async def saveTitle():
    id = await do_db_stuff()
    return id

childMachine = createMachine('idle', {
    'idle': state(transition('toggle', 'end', action(lambda: print('in child machine!')))),
    'end': final()
})

machine = createMachine('preview', {
    'preview': state(
        transition('edit', 'editMode',
                   # Save the current title as oldTitle so we can reset later.
                   reduce(lambda ctx: ctx | {'oldTitle': ctx['title']}),
                   action(lambda: print('side effect action'))
                   )
    ),
    'editMode': state(
        transition('input', 'editMode',
                   reduce(lambda ctx, ev: ctx | {'title': ev.target.value})
                   ),
        transition('cancel', 'cancel'),
        transition('child', 'child'),
        transition('save', 'validate')
    ),
    'cancel': state(
        immediate('preview',
                  # Reset the title back to oldTitle
                  reduce(lambda ctx: ctx | {'title': ctx['oldTitle']})
                  )
    ),
    'validate': state(
        # Check if the title is valid. If so go
        # to the save state, otherwise go back to editMode
        immediate('save', guard(titleIsValid), action(
            lambda ctx: print(ctx['title'], ' is in validation'))),
        immediate('editMode')
    ),
    'save': invoke(saveTitle,
                   transition('done', 'preview', action(
                       lambda: print('side effect action'))),
                   transition('error', 'error')
                   ),
    'child': invoke(childMachine,
                    transition('done', 'preview'),
                    ),
    'error': state(
        # Should we provide a retry or...?
    )
}, lambda ctx: {'title': 'example title'})


def service_log(service: Service):
    print('send event! current state: ', service.machine.current)


service = interpret(machine, service_log)
print(service.machine.current)
service.send('edit')
service.send('child')
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
