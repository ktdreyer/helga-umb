""" Announce Pungi status change. """
import helga_umb.topics.eng.pungi as pungi


def consume(client, channel, frame):
    message = pungi.describe_status(frame)
    client.msg(channel, message)
