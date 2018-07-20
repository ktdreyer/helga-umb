import json
import smokesignal
from twisted.internet import defer


@smokesignal.on('umb.eng.greenwave.decision.update')
def decision_update(frame):
    # IMAGE rh-python35-container is successfully rebuilt from original build rh-python35-container-3.5-30 to new build rh-python35-container-3.5-30.1533128008
    data = json.loads(frame.body)

    mtmpl = "greenwave ........"
    message = mtmpl.format(.....)
    product = ...
    return defer.succeed((message, product))
