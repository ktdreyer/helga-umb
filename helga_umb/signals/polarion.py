""" Announce Polarion messages. """
import json
import smokesignal
from twisted.internet import defer
from helga import log


logger = log.getLogger(__name__)


@smokesignal.on('umb.qe.ci.polarion')
def polarion(frame):
    polarion_type = frame.headers['type']  # "import-results"
    payload = '(cannot parse this type)'  # TODO: show datagrepper URL

    if polarion_type == 'import-results':
        data = json.loads(frame.body.decode())
        # Some messages lack a "import-results" key. I'm not sure why.
        # Log everthing when this happens so we can debug more.
        import_results = data.get('import-results')
        if not import_results:
            from pprint import pprint
            pprint(frame.headers)
            pprint(data)
        payload = describe_results(import_results)
        # Other interesting pieces:
        # jenkins_job_url = frame.headers['jenkins-job-url']
        # log_url = data['log-url']  # 'http://ops-qe-logstash-2.example.com:9981/polarion/RedHatEnterpriseLinux7/20171129-224014.749.log
        testrun_url = data.get('testrun-url')  # https://polarion.engineering.redhat.com/polarion/#/project/RedHatEnterpriseLinux7/testrun?id=RTT-RUN_Tier1_RHEL-7_5-20171129_n_4_Server_ppc64  # NOQA: E501
        if testrun_url:
            project = find_project(testrun_url)
        else:
            project = ''

    if polarion_type == 'import-testcases':
        data = json.loads(frame.body.decode())
        import_testcases = data['import-testcases']
        payload = describe_testcases(import_testcases)

    mtmpl = "polarion {polarion_type}: {payload}"
    message = mtmpl.format(polarion_type=polarion_type,
                           payload=payload)
    product = project
    return defer.succeed((message, product))


def describe_result(result):
    """ Describe the result from "import-results" """
    status = result['status']
    suite_name = result['suite-name']
    return '%s %s' % (status, suite_name)


def describe_results(results):
    """ Describe all results from "import-results" """
    # I'm not sure there can be more than one result, but the data is a list in
    # JSON, so let's theoretically handle more than one.
    descriptions = [describe_result(result) for result in results]
    return ', '.join(descriptions)


def describe_testcases(testcases):
    """ Describe all testcases from "import-testcases" """
    # If we have a few, just return them all (often it's just one).
    if len(testcases) < 4:
        descriptions = [testcase['id'] for testcase in testcases]
        return ', '.join(descriptions)
    # If we have more than three, list the first three, then count the rest.
    # (I've seen 170 sent at a time here)
    firstdescriptions = [testcase['id'] for testcase in testcases[:3]]
    first = ', '.join(firstdescriptions)
    more = len(testcases) - 3
    return '{first} and {num} more'.format(first=first, num=more)


def find_project(testrun_url):
    """
    Find a project name from this Polarion testrun URL.

    :param testrun_url: Polarion test run URL
    :returns: project name eg "CEPH" or "ContainerNativeStorage"
    """
    url_suffix = testrun_url[59:]
    index = url_suffix.index('/')
    return url_suffix[:index]
