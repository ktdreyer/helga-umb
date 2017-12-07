""" Announce ET signing operations. """

PROD = 'robosignatory/robosignatory.host.prod.eng.bos.redhat.com@REDHAT.COM'


def consume(client, channel, frame):
    who = frame.headers['who']  # "robosignatory@REDHAT.COM"
    # product = frame.headers['product']  # "RHEL"
    release = frame.headers['release']  # "RHEL-7.3.EUS"
    package = frame.headers['to']  # "kernel-3.10.0-514.36.1.el7"

    # Easier-to-read summary of this long user ID:
    if who == PROD:
        who = 'robosignatory'

    errata_id = int(frame.headers['errata_id'])  # 12345
    errata_url = 'https://errata.devel.redhat.com/advisory/%d' % errata_id

    mtmpl = '{who} signed {package} in {release} {errata_url}'
    message = mtmpl.format(who=who,
                           package=package,
                           release=release,
                           errata_url=errata_url)
    client.msg(channel, message)
