#!/usr/local/bin/python

'''
Post compromised credentials to ThreatExchange
'''

from __future__ import print_function

import argparse
import hashlib
import json
import re
import sys
import time
from urllib import urlencode
from urllib2 import urlopen

FB_APP_ID = 'Your AppID Here'
FB_ACCESS_TOKEN = 'Your AccessToken Here'

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

def get_url():
    return SERVER + 'threat_indicators'

def post_datum(fields):
    try:
        start = int(time.time())
        print ('POST %s' % (clean_url(fields)))
        response = urlopen(get_url(), data=fields).read()
    except Exception as e:
        end = int(time.time())
        lines = str(e.info()).split('\r\n')
        msg = str(e)
        for line in lines:
            # Hacky way to get the exact error from the server
            result = re.search('^WWW-Authenticate: .*\) (.*)\"$', line)
            if result:
                msg = result.groups()[0]
        print ('ERROR: %s\nReceived in %d seconds' % (msg, end-start))
        return True

    print (response)

def parse_args(args):
    if args.input is None:
        raise Exception('You must specify an input file')
    if args.description is None:
        raise Exception('You must specify a description')

    privacy_members = None
    if args.privacy_type is None or args.privacy_type == 'VISIBLE':
        privacy_type = 'VISIBLE'
        share_level = 'GREEN'
    elif args.privacy_type == 'HAS_WHITELIST' or \
         args.privacy_type == 'HAS_BLACKLIST':
        share_level = 'AMBER'
        if args.privacy_members is None:
            raise Exception('You must specify privacy members')
        privacy_type = args.privacy_type
        privacy_members = args.privacy_members
    else:
        raise Exception('Invalid privacy_type')

    fields = ({
        'access_token' : FB_APP_ID + '|' + FB_ACCESS_TOKEN,
        'type' : 'EMAIL_ADDRESS',
        'threat_type' : 'COMPROMISED_CREDENTIAL',
        'description': args.description,
        'privacy_type' : privacy_type,
        'share_level' : share_level,
        'status' : 'UNKNOWN',
    })
    if privacy_members is not None:
        fields['privacy_members'] = privacy_members
    if args.report_url is not None:
        fields['report_url'] = args.report_url

    return fields

def post_data(args):
    base_fields = parse_args(args)
    handle = open(args.input, 'r')
    total = 0
    for line in handle.readlines():
        parts = line.split(':')
        if len(parts) != 2:
            continue

        email = parts[0]
        password = parts[1]

        # Basic input validation
        if not re.match('^[0-9a-f]{32}$', password, re.IGNORECASE):
            h = hashlib.md5()
            h.update(password)
            hash = h.hexdigest()
        else:
            hash = password

        fields = base_fields.copy()
        fields['indicator'] = email
        fields['password'] = hash

        post_datum(urlencode(fields))
        total += 1

    handle.close()
    return total

def get_parser():
    parser = argparse.ArgumentParser(
        description='Post Compromised Credentials to ThreatExchange',
    )
    parser.add_argument('-d', '--description')
    parser.add_argument('-i', '--input')
    parser.add_argument('-t', '--privacy-type')
    parser.add_argument('-m', '--privacy-members')
    parser.add_argument('-r', '--report-url')

    return parser

if __name__ == '__main__':
    start = int(time.time())
    args = get_parser().parse_args()
    count = post_data(args)
    print ('Uploaded %d credentials' % (count))
    end = int(time.time())
    print ('Total time elapsed: %d seconds' % (end - start))
