import json
import smokesignal
from twisted.internet import defer
import re
from helga import log

"""
Announce Jenkins messages.

See https://wiki.jenkins.io/display/JENKINS/JMS+Messaging+Plugin
"""

logger = log.getLogger(__name__)


@smokesignal.on('umb.qe.ci.jenkins')
def jenkins(frame):
    # These are always present:
    ci_name = frame.headers['CI_NAME']  # "jobname"
    ci_type = frame.headers['CI_TYPE']  # "tier-0-testing-done"

    # "CI_USER" and "CI_STATUS" are not always present.
    # I'm guessing this depends on whether "ci-publish" is a build step or
    # post-build step.
    ci_user = frame.headers.get('CI_USER')  # "atomic-e2e-jenkins", or None
    ci_status = frame.headers.get('CI_STATUS')  # "passed", or None

    mtmpl = "{ci_user}'s job {ci_name} {ci_status} {ci_type}"

    hostname = hostname_from_message_id(frame.headers['message-id'])

    if ci_user is None and hostname:
        # Set ci_user from the hostname FQDN in the message-id header.
        r = re.match('[^\.]+', hostname)
        ci_user = r.group()
    elif ci_user is None and hostname is None:
        # Unable to determine where this job is running.
        # Use a more general template.
        mtmpl = "jenkins job {ci_name} {ci_status} {ci_type}"

    if ci_status is None:
        ci_status = 'ran'

    # Many messages have a "github_pull_link" header.
    if 'github_pull_link' in frame.headers:
        mtmpl = "%s (%s)" % (mtmpl, frame.headers['github_pull_link'])

    message = mtmpl.format(**locals())
    product = product_from_hostname(hostname)
    return defer.succeed((message, product))


def hostname_from_message_id(message_id):
    """
    Get the hostname value from this message ID header.

    It seems all messages from Jenkins have a message ID that includes the
    FQDN.

    :param message_id: STOMP header string, eg.
                       "ID:ceph-jenkins.example.com-44193-1511460447792..."
    :returns: hostname string, eg. "ceph-jenkins.example.com", or None if we
              found no FQDN in the message ID.
    """
    r = re.match('ID:(.+)-\d+-', message_id)
    if r:
        return r.group(1)


def product_from_hostname(hostname):
    """
    Return a product name based on this Jenkins hostname.
    """
    if not hostname:
        return ''
    if hostname.endswith('-jenkins'):
        return hostname[:-8]
    return hostname
