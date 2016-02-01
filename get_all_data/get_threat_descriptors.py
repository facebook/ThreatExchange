import csv
import argparse

from datetime import timedelta, datetime
from dateutil.parser import parse

from pytx import ThreatIndicator, ThreatDescriptor
from pytx.vocabulary import ThreatIndicator as TI, ThreatDescriptor as TD

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-I", "--include_expired", help="Search results will \
        match expired data", action="store_true")
    parser.add_argument("-M", "--max_confidence", help="The maximum allowed \
        confidence value for the data returned", type=int)
    parser.add_argument("-m", "--min_confidence", help="The minimum allowed \
        confidence value for the data returned", type=int)
    parser.add_argument("-O", "--owner", help="Comma separated list of AppIDs \
        of the person who submitted the data")
    parser.add_argument("-t", "--text", help="The text to match against")
    parser.add_argument("-R", "--review_status", help="The review status \
        (ReviewStatusType) to match")
    parser.add_argument("-H", "--share_level", help="The TLP Share Level \
        to match")
    parser.add_argument("-s", "--status", help="The status (StatusType) \
        to match")
    parser.add_argument("-S", "--strict_text", help="Search results will \
        only match strict text (without wildcards)", action="store_true")
    parser.add_argument("-y", "--threat_type", help="The threat_type of \
        indicator to search for")
    parser.add_argument("-T", "--type", help="The type of indicator for which \
        to search")
    parser.add_argument("-e", "--end_date", help="Search for descriptors \
        created up until a date (inclusive). The default is today's date. \
        Note that this date is converted to UTC time, so for example entering \
        1-27-16 would search until 1-27-16 00:00:00 UTC.",
        type=str, default=str(datetime.utcnow()))
    parser.add_argument("-d", "--days_back", help="Number of days prior to the \
        end_date from which results will be pulled.", type=int, default=1)
    return parser.parse_args()

def main():
    s = get_args()
    format_ = '%d-%m-%Y'
    for day_counter in range(s.days_back):
        # We use dateutil.parser.parse for its robustness in accepting different
        # datetime formats
        until_param = parse(s.end_date) - timedelta(days=day_counter)
        until_param_string = until_param.strftime(format_)

        since_param = until_param - timedelta(days=1)
        since_param_string = since_param.strftime(format_)

        output_file = 'threat_descriptors_' + since_param_string + '_to_' + \
            until_param_string + '.csv'
        with open(output_file,'wb') as fout:
            writer = csv.writer(fout)
            results = ThreatDescriptor.objects(
                fields=ThreatDescriptor._fields,
                include_expired=s.include_expired,
                limit=1000,
                max_confidence=s.max_confidence,
                min_confidence=s.min_confidence,
                owner=s.owner,
                text=s.text,
                review_status=s.review_status,
                share_level=s.share_level,
                status=s.status,
                strict_text=s.strict_text,
                threat_type=s.threat_type,
                type_=s.type,
                since=since_param_string,
                until=until_param_string,
            )

            # Headers
            writer.writerow([
                ")ID", # Need leading underscore so we don't confuse Excel
                "ADDED_ON",
                "CONFIDENCE",
                "DESCRIPTION",
                "EXPIRED_ON",
                "INDICATOR",
                "INDICATORS_TYPE",
                "INDICATOR_ID",
                "LAST_UPDATED",
                "OWNER_ID",
                "OWNER_NAME",
                "OWNER_EMAIL",
                "PRECISION",
                "RAW_INDICATOR",
                "REVIEW_STATUS",
                "SEVERITY",
                "SHARE_LEVEL",
                "STATUS",
                "THREAT_TYPE",
                "TYPE",
            ])
            for r in results:
                writer.writerow(
                    map(
                        lambda x: x if type(x) == int else
                            (x.encode('utf-8') if x else ""),
                        [
                            r.get(TD.ID),
                            r.get(TD.ADDED_ON),
                            r.get(TD.CONFIDENCE),
                            r.get(TD.DESCRIPTION),
                            r.get(TD.EXPIRED_ON),
                            r.get(TD.INDICATOR)['indicator'],
                            r.get(TD.INDICATOR)['type'],
                            r.get(TD.INDICATOR)['id'],
                            r.get(TD.LAST_UPDATED),
                            r.get(TD.OWNER)['id'],
                            r.get(TD.OWNER)['name'],
                            r.get(TD.OWNER)['email']
                                if 'email' in r.get(TD.OWNER).keys() else "",
                            r.get(TD.PRECISION),
                            r.get(TD.RAW_INDICATOR),
                            r.get(TD.REVIEW_STATUS),
                            r.get(TD.SEVERITY),
                            r.get(TD.SHARE_LEVEL),
                            r.get(TD.STATUS),
                            r.get(TD.THREAT_TYPE),
                            r.get(TD.TYPE),
                        ]
                    )
                )

if __name__ == "__main__":
    main()
