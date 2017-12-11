""" Brew message helpers. """
import json


def owner_name(frame):
    """ Return the owner username """
    # From what I can tell, this is not the pkg "owner" in Brew, but the actual
    # username of whoever triggered the build.
    data = json.loads(frame.body.decode())
    try:
        # Not every message has an owner_name, see BREW-1640
        owner_name = data['info']['owner_name']
    except KeyError:
        # This should be the owner_id number
        owner_id = data['info']['owner']
        # TODO: xml-rpc getUser call to brewhub
        return 'brew user %d' % owner_id
    # Shorten any system account FQDN here for readability.
    if '.' in owner_name:
        (owner_name, _) = owner_name.split('.', 1)
    return owner_name
