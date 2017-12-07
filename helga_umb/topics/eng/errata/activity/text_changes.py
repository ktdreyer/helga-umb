""" Announce ET text changes. """
import json


def describe_text_changes(text_changes):
    """ Return a textual description (str) for a list of text fields. """
    return ', '.join([change['name'] for change in text_changes])


def consume(client, channel, frame):
    who = frame.headers['who']  # "kdreyer@redhat.com"
    release = frame.headers['release']  # "Extras-RHEL-7.4"
    errata_id = int(frame.headers['errata_id'])  # 12345
    errata_url = 'https://errata.devel.redhat.com/advisory/%d' % errata_id

    data = json.loads(frame.body.decode())
    # "text_changes" key contains a list of things that changed, like so:
    # 'text_changes': [{'name': 'description',
    #                   'from': "My old description text",
    #                   'to': "My new description text",
    #                  }]
    text_changes = data['text_changes']
    changes = describe_text_changes(text_changes)

    mtmpl = '{who} changed {changes} on {release} {errata_url}'
    message = mtmpl.format(who=who,
                           changes=changes,
                           release=release,
                           errata_url=errata_url)
    client.msg(channel, message)
