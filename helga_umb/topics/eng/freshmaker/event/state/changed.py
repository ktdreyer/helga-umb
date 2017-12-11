""" Announce freshmaker state change messages. """
import json


def consume(client, channel, frame):
    data = json.loads(frame.body.decode())
    state_name = data['state_name']
    mtmpl = 'freshmaker {state_name}'

    # Not sure if this key is always present in the body.
    # If it is, append it to the message.
    if 'state_reason' in data:
        mtmpl += ' %s' % data['state_reason']

    message = mtmpl.format(state_name=state_name)
    client.msg(channel, message)



