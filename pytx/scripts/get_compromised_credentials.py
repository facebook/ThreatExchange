#!/usr/bin/env python

import argparse
import time

from pytx import ThreatIndicator
from pytx.vocabulary import ThreatExchange as te
from pytx.vocabulary import ThreatType as tt
from pytx.vocabulary import Types as t


def get_results(options):
    '''
    Builds a query string based on the specified options and runs it.
    '''

    if options.since is None or options.until is None:
        raise Exception('You must specify both "since" and "until" values')

    results = ThreatIndicator.objects(threat_type=tt.COMPROMISED_CREDENTIAL, type_=t.EMAIL_ADDRESS, limit=options.limit,
                                      fields=['indicator', 'passwords'], since=options.since, until=options.until)
    return results


def process_result(handle, result):
    '''
    Process the threat indicators received from the server. This version
    writes the indicators to the output file specified by 'handle', if any.
    Indicators are written one per line.
    '''

    for password in result.passwords:
        output = '%s:%s\n' % (result.indicator, password)
        if handle is None:
            print output,
        else:
            handle.write(output)


def run_query(options, handle):
    start = int(time.time())
    print 'READING %s%s' % (te.URL, te.THREAT_INDICATORS)
    results = get_results(options)

    count = 0
    for result in results:
        process_result(handle, result)
        count += 1

    end = int(time.time())
    print ('SUCCESS: Got %d indicators in %d seconds' %
           (count, end - start))

    return


def get_args():
    parser = argparse.ArgumentParser(description='Query ThreatExchange for Compromised Credentials')
    parser.add_argument('-o', '--output', default='/dev/stdout',
                        help='[OPTIONAL] output file path.')
    parser.add_argument('-s', '--since',
                        help='[OPTIONAL] Start time for search')
    parser.add_argument('-u', '--until',
                        help='[OPTIONAL] End time for search')
    parser.add_argument('-l', '--limit',
                        help='[OPTIONAL] Maximum number of results')

    return parser.parse_args()


def main():
    args = get_args()
    with open(args.output, 'w') as fp:
        run_query(args, fp)

if __name__ == '__main__':
    main()
