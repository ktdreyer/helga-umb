""" Announce dist-git commits. """
import json


def consume(client, channel, frame):
    # Interesting variables:
    branch = frame.headers['branch']  # "master"
    rev = frame.headers['rev']  # 82b7641313e64b4d725a0b86c6e46f979a7bdfff
    username = frame.headers['username']  # tli
    namespace = frame.headers['namespace']  # "tests"
    repo = frame.headers['repo']  # "kernel"

    data = json.loads(frame.body.decode())
    summary = data['summary']

    utmpl = ('http://pkgs.devel.redhat.com/cgit/{namespace}/{repo}'
             '/commit/?h={branch}&id={rev}')
    url = utmpl.format(namespace=namespace, repo=repo, branch=branch,
                       rev=rev)
    mtmpl = '{username} pushed "{summary}" {url}'
    message = mtmpl.format(username=username, summary=summary, url=url)
    client.msg(channel, message)
