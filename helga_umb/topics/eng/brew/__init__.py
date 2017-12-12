""" Brew message helpers. """
import errno
import os
import json
from txkoji import Connection
from munch import Munch
from twisted.internet import defer

koji = Connection('brew')

CACHEDIR = os.path.expanduser('~/.cache/helga-umb')

def cached_name(type_, id_):
    cachefile = os.path.join(CACHEDIR, 'brew-%s-%d' % (type_, id_))
    try:
        with open(cachefile, 'r') as f:
            return f.read()
    except (OSError, IOError) as e:
        if e.errno != errno.ENOENT:
            raise


def cached_owner_name(id_):
    return cached_name('owner', id_)


def cached_tag_name(id_):
    return cached_name('tag', id_)


def cache_name(type_, id_, name):
    try:
        os.makedirs(CACHEDIR)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    cachefile = os.path.join(CACHEDIR, 'brew-%s-%d' % (type_, id_))
    with open(cachefile, 'w') as f:
        return f.write(name)


def cache_owner_name(id_, name):
    return cache_name('owner', id_, name)


def cache_tag_name(id_, name):
    return cache_name('tag', id_, name)


def owner_name(frame):
    """ Return a Deferred that calls back with the Brew owner name """
    # From what I can tell, this is not the pkg "owner" in Brew, but the actual
    # username of whoever triggered the build.
    data = json.loads(frame.body.decode())
    # Some messages have the owner ID number as "owner", some have it as
    # "owner_id".
    owner_id = data['info'].get('owner')
    if not isinstance(owner_id, int):
        owner_id = data['info']['owner_id']
    try:
        # Not every message has an owner_name, see BREW-1640
        owner_name = data['info']['owner_name']
    except KeyError:
        # Try the local disk cache first before querying brewhub
        owner_name = cached_owner_name(owner_id)
        if not owner_name:
            # xml-rpc getUser call to brewhub
            d = koji.get_user(owner_id)
            d.addCallback(owner_callback)
            return d
    owner = Munch(id=owner_id, name=owner_name)
    d = defer.succeed(owner)
    d.addCallback(owner_callback)
    return d


def owner_callback(owner):
    """ Return a (maybe shortened) Brew user name for this user object """
    cache_owner_name(owner.id, owner.name)
    # Shorten any system account FQDN here for readability.
    name = owner.name
    if '.' in name:
        (name, _) = name.split('.', 1)
    return name


def package_from_src(src):
    """
    Return a human-readable package from a build "src" parameter.

    eg. cli-build/123.456.abc/kernel-3.10.0-1.el7.src.rpm
        Returns the full NVR "kernel-3.10.0-1.el7"
    eg. git://example.com/rpms/kernel#sha
        Returns the name "kernel"
    """
    basename = os.path.basename(src)
    if basename.endswith('.src.rpm'):
        return basename[:-8]
    elif '#' in basename:
        (name, _) = basename.split('#')
        # branch name after "?", I guess?
        # git://example.com/users/foo/pkg-devel.git?bar/baz#fd6269221
        if '?' in name:
            (name, _) = name.split('?')
        if name.endswith('.git'):
            return basename[:-4]
        return name


def tag_name(tag_id):
    """ Return a Deferred that calls back with the Brew tag name """
    cache = cached_tag_name(tag_id)
    if cache:
        tag = Munch(id=tag_id, name=cache)
        d = defer.succeed(tag)
    else:
        d = koji.get_tag(tag_id)
    d.addCallback(tag_callback)
    return d


def tag_callback(tag):
    """ Cache and return a Brew tag name for this tag object """
    cache_tag_name(tag.id, tag.name)
    return tag.name
