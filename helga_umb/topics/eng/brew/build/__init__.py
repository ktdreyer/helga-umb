""" Brew build message parser. """
import json
from twisted.internet import defer
import helga_umb.topics.eng.brew as brew


URL = 'https://brewweb.engineering.redhat.com/brew/buildinfo?buildID=%d'


def get_nvr(frame):
    """ Should this go in the parent "brew" library? """
    name = frame.headers['name']  # "release-e22-test", pkg name
    version = frame.headers['version']  #  "1.0.657"
    release = frame.headers['release']  #  "1.el7"
    return '%s-%s-%s' % (name, version, release)


def get_build_url(frame):
    data = json.loads(frame.body.decode())
    build_id = data['info']['id']
    return URL % build_id


def get_action(frame):
    dest = frame.headers['destination']
    (_, action) = dest.rsplit('.', 1)
    return action


@defer.inlineCallbacks
def consume(client, channel, frame):
    owner_name = yield brew.owner_name(frame)
    nvr = get_nvr(frame)
    build_url = get_build_url(frame)
    action = get_action(frame)

    mtmpl = "{owner_name}'s {nvr} {action} ({build_url})"
    message = mtmpl.format(owner_name=owner_name,
                           nvr=nvr,
                           action=action,
                           build_url=build_url)
    client.msg(channel, message)
