""" Announce ET builds changes. """
import json


def consume(client, channel, frame):
    who = frame.headers['who']  # "kdreyer@redhat.com"
    # product = frame.headers['product']  # "RHEL-EXTRAS"
    release = frame.headers['release']  # "Extras-RHEL-7.4"
    # In the header this is currently a string. Convert it to an int:
    errata_id = int(frame.headers['errata_id'])
    data = json.loads(frame.body.decode())
    # "added" looks like:
    # 'added': [{'nvr': 'sssd-docker-7.4-13',
    #           'product_versions': ['EXTRAS-7.4-RHEL-7']}]
    added = data['added']
    removed = data['removed']
    change = ''
    if added:
        nvrs = ', '.join([build['nvr'] for build in added])
        change = 'added %s' % nvrs
    if removed:
        if added:
            change += ' and '
        nvrs = ', '.join([build['nvr'] for build in removed])
        change += 'removed %s' % nvrs
    errata_url = 'https://errata.devel.redhat.com/advisory/%d' % errata_id
    mtmpl = '{who} {change} in {release} {errata_url}'
    message = mtmpl.format(who=who,
                           change=change,
                           release=release,
                           errata_url=errata_url)
    client.msg(channel, message)
