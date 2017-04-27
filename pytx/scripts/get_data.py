"""

This script demonstrates using pytx to query the ThreatExchange API.

Key parameters:

    -o (--object)       type of object to query; see main()
    -O (--output)       output stream (default /dev/stdout)  

If no value is supplied for --object:

    - The script fetches each type of object
    - It saves results in the working directory in files named [object_type].csv 

Sample usage:

    python scripts/fetch_data.py -o exchange_member -O /dev/stdout
    
    python scripts/fetch_data.py -o threat_descriptor -O /dev/stdout -t smarturl
  
"""


import argparse
import csv
from datetime import datetime

from pytx import (
    Malware,
    MalwareFamily,
    ThreatDescriptor,
    ThreatExchangeMember,
    ThreatIndicator,
    utils
)

from pytx.vocabulary import (
    Malware as MA,
    MalwareFamilies as MF,
    ThreatDescriptor as TD,
    ThreatExchangeMember as XM,
    ThreatIndicator as TI
)


def main():

    args = parse_arguments()

    if args.object is None:

        args.object = 'exchange_member'
        args.output = 'exchange_members.csv'
        query(args)

        args.object = 'malware_analysis'
        args.output = 'malware_analyses.csv'
        query(args)

        args.object = 'malware_family'
        args.output = 'malware_families.csv'
        query(args)

        args.object = 'threat_descriptor'
        args.output = 'threat_descriptors.csv'
        query(args)

        args.object = 'threat_indicator'
        args.output = 'threat_indicators.csv'
        query(args)

    else:

        query(args)


def query(args):

    """
    Query the ThreatExchange API at the specified endpoint.
    """

    # maximum number of indicators to fetch
    result_limit = 1000

    # write results to this stream
    output_stream = '/dev/stdout' if not args.output else args.output

    for day in range(args.days_back):

        # format date parameters for HTTP request
        until, until_str, since, since_str = utils.get_time_params(args.end_date, day, '%d-%m-%Y')

        with open(output_stream, 'wb') as ostream:

            print('Writing to %s...' % output_stream)

            writer = csv.writer(ostream)

            if args.object == 'exchange_member':

                engine = ThreatExchangeMember

                fields = [XM.ID, XM.NAME]

                parameters = dict()

            elif args.object == 'malware_analysis':

                engine = Malware

                fields = [
                    MA.ID,
                    MA.ADDED_ON,
                    MA.CRX,
                    MA.IMPHASH,
                    MA.MD5,
                    MA.PASSWORD,
                    MA.PE_RICH_HEADER,
                    MA.SAMPLE_TYPE,
                    MA.SAMPLE_SIZE_COMPRESSED,
                    MA.SHA1,
                    MA.SHA256,
                    MA.SHARE_LEVEL,
                    MA.SSDEEP,
                    MA.STATUS,
                    MA.VICTIM_COUNT,
                    MA.XPI,
                ]

                param_fields = Malware._default_fields
                if args.full_sample:
                    param_fields += ['sample_size', 'sample']

                parameters = dict(
                    fields=param_fields,
                    limit=result_limit,
                    text=args.text,
                    strict_text=args.strict_text,
                    sample_type=args.malware_type,
                    status=args.status,
                    share_level=args.share_level,
                    since=since_str,
                    until=until_str
                )

            elif args.object == 'malware_family':

                engine = MalwareFamily

                fields = [
                    MF.ID,
                    MF.ADDED_ON,
                    MF.ALIASES,
                    MF.DESCRIPTION,
                    MF.FAMILY_TYPE,
                    MF.MALICIOUS,
                    MF.NAME,
                    MF.SAMPLE_COUNT
                ]

                parameters = dict(
                    fields=MalwareFamily._fields,
                    limit=result_limit,
                    text=args.text,
                    strict_text=args.strict_text,
                    since=since_str,
                    until=until_str
                )

            elif args.object == 'threat_descriptor':

                engine = ThreatDescriptor

                fields = [
                    TD.ID,
                    TD.ADDED_ON,
                    TD.CONFIDENCE,
                    TD.DESCRIPTION,
                    TD.EXPIRED_ON,
                    [TD.INDICATOR, TI.INDICATOR],
                    [TD.INDICATOR, TI.TYPE],
                    [TD.INDICATOR, TI.ID],
                    TD.LAST_UPDATED,
                    [TD.OWNER, XM.ID],
                    [TD.OWNER, XM.NAME],
                    [TD.OWNER, XM.EMAIL],
                    TD.PRECISION,
                    TD.RAW_INDICATOR,
                    TD.REVIEW_STATUS,
                    TD.SEVERITY,
                    TD.SHARE_LEVEL,
                    TD.STATUS
                ]

                parameters = dict(
                    fields=ThreatDescriptor._fields,
                    include_expired=args.include_expired,
                    min_confidence=args.confidence_lb,
                    max_confidence=args.confidence_ub,
                    owner=args.owner,
                    review_status=args.review_status,
                    share_level=args.share_level,
                    status=args.status,
                    limit=result_limit,
                    text=args.text,
                    strict_text=args.strict_text,
                    type_=args.indicator_type,
                    since=since_str,
                    until=until_str
                )

            elif args.object == 'threat_indicator':

                engine = ThreatIndicator

                fields = [TI.ID, TI.INDICATOR, TI.TYPE]

                parameters = dict(
                    fields=ThreatIndicator._fields,
                    limit=result_limit,
                    text=args.text,
                    strict_text=args.strict_text,
                    type_=args.indicator_type,
                    since=since_str,
                    until=until_str
                )

            objects = engine.objects(**parameters)
            headers = [utils.convert_to_header(f) for f in fields]
            writer.writerow(headers)

            for i, o in enumerate(objects):
                data = [i] + [utils.get_data_field(f, o) for f in fields]
                writer.writerow(data)


def parse_arguments():
    parser = argparse.ArgumentParser()

    add = parser.add_argument

    add('-d', '--days_back', help='Number of days to look back', type=int, default=1)
    add('-e', '--end_date', help='Date upper bound (inclusive) (UTC)', type=str, default=str(datetime.utcnow()))
    add('-f', '--full_sample', help='Full sample', action='store_true')
    add('-i', '--indicator_type', help='Threat indicator type')
    add('-L', '--confidence_lb', help='Confidence lower bound', type=int)
    add('-l', '--share_level', help='Share level')
    add('-m', '--malware_type', help='Malware sample type')
    add('-O', '--output', help='Output stream')
    add('-o', '--object', help='Object type')
    add('-r', '--review_status', help='Review status')
    add('-s', '--status', help='Status')
    add('-T', '--strict_text', help='Strict text query (no wildcards)', action='store_true')
    add('-t', '--text', help='Text query')
    add('-U', '--confidence_ub', help='Confidence upper bound', type=int)
    add('-w', '--owner', help='Comma-separated list of AppIDs')
    add('-x', '--include_expired', help='Include expired data', action='store_true')

    return parser.parse_args()


if __name__ == '__main__':
    main()
