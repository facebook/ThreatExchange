#!/usr/local/bin/python

'''
Search for and retrieve threat indicators from ThreatExchange
'''

from __future__ import print_function

import argparse
import json
import os
import re
import time
from urllib import urlencode
from urllib2 import urlopen

FB_APP_ID = os.environ['TX_APP_ID']
FB_ACCESS_TOKEN = os.environ['TX_APP_SECRET']

SERVER = 'https://graph.facebook.com/'


def clean_url(url):
    '''
    Removes the access token from the URL to display onscreen
    '''
    return re.sub(
        'access_token\=[A-Za-z0-9\%\|]+&',
        'access_token=xxx|xxxx&',
        url
    )


def get_query(options):
    '''
    Builds a query string based on the specified options
    '''
    if options.type is None and options.text is None:
        raise Exception('You must specify either a type or text')

    fields = ({
        'access_token': FB_APP_ID + '|' + FB_ACCESS_TOKEN,
    })
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

    return SERVER + 'threat_indicators?' + urlencode(fields)


def process_results(handle, data):
    '''
    Process the threat indicators received from the server. This version
    writes the indicators to the output file specified by 'handle', if any.
    Indicators are written one per line, formatted in JSON.
    '''
    if handle is None:
        return

    for d in data:
        handle.write(json.dumps(d))
        handle.write('\n')


def run_query(url, handle):
    try:
        start = int(time.time())
        print ('READING %s' % (clean_url(url)))
        response = urlopen(url).read()
    except Exception as e:
        end = int(time.time())
        lines = str(e.info()).split('\r\n')
        msg = str(e)
        for line in lines:
            # Hacky way to get the exact error from the server
            result = re.search('^WWW-Authenticate: .*\) (.*)\"$', line)
            if result:
                msg = result.groups()[0]
        print ('ERROR: %s\nReceived in %d seconds' % (msg, end - start))
        return True

    try:
        end = int(time.time())
        data = json.loads(response)
        print ('SUCCESS: Got %d indicators in %d seconds' %
               (len(data['data']), end - start))

        if 'data' in data:
            process_results(handle, data['data'])

        if 'paging' in data:
            paging = data['paging']
            if 'next' in paging:
                return run_query(paging['next'], handle)

        print ('No next link. Done.')
        if handle:
            handle.close()
        return False

    except Exception as e:
        print (str(e))
        return True


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
    run_query(get_query(args), handle)
    end = int(time.time())
    print ('Total time elapsed: %d seconds' % (end - start))
