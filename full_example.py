from core import createMachine, guard, immediate, invoke, state, transition, reduce, action, state as final, interpret, Service
import core.debug
import core.logging


def titleIsValid(ctx, ev):
    return len(ctx.title) > 5


async def saveTitle():
    id = await do_db_stuff()
    return id

childMachine = createMachine({
    # ...
    'idle': state(transition('toggle', 'end', action(lambda : print('in child machine!')))),
    'end': final()
})

machine = createMachine({
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
            lambda ctx: print(ctx.title, ' is in validation'))),
        immediate('editMode')
    ),
    'save': invoke(saveTitle,
                   transition('done', 'preview', action(lambda: print('side effect action'))),
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
service.send('edit')
service.send('child')
service.child.send('toggle')
