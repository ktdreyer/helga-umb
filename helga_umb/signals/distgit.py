import json
import sys
import smokesignal
from twisted.internet import defer
from helga_umb.signals.util import product_from_branch


BASEURL = 'http://pkgs.devel.redhat.com/cgit/'


@smokesignal.on('umb.eng.distgit.commit')
def commit(frame):
    branch = frame.headers['branch']  # "master"
    rev = frame.headers['rev']  # 82b7641313e64b4d725a0b86c6e46f979a7bdfff
    username = frame.headers['username']  # tli
    namespace = frame.headers['namespace']  # "tests"
    repo = frame.headers['repo']  # "kernel"

    data = json.loads(frame.body.decode())
    summary = data['summary']

    # This could have unicode that needs an explicit conversion on py2.
    if sys.version_info.major < 3:
        summary = summary.encode('utf-8')

    utmpl = ('{baseurl}{namespace}/{repo}/commit/?h={branch}&id={rev}')
    url = utmpl.format(baseurl=BASEURL,
                       namespace=namespace,
                       repo=repo,
                       branch=branch,
                       rev=rev)
    mtmpl = '{username} pushed "{summary}" {url}'
    message = mtmpl.format(username=username, summary=summary, url=url)
    product = product_from_branch(branch)
    return defer.succeed((message, product))
