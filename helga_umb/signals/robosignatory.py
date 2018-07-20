import json
import smokesignal
from twisted.internet import defer

TASK_URL = 'http://pub.devel.redhat.com/pub/task/%d/'


@smokesignal.on('umb.eng.robosignatory.container.sign')
def container_sign(frame):
    """ Announce robosignatory container signing """
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
    product = repo  # not great...
    return defer.succeed((message, product))
