#!/usr/bin/env python

import argparse
import json
import sys
import time

from pytx import Malware
from pytx import ThreatExchangeMember
from pytx import ThreatIndicator
from pytx import vocabulary
from pytx.common import Common

def get_arg_parser():
    """
    Establishes a verb and options for each API endpoint.
    """
    parser = argparse.ArgumentParser(description='Query Facebook ThreatExchange')

    subparsers = parser.add_subparsers(help='sub-command help', dest='api')

    # https://graph.facebook.com/threat_exchange_members
    members_parser = subparsers.add_parser('members', help='Call the /threat_exchange_members API endpoint')

    # https://graph.facebook.com/malware_analyses
    malware_parser = subparsers.add_parser('malware', help='Call the /malware_analyses API endpoint')
    malware_parser.add_argument('--limit', default=1000, type=int,
        help='Defines the maximum size of a page of results. The maximum is %(default).')
    malware_parser.add_argument('--text',
        help='Freeform text field with a value to search for. '
        'This can be a file hash or a string found in other fields of the objects.')
    malware_parser.add_argument('--strict_text', default=False, action='store_true',
        help='When set, the API will not do approximate matching on the value in text')
    malware_parser.add_argument('--since', default=None,
        help='Returns malware collected after a timestamp')
    malware_parser.add_argument('--until', default=None,
        help='Returns malware collected before a timestamp')

    # https://graph.facebook.com/threat_indicators
    indicators_parser = subparsers.add_parser('indicators', help='Call the /threat_indicators API endpoint')
    indicators_parser.add_argument('--limit', default=1000, type=int,
        help='Defines the maximum size of a page of results.')
    indicators_parser.add_argument('--text',
        help='Freeform text field with a value to search for. '
        'This can be a file hash or a string found in other fields of the objects.')
    indicators_parser.add_argument('--strict_text', default=False, action='store_true',
        help='When set, the API will not do approximate matching on the value in text')
    indicators_parser.add_argument('--threat_type',
        help='The broad threat type the indicator is associated with')
    indicators_parser.add_argument('--type',
        help='The type of indicators to search for')
    indicators_parser.add_argument('--since', default=None,
        help='Returns malware collected after a timestamp')
    indicators_parser.add_argument('--until', default=None,
        help='Returns malware collected before a timestamp')

    # https://graph.facebook.com/<object-id>
    objid_parser = subparsers.add_parser('objid', help='Call the /<object-id> API endpoint')
    objid_parser.add_argument('--id',
        help='The object-id to search for.')
    objid_parser.add_argument('--connections', default=False, action='store_true',
        help='Pull the connections for an object.')

    # Print elements of the vocab
    vocab_parser = subparsers.add_parser('docs', help='Documentation for ThreatExchange vocabulary')
    for elem in [elem.lower() for elem in dir(vocabulary) if not elem.startswith('__')]:
        vocab_parser.add_argument('--{0}'.format(elem), default=False, action='store_true',
            help='List valid values for {0}'.format(elem))

    return parser

def objid_main(args):
    """
    Call the /<object-id> API endpoint and print the results.

    :param args: Command line arguments
    :type args: ArgumentParser    
    """
    indicator = Common.details(id=args.id, full_response=True, metadata=True)
    sys.stdout.write(json.dumps(indicator))
    sys.stdout.write('\n')

    if args.connections:
        for connection_name in indicator.get('metadata', {}).get('connections', {}).keys():
            connections = Common.details(id=args.id, connection=connection_name,full_response=True, metadata=True, dict_generator=True)
            for connected in connections:
                if connected:
                    sys.stdout.write(json.dumps(connected))
                    sys.stdout.write('\n')

def indicators_main(args):
    """
    Call the /threat_indicators API endpoint and print the results.

    :param args: Command line arguments
    :type args: ArgumentParser    
    """
    indicators = ThreatIndicator.objects(text=args.text, strict_text=args.strict_text, limit=args.limit, 
        type_=args.type, threat_type=args.threat_type, 
        since=args.since, until=args.until, dict_generator=True)
    for indicator in indicators:
        sys.stdout.write(json.dumps(indicator))
        sys.stdout.write('\n')

def malware_main(args):
    """
    Call the /malware_analyses API endpoint and print the results.

    :param args: Command line arguments
    :type args: ArgumentParser    
    """
    malwares = Malware.objects(text=args.text, strict_text=args.strict_text, limit=args.limit, 
        since=args.since, until=args.until, dict_generator=True)
    for malware in malwares:
        sys.stdout.write(json.dumps(malware))
        sys.stdout.write('\n')

def members_main(args):
    """
    Call the /threat_exchange_members API endpoint and print the results.

    :param args: Command line arguments
    :type args: ArgumentParser    
    """
    members = ThreatExchangeMember.objects(dict_generator=True)
    for member in members:
        sys.stdout.write(json.dumps(member))
        sys.stdout.write('\n')

def doc_class(cls):
    """
    Prints the documentation for a class.

    :param cls: A class
    :type cls: A class
    """
    doc_strs = [elem.strip() for elem in cls.__doc__.split('\n')]
    keys = [key for key in cls.__dict__.keys() if not key.startswith('__')]

    for doc_str in doc_strs:
        if doc_str:
            sys.stdout.write(doc_str)
            sys.stdout.write('\n')
    for key in keys:
        sys.stdout.write('\t{0}\n'.format(key))

def docs_main(args):
    """
    Entry point for the 'docs' command.

    :param args: Command line arguments
    :type args: ArgumentParser
    """
    for elem in [elem for elem in dir(vocabulary) if not elem.startswith('__')]:
        if getattr(args, elem.lower(), False):
            doc_class(getattr(vocabulary, elem))

def main():
    parser = get_arg_parser()
    args = parser.parse_args()

    if args.api == 'members':
        members_main(args)
    elif args.api == 'malware':
        malware_main(args)
    elif args.api == 'indicators':
        indicators_main(args)
    elif args.api == 'objid':
        objid_main(args)
    elif args.api == 'connection':
        pass
    elif args.api == 'docs':
        docs_main(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
