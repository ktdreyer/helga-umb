""" Announce ccat messages. """
import json


def consume(client, channel, frame):
    headers = json.dumps(frame.headers)
    body = frame.body.decode()
    message = 'ccat: %s %s' % (headers, body)
    client.msg(channel, message)
