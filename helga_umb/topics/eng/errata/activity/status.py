""" Announce ET status changes. """


def consume(client, channel, frame):
    who = frame.headers['who']  # "kdreyer@redhat.com"
    # product = frame.headers['product']  # "RHEL-EXTRAS"
    release = frame.headers['release']  # "Extras-RHEL-7.4"
    errata_id = int(frame.headers['errata_id'])  # 12345
    errata_url = 'https://errata.devel.redhat.com/advisory/%d' % errata_id
    # from_status = frame.headers['from']  # "NEW_FILES"
    to_status = frame.headers['to']  # "QE"
    mtmpl = '{who} changed {release} {errata_url} to {to_status} status'
    message = mtmpl.format(who=who,
                           release=release,
                           errata_url=errata_url,
                           to_status=to_status)
    client.msg(channel, message)
