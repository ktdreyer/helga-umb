import json
import smokesignal
from twisted.internet import defer
from helga import log


logger = log.getLogger(__name__)


BASEURL = 'https://errata.devel.redhat.com/'

# Huge name that we shorten to make easier to read:
ROBOSIG = 'robosignatory/robosignatory.host.prod.eng.bos.redhat.com@REDHAT.COM'


@smokesignal.on('umb.eng.errata.activity.created')
def activity_created(frame):
    """ Announce ET advisory creations. """
    advisory = AdvisoryActivity(**frame.headers)
    mtmpl = '{who} created new {release} {type} advisory {url}'
    message = advisory.format(mtmpl)
    return defer.succeed((message, advisory.product))


@smokesignal.on('umb.eng.errata.activity.docs_approval')
def activity_docs_approval(frame):
    """ Announce ET docs approval changes. """
    advisory = AdvisoryActivity(**frame.headers)

    # set an "action"
    advisory.action = advisory.to
    if advisory.to == "docs_approval_requested":  # Is this always true here?
        advisory.action = 'requested docs approval'
    if advisory.to == "docs_approved":  # Does this ever happen?
        advisory.action = 'approved the docs'

    mtmpl = '{who} {action} on {release} {url}'
    message = advisory.format(mtmpl)
    return defer.succeed((message, advisory.product))


@smokesignal.on('umb.eng.errata.activity.security_approval')
def activity_security_approval(frame):
    """ Announce ET docs approval changes. """
    advisory = AdvisoryActivity(**frame.headers)

    # defensively init default action str:
    advisory.action = 'changed security approval'
    if advisory.to == 'true':
        advisory.action = 'approved security'
    if advisory.to == 'false':
        # ET comments this action as "Product Security approval requested."
        advisory.action = 'requested security approval'

    mtmpl = '{who} {action} on {release} {url}'
    message = advisory.format(mtmpl)
    return defer.succeed((message, advisory.product))


@smokesignal.on('umb.eng.errata.activity.people.assigned_to')
def activity_people_assigned_to(frame):
    advisory = AdvisoryActivity(**frame.headers)
    mtmpl = '{who} assigned QE of {release} {url} to {to}'
    message = advisory.format(mtmpl)
    return defer.succeed((message, advisory.product))


@smokesignal.on('umb.eng.errata.activity.people.package_owner')
def activity_people_package_owner(frame):
    advisory = AdvisoryActivity(**frame.headers)
    mtmpl = '{who} set package owner of {release} {url} to {to}'
    message = advisory.format(mtmpl)
    return defer.succeed((message, advisory.product))


@smokesignal.on('umb.eng.errata.activity.people.manager')
def activity_people_package_manager(frame):
    advisory = AdvisoryActivity(**frame.headers)
    mtmpl = '{who} set manager of {release} {url} to {to}'
    message = advisory.format(mtmpl)
    return defer.succeed((message, advisory.product))


@smokesignal.on('umb.eng.errata.activity.signing')
def activity_signing(frame):
    advisory = AdvisoryActivity(**frame.headers)
    mtmpl = '{who} signed {to} in {release} {url}'
    message = advisory.format(mtmpl)
    return defer.succeed((message, advisory.product))


@smokesignal.on('umb.eng.errata.activity.status')
def activity_status(frame):
    advisory = AdvisoryActivity(**frame.headers)
    mtmpl = '{who} changed {release} {url} to {to} status'
    message = advisory.format(mtmpl)
    return defer.succeed((message, advisory.product))


@smokesignal.on('umb.eng.errata.activity.text_changes')
def activity_text_changes(frame):
    advisory = AdvisoryActivity(**frame.headers)
    data = json.loads(frame.body.decode())
    # "text_changes" key contains a list of things that changed, like so:
    # 'text_changes': [{'name': 'description',
    #                   'from': "My old description text",
    #                   'to': "My new description text",
    #                  }]
    text_changes = data['text_changes']
    changes = describe_text_changes(text_changes)
    mtmpl = '{who} changed {changes} on {release} {url}'
    message = advisory.format(mtmpl, changes=changes)
    return defer.succeed((message, advisory.product))


@smokesignal.on('umb.eng.errata.batch.push.complete')
def batch_push_complete(frame):
    who = frame.headers['who']  # "kdreyer@redhat.com"
    batch_name = frame.headers['batch_name']  # "RHEL-7.4.3-Extras"
    mtmpl = '{who} completed batch push for {batch_name}'
    message = mtmpl.format(who=who, batch_name=batch_name)
    return defer.succeed((message, advisory.product))


