""" Announce ET advisory creations. """


def consume(client, channel, frame):
    who = frame.headers['who']  # "kdreyer@redhat.com"
    # product = frame.headers['product']  # "RHEL-EXTRAS"
    release = frame.headers['release']  # "Extras-RHEL-7.4"
    type = frame.headers['type']  # "RHBA"
    errata_id = int(frame.headers['errata_id'])  # 12345
    errata_url = 'https://errata.devel.redhat.com/advisory/%d' % errata_id
    mtmpl = '{who} created new {release} {type} advisory {errata_url}'
    message = mtmpl.format(who=who,
                           release=release,
                           type=type,
                           errata_url=errata_url)
    client.msg(channel, message)
