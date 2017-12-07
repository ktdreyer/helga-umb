""" Announce ET assignment changes. """


def consume(client, channel, frame):
    who = frame.headers['who']  # "kdreyer@redhat.com"
    # product = frame.headers['product']  # "RHEL-EXTRAS"
    release = frame.headers['release']  # "Extras-RHEL-7.4"
    errata_id = int(frame.headers['errata_id'])  # 12345
    errata_url = 'https://errata.devel.redhat.com/advisory/%d' % errata_id
    # from_person = frame.headers['from']  # "old-example@redhat.com"
    person = frame.headers['to']  # "example@redhat.com"
    mtmpl = '{who} assigned QE of {release} {errata_url} to {person}'
    message = mtmpl.format(who=who,
                           release=release,
                           errata_url=errata_url,
                           person=person)
    client.msg(channel, message)
