from typing import Dict

from .machine import d, InvokeFn, State

def unknownState(from_, state):
    raise Exception('Cannot transition from '+from_+' to unknown state: '+state)

def create(current: str, states: Dict[str,State]):
    # print(current, states)
    if current not in states:
        raise Exception('Initial state ['+current+'] is not a known state')
    for p in states:
        state = states[p]
        for candidates in state.transitions.values():
            for c in candidates:
                if c.to not in states:
                    unknownState(p,c.to)
        if isinstance(state, InvokeFn):
            hasErrorFrom = False
            for candidates in state.transitions.values():
                for c in candidates:
                    if c.from_ == 'error':
                        hasErrorFrom = True
            if not hasErrorFrom:
                print('When using invoke [current state: '+p+'] with Promise-returning function, you need to add \'error\' state. Otherwise, robot will hide errors in Promise-returning function')
                
d._create = create

def send(eventName, currentStateName):
    raise Exception('No transitions for event '+eventName+' from the current state ['+currentStateName+']')

d._send = send