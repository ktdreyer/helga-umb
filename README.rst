A Unified Message Bus plugin for helga chat bot
===============================================

About
-----

Helga is a Python chat bot. Full documentation can be found at
http://helga.readthedocs.org.

This plugin allows Helga to respond to messages on Red Hat's internal Unified
Message Bus and report them in IRC. For example::

  03:14 < helgabot> kdreyer tagged libntirpc-1.4.1-2.el7 in ceph-2-rhel-7-candidate

Settings
--------

You will need an x509 keypair and read access to the ``eng.>`` and ``qe.ci.>``
VirtualTopics.

In Helga's settings, you must specify your consumer queues and keypair::

  UMB_CHANNEL = '#chatops'
  UMB_DESTINATIONS = [
      '/queue/Consumer.kdreyer.eng.VirtualTopic.eng.>',
      '/queue/Consumer.kdreyer.qeci.VirtualTopic.qe.ci.>'
  ]
  UMB_CERT = 'kdreyer.pem'
  UMB_KEY = 'kdreyer.key'

* ``UMB_CHANNEL`` should be the channel to which to report UMB traffic.

* ``UMB_DESTINATIONS`` should be the VirtualTopic queues to which your client
  has access.

* ``UMB_CERT`` should be the path to the public PEM-formatted x509 certificate.

* ``UMB_KEY`` should be the path to the PEM-formatted RSA private key.

Note about stompest
-------------------

This plugin relies on the excellent `stompest.async
<https://nikipore.github.io/stompest/async.html>`_ library, but the UMB needs a
few features that are not merged in stompest upstream:

* SSL client authentication (works for the non-async client, does not yet work
  for the Twisted-based client)
* Messages with destinations that do not match the subscription destinations
  (this is a result of using ActiveMQ's VirtualTopics)

I've submitted patches for these features to stompest upstream but they need
work before the features are accepted.


Future Plugin Feature Ideas
---------------------------
- "helgabot, debug last message"
  ... would print the headers (json-encoded) and raw body directly to IRC
  ... and link to a datagrepper instance for that message ID
- Switch to using ``fedmsg.meta.msg2subject(msg, **config)`` and
  ``fedmsg.meta.msg2link(msg, **config)``
- Filter for a single product. Use a regex?
- Stop hard-coding ``UMB_CHANNEL`` and store this setting in MongoDB.
