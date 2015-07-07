#!/usr/local/bin/python

'''
Search for and retrieve threat indicators from ThreatExchange
'''

from __future__ import print_function

import json
import os
import re
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
        'access_token\=[A-Za-z0-9\%\|]+',
        'access_token=xxx|xxxx',
        url
    )


def get_query():
    '''
    Builds a query string based on the specified options
    '''
    fields = ({
        'access_token': FB_APP_ID + '|' + FB_ACCESS_TOKEN,
    })
    return SERVER + 'threat_exchange_members?' + urlencode(fields)


def process_results(data):
    '''
    Process the threat indicators received from the server.
    '''
    for row in data:
        if 'email'in row:
            email = row['email']
        else:
            email = ''

        print ('"' + row['name'] + '","' + email + '","' + row['id'] + '"')


def run_query(url):
    try:
        response = urlopen(url).read()
    except Exception as e:
        lines = str(e.info()).split('\r\n')
        msg = str(e)
        for line in lines:
            # Hacky way to get the exact error from the server
            result = re.search('^WWW-Authenticate: .*\) (.*)\"$', line)
            if result:
                msg = result.groups()[0]
        print ('ERROR: %s\n' % (msg))
        return True

    try:
        data = json.loads(response)
        if 'data' in data:
            process_results(data['data'])
        return False

    except Exception as e:
        print (str(e))
        return True

if __name__ == '__main__':
    run_query(get_query())
