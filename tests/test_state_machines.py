import time
from scullery import statemachines


class Obj:
    def __init__(self) -> None:
        # We turn this var on and off
        # to make sure we can
        self.sm_lamp = 0


def test_state_machines():
    blink = statemachines.StateMachine(start="off")

    blink.add_state("on")
    blink.add_state("off")

    blink.set_timer("on", 1, "off")

    blink.set_timer("off", 1, "on")
    blink.add_rule("off", "begin", "on")
    blink("begin")

    container = Obj()

    container.sm_lamp = 0

    def on():
        container.sm_lamp = 1

    def off():
        container.sm_lamp = 0

    sm = statemachines.StateMachine(start="off")

    sm.add_state("on", enter=on)
    sm.add_state("off", enter=off)

    sm.set_timer("on", 1, "off")

    sm.add_rule("off", "motion", "on")

    if container.sm_lamp:
        raise RuntimeError("state machine imaginary lamp is on too soon")
    sm.event("motion")
    time.sleep(0.3)
    if not container.sm_lamp:
        raise RuntimeError("state machine imaginary lamp is not on")
    time.sleep(2)

    if container.sm_lamp:
        time.sleep(8)
        if container.sm_lamp:
            raise RuntimeError(
                "state machine imaginary lamp didn't turn itself off within 10s"
            )
        else:
            raise RuntimeError(
                "state machine imaginary lamp didn't turn itself off within 2s"
            )

    # Turn it on before deleting so we can make sure the timer won't trigger after it's gone
    sm.event("motion")
    del sm

    sm = statemachines.StateMachine(start="off")

    sm.add_state("on", enter=on)
    sm.add_state("off", enter=off)

    lights_on = [False]

    last_poll = [0.0]

    # Polled function trigger, when f returns true
    # We should go to the next state
    def f():
        last_poll[0] = time.time()
        return lights_on[0]

    sm.add_rule("on", f, "off")
    sm.add_rule("off", "motion", "on")

    if not sm.state == "off":
        raise RuntimeError("Unexpected state")

    sm.event("motion")
    if not sm.state == "on":
        raise RuntimeError("Unexpected state")

    # Make sure polling doesn't trigger it if false
    time.sleep(0.3)
    if not sm.state == "on":
        raise RuntimeError("Unexpected state")

    lights_on[0] = True
    time.sleep(0.3)

    if not sm.state == "off":
        raise RuntimeError("Unexpected state")

    t = last_poll[0]
    if not t:
        raise RuntimeError("Test probably is buggy")

    time.sleep(0.3)
    if not last_poll[0] == t:
        raise RuntimeError("State machine continued polling after exiting event")

    lights_on[0] = False
    time.sleep(0.25)
    t = last_poll[0]
    del sm
    time.sleep(1)

    if not last_poll[0] == t:
        raise RuntimeError("State machine continued polling after deleting")

    transitions = []

    sm = statemachines.StateMachine(start="off")

    sm.add_state("on", enter=on)
    sm.add_state("off", enter=off)

    sm.add_rule("off", "switch", "on")

    def subscriber(s):
        transitions.append(s)

    sm.subscribe(subscriber)
    sm.event("switch")
    if not transitions == ["on"]:
        print(transitions)
        raise RuntimeError("State machines not working as they should")
