""" Announce Brew tagging builds. """
import helga_umb.topics.eng.brew.build as build


def consume(client, channel, frame):
    # Interesting variables:
    tag = frame.headers['tag']  # "release-e22-test-1.0-rhel-7", brew tag
    if tag == 'trashcan':
        # We don't care
        return
    user = frame.headers['user']  # "errata/beehive"
    # Shorten any system account FQDN here for readability.
    if '.' in user:
        (user, _) = user.split('.', 1)
    nvr = build.get_nvr(frame)
    mtmpl = '{user} tagged {nvr} in {tag}'
    message = mtmpl.format(user=user, nvr=nvr, tag=tag)
    client.msg(channel, message)
