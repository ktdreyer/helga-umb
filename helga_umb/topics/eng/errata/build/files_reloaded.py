""" Announce ET build list reloads. """


def consume(client, channel, frame):
    # ("who" is always qa-errata-list@redhat.com. An ET bug?)
    who = frame.headers['who']  # "example@redhat.com"
    build_nvr = frame.headers['build_nvr']  # "udisks2-2.7.3-3.el7"
    release = frame.headers['release']  # "Extras-RHEL-7.4"
    errata_id = int(frame.headers['errata_id'])  # 12345
    errata_url = 'https://errata.devel.redhat.com/advisory/%d' % errata_id
    mtmpl = '{who} reloaded build list for {build_nvr} for {release} {errata_url}'  # NOQA: E501
    message = mtmpl.format(who=who,
                           build_nvr=build_nvr,
                           release=release,
                           errata_url=errata_url)
    client.msg(channel, message)
