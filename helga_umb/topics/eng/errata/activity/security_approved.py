""" Announce security approval changes. """


def consume(client, channel, frame):
    who = frame.headers['who']  # "kdreyer@redhat.com"
    release = frame.headers['release']  # "Extras-RHEL-7.4"
    errata_id = int(frame.headers['errata_id'])  # 12345
    errata_url = 'https://errata.devel.redhat.com/advisory/%d' % errata_id

    action = 'changed security approval'  # defensively init default action str
    if frame.headers['to'] == 'true':
        action = 'approved security'
    if frame.headers['to'] == 'false':
        # ET comments this action as "Product Security approval requested."
        action = 'requested security approval'

    mtmpl = '{who} {action} on {release} {errata_url}'
    message = mtmpl.format(who=who,
                           action=action,
                           release=release,
                           errata_url=errata_url)
    client.msg(channel, message)
