"""

This script demonstrates using pytx to publish data to the ThreatExchange API. 

Sample usage:

    python -t DOMAIN -i evil_domain.com -l RED -d baaad -m [APP_ID_LIST] -p HAS_WHITELIST -s MALICIOUS

"""

import argparse

from pytx import ThreatDescriptor


def main():

    args = parse_arguments()

    post(args)


def post(args):

    response = ThreatDescriptor.new(vars(args))
    print(response)


def parse_arguments():
    parser = argparse.ArgumentParser()

    add = parser.add_argument

    add('-d', '--description')
    add('-i', '--indicator')
    add('-l', '--share_level')
    add('-m', '--privacy_members')
    add('-p', '--privacy_type')
    add('-s', '--status')
    add('-T', '--tags')
    add('-t', '--type')

    return parser.parse_args()


if __name__ == '__main__':
    main()