import json
import smokesignal
from twisted.internet import defer


@smokesignal.on('umb.eng.resultsdb.result.new')
def result_new(frame):
    data = json.loads(frame.body)
    testcase_name = data['testcase']['name']
    outcome = data['outcome']
    items = ' '.join(data['data']['item'])
    # URL to result:
    # href = data['href']

    mtmpl = "resultsdb saw {testcase_name} {outcome} for {items}"
    message = mtmpl.format(testcase_name=testcase_name,
                           outcome=outcome,
                           items=items)
    product = ''  # not sure how to determine this
    return defer.succeed((message, product))
