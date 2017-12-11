""" Brew build message helpers. """
import json


URL = 'https://brewweb.engineering.redhat.com/brew/buildinfo?buildID=%d'


def nvr(frame):
    """ Should this go in the parent "brew" library? """
    name = frame.headers['name']  # "release-e22-test", pkg name
    version = frame.headers['version']  #  "1.0.657"
    release = frame.headers['release']  #  "1.el7"
    return '%s-%s-%s' % (name, version, release)


def build_url(frame):
    data = json.loads(frame.body.decode())
    build_id = data['info']['id']
    return URL % build_id
