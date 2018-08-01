from pprint import pprint
import re
import json
import logging

import smokesignal

from helga.plugins import command
from helga import log, settings

from stompest.config import StompConfig
from stompest.protocol import StompSpec

from stompest.async import Stomp
from stompest.async.listener import SubscriptionListener

from helga_umb import datagrepper

# prod with failover
STOMP_URL = 'failover:(ssl://messaging-devops-broker01.web.prod.ext.phx2.redhat.com:61612,ssl://messaging-devops-broker02.web.prod.ext.phx2.redhat.com:61612)?startupMaxReconnectAttempts=10'  # NOQA: E501

# stage with failover
# STOMP_URL = 'failover:(ssl://messaging-devops-broker01.web.stage.ext.phx2.redhat.com:61612,ssl://messaging-devops-broker02.web.stage.ext.phx2.redhat.com:61612)?startupMaxReconnectAttempts=10'  # NOQA: E501

# dev
# STOMP_URL = 'ssl://messaging-devops-broker01.dev1.ext.devlab.redhat.com:61612'


# Load our built-in signals:
import helga_umb.signals


logger = log.getLogger(__name__)
for slog in ['stompest.async.protocol', 'stompest.async.listener']:
    sl = log.getLogger(slog)
    sl.setLevel(logging.INFO)


class HelgaStompConsumer():
    """ Consume messages and report them to an IRC client's channel. """
    def __init__(self, client, channel):
        self.client = client
        self.channel = channel

    def is_interesting(self, destination):
        """
        Determine if we should log or mention this destination.

        Return True if we should continue processing this destination.
        Return False if we should ignore this entirely.
        """
        IGNORE_PREFIX = [
            '/topic/VirtualTopic.eng.brew.build.deleted',
            '/topic/VirtualTopic.eng.brew.build.tag',
            '/topic/VirtualTopic.eng.brew.build.untag',
            '/topic/VirtualTopic.eng.brew.import',
            '/topic/VirtualTopic.eng.brew.package',
            '/topic/VirtualTopic.eng.brew.repo',
            '/topic/VirtualTopic.eng.brew.sign',
            '/topic/VirtualTopic.eng.cips',  # TPS replacement
            '/topic/VirtualTopic.eng.ci',  # QE groups' Jenkins?
            '/topic/VirtualTopic.eng.distill',
            '/topic/VirtualTopic.eng.errata-bridge',
            '/topic/VirtualTopic.eng.errata.activity.batch',
            '/topic/VirtualTopic.eng.errata.builds.added',
            '/topic/VirtualTopic.eng.errata.builds.changed',
            '/topic/VirtualTopic.eng.errata.builds.removed',
            '/topic/VirtualTopic.eng.imagemanager',  # just heartbeats
            '/topic/VirtualTopic.eng.metaxor',
            '/topic/VirtualTopic.eng.platformci',
            '/topic/VirtualTopic.eng.pub',
            '/topic/VirtualTopic.eng.pungi.createiso',
            '/topic/VirtualTopic.eng.pungi.phase',
            '/topic/VirtualTopic.eng.rhchi',  # Container Health Index
            '/topic/VirtualTopic.eng.rpmdeplint',  # TPS replacement
            '/topic/VirtualTopic.eng.rpmdiff',
            '/topic/VirtualTopic.qe.ci.brew',  # Mirrors everything from brew
            '/topic/VirtualTopic.qe.ci.brew-build',  # some kinda "tests"
            '/topic/VirtualTopic.qe.ci.centos.messages',  # just heartbeats
            '/topic/VirtualTopic.qe.ci.create-task-repo',
            '/topic/VirtualTopic.qe.ci.distgit',
            '/topic/VirtualTopic.qe.ci.errata',
            '/topic/VirtualTopic.qe.ci.fedmsg',
            '/topic/VirtualTopic.qe.ci.pub',
            '/topic/VirtualTopic.qe.ci.rcm',
            '/topic/VirtualTopic.qe.ci.rhchi',
            '/topic/VirtualTopic.qe.ci.rpmdiff',
            '/topic/VirtualTopic.qe.ci.upload-ami',
        ]
        for prefix in IGNORE_PREFIX:
            if destination.startswith(prefix):
                return False
        return True

    def consume(self, client, frame):
        """ NOTE: you can return a Deferred here """
        destination = frame.headers['destination']
        # logger.debug('saw "%s"' % destination)  # noisy

        if not destination.startswith('/topic/VirtualTopic.'):
            logger.error('unhandled destination "%s"' % destination)
            return

        if not self.is_interesting(destination):
            # logger.debug('ignoring %s' % destination)  # noisy
            return

        signal = 'umb.' + destination[20:]

        # note: the smokesignal helga requires is too old for some things we do
        # here. Fix in https://github.com/shaunduncan/helga/pull/166
        # 1) ._receivers in 0.5 vs .receivers in 0.7.0
        # 2) emit() returns nothing in 0.5, and it returns
        #    Twisted's DeferredList in master (0.8.0, tbd)

        def errback(e):
            """ Send errors through our main send_err method. """
            send_err(e, self.client, self.channel)

        if signal not in smokesignal.receivers:
            # If we don't have anything to process this message, just print its
            # destination to the channel. In the future we may we want to
            # silence this, because it's noisy.
            #self.client.msg(self.channel, signal)
            # Show datagrepper URLs.
            msg = signal + ' ' + datagrepper.get_url(frame.headers)
            self.client.msg(self.channel, msg)
        d = smokesignal.emit(signal, frame, errback=errback)
        # d is a twisted.internet.defer.DeferredList
        d.addCallback(route_product_message, self.client)
        d.addErrback(send_err, self.client, self.channel)
        return d


