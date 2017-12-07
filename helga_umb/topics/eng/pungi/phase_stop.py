""" Announce Pungi phases stopping. """
import helga_umb.topics.eng.pungi as pungi


def consume(client, channel, frame):
    message = pungi.describe_phase(frame)
    client.msg(channel, message)
