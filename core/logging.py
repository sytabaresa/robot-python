from .machine import d

def onEnter(machine, to, state, prevState, event):
    print('Enter state '+ to)
    print('---Details---')
    print('Machine', machine)
    print('Current state', state)
    print('Previous state', prevState)
    
    if type(event) is str:
        print('Event '+ event)
    else:
        print('Event', event)

d._onEnter = onEnter