@smokesignal.on('umb.eng.errata.bugs.changed')
def bugs_changed(frame):
    advisory = AdvisoryActivity(**frame.headers)
    data = json.loads(frame.body.decode())
    # "added" looks like:
    # 'added': [{'id': 1450475, 'type': 'RHBZ'}],
    added = data['added']
    dropped = data['dropped']
    change = ''
    if added:
        change = 'added %s' % describe_bugs(added)
    if dropped:
        if added:
            change += ' and '
        change += 'dropped %s' % describe_bugs(dropped)
    mtmpl = '{who} {change} in {release} {url}'
    message = advisory.format(mtmpl, change=change)
    return defer.succeed((message, advisory.product))


@smokesignal.on('umb.eng.errata.build.files_reloaded')
def build_files_reloaded(frame):
    """ Announce ET build list reloads. """
    # ("who" is always qa-errata-list@redhat.com. An ET bug?)
    advisory = AdvisoryActivity(**frame.headers)
    build_nvr = frame.headers['build_nvr']  # "udisks2-2.7.3-3.el7"
    mtmpl = '{who} reloaded build list for {build_nvr} for {release} {url}'
    message = advisory.format(mtmpl, build_nvr=build_nvr)
    return defer.succeed((message, advisory.product))


@smokesignal.on('umb.eng.errata.build.flags_changed')
def build_flags_changed(frame):
    """ Announce ET build flag changes. """
    advisory = AdvisoryActivity(**frame.headers)
    brew_build = frame.headers['brew_build']  # "udisks2-2.7.3-3.el7"
    data = json.loads(frame.body.decode())
    from_flags = ''
    if data['from']:
        from_flags = 'from %s' % ', '.join(data['from'])
    to_flags = 'to %s' % ', '.join(data['to'])
    mtmpl = '{who} changed flags {from_flags} {to_flags} for {brew_build} for {release} {url}'  # NOQA: E501
    message = advisory.format(mtmpl,
                              brew_build=brew_build,
                              from_flags=from_flags,
                              to_flags=to_flags)
    return defer.succeed((message, advisory.product))


@smokesignal.on('umb.eng.errata.v2.builds.changed')
def v2_builds_changed(frame):
    advisory = AdvisoryActivity(**frame.headers)
    data = json.loads(frame.body.decode())
    # "added" looks like:
    # 'added': [{'nvr': 'sssd-docker-7.4-13',
    #           'product_versions': ['EXTRAS-7.4-RHEL-7']}]
    added = data['added']
    removed = data['removed']
    change = ''
    if added:
        nvrs = ', '.join([build['nvr'] for build in added])
        change = 'added %s' % nvrs
    if removed:
        if added:
            change += ' and '
        nvrs = ', '.join([build['nvr'] for build in removed])
        change += 'removed %s' % nvrs
    advisory.action = change
    mtmpl = '{who} {action} in {release} {url}'
    message = advisory.format(mtmpl)
    return defer.succeed((message, advisory.product))


class AdvisoryActivity(object):
    """ represent an advisory change. """
    def __init__(self, **kwargs):
        """ Designed to pass in a frame dict here """
        self._who = kwargs['who']  # "kdreyer@redhat.com"
        self.product = kwargs['product']  # "RHEL-EXTRAS"
        self.release = kwargs['release']  # "Extras-RHEL-7.4"
        self.type = kwargs['type']  # "RHBA"
        if 'id' in kwargs:
            self.id = int(kwargs['id'])  # 12345
        else:
            self.id = int(kwargs['errata_id'])
        self.to = kwargs.get('to')  # a change "to" this value.
        self.action = None  # populate this later, if at all.

    @property
    def who(self):
        # Easier-to-read summary of this long user ID:
        if self._who == ROBOSIG:
            return 'robosignatory'
        # Strip @redhat.com suffix:
        if self._who.lower().endswith('@redhat.com'):
            return self._who[:-11]
        return self._who

    @property
    def url(self):
        return '%sadvisory/%d' % (BASEURL, self.id)

    def as_dict(self):
        """ Represent ourselves as a dict """
        return {
            'action': self.action,
            'id': self.id,
            'product': self.product,
            'release': self.release,
            'to': self.to,
            'type': self.type,
            'url': self.url,
            'who': self.who,
        }

    def format(self, template, **kwargs):
        """
        Format ourselves as a string according to this template.

        :param **kwargs: any other values to add into the format string.
        :returns: formatted string
        """
        values = self.as_dict()
        values.update(kwargs)
        return template.format(**values)


def describe_text_changes(text_changes):
    """ Return a textual description (str) for a list of text fields. """
    return ', '.join([change['name'] for change in text_changes])


def describe_bug(bug):
    """ Return a textual description for a single bug. """
    if bug['type'] == 'RHBZ':
        return 'rhbz#%d' % bug['id']
    return '%s %s' % (bug['type'], bug['id'])


def describe_bugs(bugs):
    """ Return a textual description for a list of bugs. """
    return ', '.join([describe_bug(bug) for bug in bugs])
