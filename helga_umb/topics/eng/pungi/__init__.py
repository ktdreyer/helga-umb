import json


def phase_action(frame):
    """ Return a human-readable verb, "started" or "stopped". """
    mtype = frame.headers['mtype']
    if mtype == 'phase-start':
        return 'started'
    if mtype == 'phase-stop':
        return 'stopped'
    return mtype


def phase_name(frame):
    data = json.loads(frame.body.decode())
    return data['phase_name']


def compose_status(frame):
    data = json.loads(frame.body.decode())
    return data.get('status')


def compose_location(frame):
    data = json.loads(frame.body.decode())
    return data['location']


def describe_phase(frame):
    """
    Human-readable description for this Pungi phase message.

    For example:
    Pungi started image_checksum phase for http://example.com/COMPOSE_ID
    """
    action = phase_action(frame)
    phase = phase_name(frame)
    location = compose_location(frame)

    mtmpl = "Pungi {action} {phase} phase for {location}"
    message = mtmpl.format(action=action,
                           phase=phase,
                           location=location)
    return message


def describe_status(frame):
    """
    Human-readable description for this Pungi status message.

    For example:
    Pungi finished at http://example.com/COMPOSE_ID
    """
    action = compose_status(frame).lower()
    location = compose_location(frame)

    mtmpl = "Pungi {action} at {location}"
    message = mtmpl.format(action=action, location=location)
    return message
