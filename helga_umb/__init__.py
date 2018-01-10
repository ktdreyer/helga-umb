from pprint import pprint
import json
import logging
import importlib

import smokesignal

from helga.plugins import command
from helga import log, settings

from twisted.internet import defer

from stompest.config import StompConfig
from stompest.protocol import StompSpec

from stompest.async import Stomp
from stompest.async.listener import SubscriptionListener
from stompest.async.listener import ErrorListener
from stompest.error import StompProtocolError


# prod with failover
STOMP_URL = 'failover:(ssl://messaging-devops-broker01.web.prod.ext.phx2.redhat.com:61612,ssl://messaging-devops-broker02.web.prod.ext.phx2.redhat.com:61612)?startupMaxReconnectAttempts=10'  # NOQA: E501

# stage with failover
# STOMP_URL = 'failover:(ssl://messaging-devops-broker01.web.stage.ext.phx2.redhat.com:61612,ssl://messaging-devops-broker02.web.stage.ext.phx2.redhat.com:61612)?startupMaxReconnectAttempts=10'  # NOQA: E501

# dev
# STOMP_URL = 'ssl://messaging-devops-broker01.dev1.ext.devlab.redhat.com:61612'


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
            '/topic/VirtualTopic.eng.brew.build.untag',
            '/topic/VirtualTopic.eng.brew.import',
            '/topic/VirtualTopic.eng.brew.package',
            '/topic/VirtualTopic.eng.brew.repo',
            '/topic/VirtualTopic.eng.brew.sign',
            '/topic/VirtualTopic.eng.cips',  # TPS replacement
            '/topic/VirtualTopic.eng.distill',
            '/topic/VirtualTopic.eng.errata-bridge',
            '/topic/VirtualTopic.eng.errata.activity.batch',
            '/topic/VirtualTopic.eng.errata.builds.added',
            '/topic/VirtualTopic.eng.errata.builds.changed',
            '/topic/VirtualTopic.eng.errata.builds.removed',
            '/topic/VirtualTopic.eng.metaxor',
            '/topic/VirtualTopic.eng.platformci',
            '/topic/VirtualTopic.eng.pub',
            '/topic/VirtualTopic.eng.pungi.createiso',
            '/topic/VirtualTopic.eng.pungi.phase',
            '/topic/VirtualTopic.eng.rhchi',  # Container Health Index
            '/topic/VirtualTopic.eng.rpmdeplint',  # TPS replacement
            '/topic/VirtualTopic.eng.rpmdiff',
            '/topic/VirtualTopic.qe.ci.brew',  # Mirrors everything from brew
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

        # pprint_frame(frame)  # Noisy

        # Route this destination to a lib under helga_umb.topics.
        topiclib = 'helga_umb.topics.%s' % destination[20:].replace('-', '_')
        try:
            # logger.debug('importing %s' % topiclib)
            lib = importlib.import_module(topiclib)
        except ImportError as e:
            # Show the raw destination value.
            self.client.msg(self.channel, destination)
            # logger.debug(e)  # debugging
            pprint_frame(frame)  # debugging
            if e.message.startswith('No module named'):
                # We have no custom code to consume this message.
                # This is ok, just move on.
                # (Note: This will skip any import issues in topiclib itself
                # though.)
                return
            else:
                # Something else went wrong.
                raise
        return lib.consume(self.client, self.channel, frame)


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
