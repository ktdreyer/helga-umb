""" Announce ccat reschedule_test messages. """

JIRA = 'https://projects.engineering.redhat.com/browse/%s'
ERRATA = 'https://errata.devel.redhat.com/advisory/%d'


def consume(client, channel, frame):
    jira_issue = frame.headers['JIRA_ISSUE_ID']
    jira_url = JIRA % jira_issue
    # errata_id = int(frame.headers['ERRATA_ID'])
    # TODO: look up this errata_id and determine the product for product-based
    # filtering.
    message = 'ccat rescheduled for %s' % jira_url
    client.msg(channel, message)
