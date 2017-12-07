""" Announce robosignatory container signing """
import json

TASK_URL = 'http://pub.devel.redhat.com/pub/task/%d/'


def consume(client, channel, frame):
    data = json.loads(frame.body.decode())
    msg = data['msg']

    # human-readable action
    if msg.get('signing_status') == 'success':
        action = 'signed'
    else:
        action = 'signed with status %s' % msg.get('signing_status')

    repo = msg['repo']

    sig_key_id = msg['sig_key_id']

    url = TASK_URL % msg['pub_task_id']

    mtmpl = 'robosignatory {action} container {repo} with {sig_key_id} ({url})'
    message = mtmpl.format(action=action,
                           repo=repo,
                           sig_key_id=sig_key_id,
                           url=url)
    client.msg(channel, message)
