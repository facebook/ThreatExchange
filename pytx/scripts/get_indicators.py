#!/usr/bin/env python

import argparse
import json
import sys
import time

from pytx import init
from pytx import ThreatIndicator
from pytx.vocabulary import ThreatExchange as te


app_id = '<your-app-id>'
app_secret = '<your-app-secret>'

init(app_id, app_secret)

def get_query(options):
    '''
    Builds a query string based on the specified options
    '''

    if options.type is None and options.text is None:
        raise Exception('You must specify either a type or text')

    fields = {}
    if options.type is not None:
        fields['type'] = options.type
    if options.threat_type is not None:
        fields['threat_type'] = options.threat_type
    if options.text is not None:
        fields['text'] = options.text
    if options.since is not None:
        fields['since'] = options.since
    if options.until is not None:
        fields['until'] = options.until

    return fields

def process_results(handle, data):
    '''
    Process the threat indicators received from the server. This version
    writes the indicators to the output file specified by 'handle', if any.
    Indicators are written one per line, formatted in JSON.
    '''
    if handle is None:
        return

    handle.write(json.dumps(data))
    handle.write('\n')

def run_query(options, handle):
    try:
        start = int(time.time())
        print 'READING %s%s' % (te.URL, te.THREAT_INDICATORS)
        query = get_query(options)
    except Exception, e:
        print str(e)
        sys.exit(1)

    count = 0
    results = ThreatIndicator.objects(__raw__=query, dict_generator=True)
    for result in results:
        process_results(handle, result)
        count += 1

    try:
        end = int(time.time())
        print ('SUCCESS: Got %d indicators in %d seconds' %
            (count, end-start))

        if handle:
            handle.close()
    except Exception as e:
        print (str(e))

    return

def get_parser():
    parser = argparse.ArgumentParser(description='Query ThreatExchange')
    parser.add_argument('-t', '--type')
    parser.add_argument('-y', '--threat-type')
    parser.add_argument('-x', '--text')
    parser.add_argument('-o', '--output')
    parser.add_argument('-s', '--since')
    parser.add_argument('-u', '--until')

    return parser

if __name__ == '__main__':
    args = get_parser().parse_args()
    if args.output is not None:
        handle = open(args.output, 'w')
    else:
        handle = None
    start = int(time.time())
    run_query(args, handle)
    end = int(time.time())
    print ('Total time elapsed: %d seconds' % (end - start))