def route_product_message(results, client):
    """ Callback from our smokesignal DeferredList """
    for msg_and_product in results:
        if not msg_and_product:
            # our callback determined the message to be uninteresting.
            continue
        try:
            (msg, product) = msg_and_product
        except (TypeError, ValueError) as e:
            # We didn't call back with the right return type.
            # There's nothing we can do, so just ignore this message.
            logger.warning(msg_and_product)
            logger.warning(e)
            continue
        channel_matchers = getattr(settings, 'PRODUCT_CHANNELS', {})
        for regex, channel in channel_matchers.items():
            if re.search(regex, product, re.I):
                client.msg(channel, msg)


def pprint_frame(frame):
    """ Debugging: pretty-print the whole frame to STDOUT. """
    pprint(frame.headers)
    try:
        body = frame.body.decode()
    except UnicodeDecodeError as e:
        # This could be a bug in the sending application, for example
        # METAXOR-1147 where the body is binary AMQP data.
        if frame.body:
            logger.error('Could not decode body text: %s' % e)
            pprint(frame.body)
        return
    try:
        data = json.loads(body)
    except ValueError as e:
        # Some applications do not send bodies:
        # - For example, VirtualTopic.qe.ci.jenkins messages do not always
        #   (ever?) have bodies.
        # - Other times this could be a bug in the sending application,
        #   for example, https://bugzilla.redhat.com/1458120 where the
        #   bodies are missing entirely.
        # Only log if we have a non-JSON body string to cut down on the
        # possible noise.
        if frame.body:
            logger.error('Could not decode JSON in body: %s' % e)
            logger.error('Plain decoded non-JSON body: %s' % body)
        return
    pprint(data)


def stomp_connection(client, channel):
    """ Set up stomp connection here """
    config = StompConfig(
        uri=STOMP_URL,
        version=StompSpec.VERSION_1_1,  # msgs can be unicode
    )  # Do we need sslContext here?
    stomp_client = Stomp(config)
    d = stomp_client.connect(certKey=settings.UMB_CERT,
                             privateKey=settings.UMB_KEY)
    d.addCallback(connect_callback, stomp_client, client, channel)
    d.addErrback(send_err, client, channel)


