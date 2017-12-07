""" Announce ET batch push completions. """


def consume(client, channel, frame):
    who = frame.headers['who']  # "kdreyer@redhat.com"
    batch_name = frame.headers['batch_name']  # "RHEL-7.4.3-Extras"
    mtmpl = '{who} completed batch push for {batch_name}'
    message = mtmpl.format(who=who, batch_name=batch_name)
    client.msg(channel, message)
