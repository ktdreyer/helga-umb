""" Announce Brew builds as they complete. """
import helga_umb.topics.eng.brew as brew
import helga_umb.topics.eng.brew.build as build


def consume(client, channel, frame):
    nvr = build.nvr(frame)
    owner_name = brew.owner_name(frame)
    build_url = build.build_url(frame)

    mtmpl = "{owner_name}'s {nvr} completed ({build_url})"
    message = mtmpl.format(owner_name=owner_name,
                           nvr=nvr,
                           build_url=build_url)
    client.msg(channel, message)
