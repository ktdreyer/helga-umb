""" Announce ET build flag changes. """
import json


def consume(client, channel, frame):
    who = frame.headers['who']  # "example@redhat.com"
    brew_build = frame.headers['brew_build']  # "udisks2-2.7.3-3.el7"
    release = frame.headers['release']  # "Extras-RHEL-7.4"
    errata_id = int(frame.headers['errata_id'])  # 12345
    errata_url = 'https://errata.devel.redhat.com/advisory/%d' % errata_id
    data = json.loads(frame.body.decode())
    from_flags = ''
    if data['from']:
        from_flags = 'from %s' % ', '.join(data['from'])
    to_flags = 'to %s' % ', '.join(data['to'])
    mtmpl = '{who} changed flags {from_flags} {to_flags} for {brew_build} for {release} {errata_url}'  # NOQA: E501
    message = mtmpl.format(who=who,
                           brew_build=brew_build,
                           from_flags=from_flags,
                           to_flags=to_flags,
                           release=release,
                           errata_url=errata_url)
    client.msg(channel, message)
