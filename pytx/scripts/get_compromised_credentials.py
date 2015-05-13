#!/usr/bin/env python

import argparse
import sys
import time

from pytx import init
from pytx import ThreatIndicator
from pytx.vocabulary import ThreatExchange as te
from pytx.vocabulary import ThreatType as tt
from pytx.vocabulary import Types as t


app_id = '<your-app-id>'
app_secret = '<your-app-secret>'

init(app_id, app_secret)

def get_results(options):
    '''
    Builds a query string based on the specified options and runs it.
    '''

    if options.since is None or options.until is None:
        raise Exception('You must specify both "since" and "until" values')


    query = {
        'threat_type': tt.COMPROMISED_CREDENTIAL,
        'type' : t.EMAIL_ADDRESS,
        'fields' : 'indicator,passwords',
        'since' : options.since,
        'until' : options.until,
    }

    results = ThreatIndicator.objects(__raw__=query, dict_generator=True)
    return results

def process_results(handle, data):
    '''
    Process the threat indicators received from the server. This version
    writes the indicators to the output file specified by 'handle', if any.
    Indicators are written one per line, formatted in JSON.
    '''
    if handle is None:
        return

    handle.write('%s:%s\n' % (data['indicator'], data['passwords'][0]))

def run_query(options, handle):
    try:
        start = int(time.time())
        print 'READING %s%s' % (te.URL, te.THREAT_INDICATORS)
        results = get_results(options)
    except Exception, e:
        print str(e)
        sys.exit(1)

    count = 0
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
    parser = argparse.ArgumentParser(
        description='Query ThreatExchange for Compromised Credentials',
    )
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
