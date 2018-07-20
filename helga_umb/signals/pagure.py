import json
import smokesignal
from twisted.internet import defer
import posixpath
from helga import log


logger = log.getLogger(__name__)

BASEURL = 'https://src.osci.redhat.com/'

# to add more callbacks here, see
# https://apps.fedoraproject.org/datagrepper/raw?category=pagure for
# message format inspiration


@smokesignal.on('umb.eng.pagure.commit.flag.added')
@smokesignal.on('umb.eng.pagure.commit.flag.updated')
def commit_flag_updated(frame):
    data = json.loads(frame.body)
    repo = data['repo']
    url_path = repo['url_path']
    flag = data['flag']
    status = flag['status']
    commit_hash = flag['commit_hash']

    url = commit_url(url_path, commit_hash)
    mtmpl = "pagure flag {status} for {url}"
    message = mtmpl.format(status=status, url=url)
    return defer.succeed((message, ''))


@smokesignal.on('umb.eng.pagure.pull-request.new')
def pull_request_new(frame):
    data = json.loads(frame.body)
    agent = data['agent']
    pullrequest = data['pullrequest']
    id_ = pullrequest['id']
    project = pullrequest['project']
    project_name = project['name']
    title = pullrequest['title']

    mtmpl = "{agent} opened Pagure PR #{id} {project} {title}"
    message = mtmpl.format(agent=agent,
                           id=id_,
                           project=project_name,
                           title=title)
    return defer.succeed((message, ''))


def commit_url(url_path, commit_hash):
    """
    Find the URL for this repository/commit.

    :param url_path: eg. "rpms/gtk-vnc"
    :param commit_hash: str, git commit sha1
    """
    return posixpath.join(BASEURL, url_path, 'c', commit_hash)
