import xmlrpclib
import json
import helga_umb.topics.eng.brew as brew
from twisted.internet import defer


URL = 'https://brewweb.engineering.redhat.com/brew/taskinfo?taskID=%d'


class Task(object):
    def __init__(self, method, state, info):
        self.method = method
        self.state = state
        self.info = info

    @classmethod
    def from_frame(cls, frame):
        method = frame.headers['method']
        state = frame.headers['new'].lower()
        data = json.loads(frame.body.decode())
        info = data['info']
        return cls(method, state, info)

    @property
    def url(self):
        return URL % self.info['id']

    @property
    def params(self):
        """
        Return a list of parameters in this task's request.

        If self.info['request'] is already a list, simply return it.

        If self.info['request'] is a raw XML-RPC string, parse it and return
        the params.
        """
        request = self.info['request']
        if isinstance(request, list):
            return request
        (params, _) = xmlrpclib.loads(request)
        return params

    @property
    def is_scratch(self):
        for param in self.params:
            if isinstance(param, dict):
                if param.get('scratch'):
                    return True
        return False

    @property
    def package(self):
        # params[0] is the src for some tasks:
        if self.method in ('build', 'buildArch', 'buildContainer',
                           'buildSRPMfromSCM'):
            src = self.params[0]
            return brew.package_from_src(src)

    @property
    def target(self):
        if self.method in ('build', 'buildContainer'):
            return self.params[1]
        if self.method in ('image'):
            return self.params[3]
        if self.method in ('createImage'):
            return self.params[0]

    @defer.inlineCallbacks
    def tag(self):
        if self.method == 'buildArch':
            tag = self.params[1]
            if isinstance(tag, int):
                # xmlrpc to getTag
                tag = yield brew.tag_name(tag)
            defer.returnValue(tag)
        if self.method == 'newRepo':
            tag = self.params[0]  # tag name, eg "foo-build"
            defer.returnValue(tag)

    @defer.inlineCallbacks
    def description(self):
        desc = self.method
        if self.is_scratch:
            desc = 'scratch %s' % desc
        if self.package:
            desc = '%s %s' % (self.package, desc)
        if self.target:
            desc += ' for %s' % self.target
        tag = yield self.tag()
        if tag:
            desc += ' for tag %s' % tag
        defer.returnValue(desc)


@defer.inlineCallbacks
def consume(client, channel, frame):
    task = Task.from_frame(frame)

    # Skip the notification tasks, it's just noise.
    # "tagBuild" is already covered separately by brew.build.tag messages.
    # "createrepo" is too low-level, newRepo is too noisy.
    if task.method in ('buildNotification', 'tagNotification', 'tagBuild',
                       'createrepo', 'newRepo', 'buildArch'):
        return

    owner_name = yield brew.owner_name(frame)
    description = yield task.description()
    mtmpl = "{owner_name}'s {description} task {state} ({url})"
    message = mtmpl.format(owner_name=owner_name,
                           description=description,
                           state=task.state,
                           url=task.url)
    client.msg(channel, message)
