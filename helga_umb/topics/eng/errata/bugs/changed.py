""" Announce ET bugs changes. """
import json


def describe_bug(bug):
    """ Return a textual description for a single bug. """
    if bug['type'] == 'RHBZ':
        return 'rhbz#%d' % bug['id']
    return '%s %s' % (bug['type'], bug['id'])


def describe_bugs(bugs):
    """ Return a textual description for a list of bugs. """
    return ', '.join([describe_bug(bug) for bug in bugs])


def consume(client, channel, frame):
    who = frame.headers['who']  # "kdreyer@redhat.com"
    # product = frame.headers['product']  # "RHEL-EXTRAS"
    release = frame.headers['release']  # "Extras-RHEL-7.4"
    # In the header this is currently a string. Convert it to an int:
    errata_id = int(frame.headers['errata_id'])
    data = json.loads(frame.body.decode())
    # "added" looks like:
    # 'added': [{'id': 1450475, 'type': 'RHBZ'}],
    added = data['added']
    dropped = data['dropped']
    change = ''
    if added:
        change = 'added %s' % describe_bugs(added)
    if dropped:
        if added:
            change += ' and '
        change += 'dropped %s' % describe_bugs(dropped)
    errata_url = 'https://errata.devel.redhat.com/advisory/%d' % errata_id
    mtmpl = '{who} {change} in {release} {errata_url}'
    message = mtmpl.format(who=who,
                           change=change,
                           release=release,
                           errata_url=errata_url)
    client.msg(channel, message)