def connect_callback(_, stomp_client, client, channel):
    """ Fires when we successfully connect to stomp. """
    client.msg(channel, 'successfully connected to stomp server')
    consumer = HelgaStompConsumer(client, channel)
    listener = SubscriptionListener(consumer.consume,
                                    onMessageFailed=listener_err)
    for id_, destination in enumerate(settings.UMB_DESTINATIONS):
        headers = {
            StompSpec.ACK_HEADER: StompSpec.ACK_AUTO,
            # XXX I'm adding 100 here because I might need to run multiple
            # instances of the bot using the same consumer destinations, and I
            # suspected that ActiveMQ might not send messages to both bots at
            # the same time unless I used unique numbers here.
            # I never found out if that's truly necessary, or if multiple
            # clients on the exact same consumer queue will really receive
            # everything.
            # If it is necessary, we'll probably want to make this "100"
            # configurable.
            StompSpec.ID_HEADER: id_ + 100
        }
        d = stomp_client.subscribe(destination, headers, listener=listener)
        d.addCallback(subscribed_callback, client, channel, destination)
        d.addErrback(send_err, client, channel)
        stomp_client.disconnected.addErrback(disconnected_errback,
                                             client, channel)
        stomp_client.catch_unknown_messages(listener)


@smokesignal.on('signon')
def init_connection(client):
    # Simply firehose the first channel in our config
    channel = settings.CHANNELS[0]
    # If channel is more than one item tuple, second value is password
    if isinstance(channel, (tuple, list)):
        channel = channel[0]
    stomp_connection(client, channel)


@command('umb', help='The stomp command (unused for now)')
def helga_umb(client, channel, nick, message, cmd, args):
    # Nothing to do here yet
    pass


def subscribed_callback(token, client, channel, destination):
    msg = 'subscribed to %s with token %s' % (destination, token)
    client.msg(channel, msg)


def send_err(e, client, channel):
    # import pdb; pdb.set_trace()
    # It would be cool to save the entire frame to disk here.
    client.msg(channel, 'stompest error: %s' % e.value)
    # Provide the file and line number.
    tb = e.getBriefTraceback().split()
    client.msg(channel, str(tb[-1]))


def listener_err(connection, e, frame, _):
    """
    SubscriptionListener onMessageFailed handler

    :param connection: ``stompest.async.client.Stomp`` instance
    :param e:          Exception raised from ``SubscriptionListener`` consumer
    :param frame:      message on which this Exception was raised.
    """
    pprint_frame(frame)
    import sys
    import traceback
    import os
    ex_type, ex, tb = sys.exc_info()
    (filename, lineno, method, text) = traceback.extract_tb(tb)[-1]
    del tb
    msg = '{filename}:{lineno}: {text} {ex_type} {ex}'.format(
        filename=os.path.relpath(filename),
        lineno=lineno,
        text=text,
        ex_type=ex_type,
        ex=ex)
    logger.error(msg)


def disconnected_errback(failure, client, channel):
    """
    client.disconnected error handler

    This can happen, for example, if the ActiveMQ server refuses to grant the
    client read access for a subscription. Maybe the client is unauthorized.

    :param failure: ``twisted.python.failure.Failure``, probably a
                    ``stompest.error.StompProtocolError``.
    :param client:  Helga client (eg irc)
    :param channel: Helga channel (eg "#chatops")
    """
    e = failure.value  # stompest.error.StompProtocolError
    try:
        # We might have an ERROR frame with more details in the "message"
        # header.
        frame = e.frame  # stompest.protocol.StompFrame
        message = 'disconnected from stomp: %s' % frame.headers['message']
    except (AttributeError, KeyError):
        message = 'disconnected from stomp: %s' % e
    client.msg(channel, message)
