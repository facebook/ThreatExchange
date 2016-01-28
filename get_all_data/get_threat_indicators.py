import csv
import argparse

from datetime import timedelta, datetime
from dateutil.parser import parse

from pytx import ThreatIndicator
from pytx.vocabulary import ThreatIndicator as TI

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--text", help="The text to match against")
    parser.add_argument("-S", "--strict_text", help="Search results will only \
        match strict text (without wildcards)", action="store_true")
    parser.add_argument("-y", "--threat_type", help="The threat_type of \
        indicator to search for")
    parser.add_argument("-T", "--type", help="The type of indicator for \
        which to search")
    parser.add_argument("-e", "--end_date", help="Search for indicators \
        created up until a date (inclusive). The default is today's date.\
        Note that this date is converted to UTC time, so for example entering \
        1-27-16 would search until 1-27-16 00:00:00 UTC.",
        type=str, default=str(datetime.utcnow()))
    parser.add_argument("-d", "--days_back", help="Number of days prior to \
        the end_date from which results will be pulled.", type=int, default=1)
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

        output_file = 'threat_indicators_' + since_param_string + '_to_' + \
            until_param_string + '.csv'

        with open(output_file,'wb') as fout:
            writer = csv.writer(fout)
            results = ThreatIndicator.objects(
                fields=ThreatIndicator._fields,
                limit=1000,
                text=s.text,
                strict_text=s.strict_text,
                threat_type=s.threat_type,
                type_=s.type,
                since=since_param_string,
                until=until_param_string,
            )

            writer.writerow([
                "_ID", # Need leading underscore so we don't confuse Excel
                "INDICATOR",
                "TYPE",
            ])
            for r in results:
                writer.writerow(
                    map(
                        lambda x: x if type(x) == int else
                            (x.encode('utf-8') if x else ""),
                        [
                            r.get(TI.ID),
                            r.get(TI.INDICATOR),
                            r.get(TI.TYPE),
                        ]
                    )
                )

if __name__ == "__main__":
    main()
