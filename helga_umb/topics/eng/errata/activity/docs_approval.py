""" Announce ET docs approval changes. """


def consume(client, channel, frame):
    who = frame.headers['who']  # "kdreyer@redhat.com"
    release = frame.headers['release']  # "Extras-RHEL-7.4"
    errata_id = int(frame.headers['errata_id'])  # 12345
    errata_url = 'https://errata.devel.redhat.com/advisory/%d' % errata_id

    action = frame.headers['to']
    if action == "docs_approval_requested":
        action = 'requested docs approval'

    mtmpl = '{who} {action} on {release} {errata_url}'
    message = mtmpl.format(who=who,
                           action=action,
                           release=release,
                           errata_url=errata_url)
    client.msg(channel, message)
