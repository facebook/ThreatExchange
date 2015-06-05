#!/usr/bin/env python

import argparse
import json
import time

from pytx import ThreatIndicator
from pytx.vocabulary import ThreatExchange as te


def process_results(handle, data):
    '''
    Process the threat indicators received from the server. This version
    writes the indicators to the output file specified by 'handle', if any.
    Indicators are written one per line, formatted in JSON.
    '''
    handle.write(json.dumps(data))
    handle.write('\n')


def run_query(options, handle):
    start = int(time.time())
    print 'READING %s%s' % (te.URL, te.THREAT_INDICATORS)

    # query = get_query(options)
    if not options.type and not options.text:
        raise Exception('You must specify either a type or text')

    count = 0
    results = ThreatIndicator.objects(__raw__=options.__dict__, dict_generator=True)
    for result in results:
        process_results(handle, result)
        count += 1

    end = int(time.time())
    print ('SUCCESS: Got %d indicators in %d seconds' %
           (count, end - start))

    return


def get_args():
    parser = argparse.ArgumentParser(description='Query ThreatExchange')
    parser.add_argument('-t', '--type',
                        help='[OPTIONAL] ThreatExchane type')
    parser.add_argument('-y', '--threat-type',
                        help='[OPTIONAL] ThreatExchane threat-type')
    parser.add_argument('-x', '--text',
                        help='[OPTIONAL] ThreatExchane search text')
    parser.add_argument('-o', '--output', default='/dev/stdout',
                        help='[OPTIONAL] output file path.')
    parser.add_argument('-s', '--since',
                        help='[OPTIONAL] Start time for search')
    parser.add_argument('-u', '--until',
                        help='[OPTIONAL] End time for search')

    return parser.parse_args()


def main():
    args = get_args()

    with open(args.output, 'w') as fp:
        run_query(args, fp)

if __name__ == '__main__':
    main()
