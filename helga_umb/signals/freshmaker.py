""" Announce freshmaker state change messages. """
import json
import smokesignal
from twisted.internet import defer
from helga_umb.signals.util import product_from_branch


@smokesignal.on('umb.eng.freshmaker.build.state.changed')
def build_state_changed(frame):
    data = json.loads(frame.body.decode())
    type_name = data['type_name']  # "IMAGE"
    state_name = data['state_name']  # "DONE"
    branch = data['build_args']['branch']  # ceph-3.0-rhel-7

    mtmpl = 'freshmaker {type_name} {state_name}'
    message = mtmpl.format(type_name=type_name, state_name=state_name)
    product = product_from_branch(branch)
    return defer.succeed(message)
