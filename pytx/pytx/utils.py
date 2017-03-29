from sys import version_info
import dateutil.parser
import datetime

#  Python 3 comparability hack
if version_info[0] >= 3:
    basestring = str


def convert_to_header(field):
    """
    Converts a ThreatExchange field name to a CSV-writeable string. Also handles
    nested fields. For example, [TD.OWNER, TE.NAME] becomes "owner_email".
    :param field: name of ThreatExchange field
    :type field: list, str
    :returns: str
    """
    if (isinstance(field, basestring)):
        if field == 'ID':
            return '_ID'  # Trailing _ so as not to confuse Excel
        else:
            return field
    elif (isinstance(field, list)):
        return '_'.join(field)


def get_data_field(field, result):
    """
    Given a field name in ThreatExchange, grabs the resulting field value
    from the ThreatExchange object.
    :param field: name of ThreatExchange field
    :type field: list, str
    :param result: The resulting object received from ThreatExchange
    :type result: ThreatExchange object
    :returns: str, int
    """
    try:
        if (isinstance(field, basestring)):
            field_value = result.get(field)
        elif (isinstance(field, list)):
            field_value = result.get(field[0])
            for i in range(1, len(field)):
                field_value = (field_value.get(field[i])
                               if field[i] in field_value.keys() else '')

        field_value = (field_value if type(field_value) == int
                       else (field_value.encode('utf-8') if field_value else ''))
        return field_value
    except:
        raise


def get_time_params(end_date, day_counter, format_):
    """
    Generates both unix and format_ specified timestamps for a given
    24 hour window ending at day_counter days back from end_date
    :param end_date: User-specified end_date of data to be gathered
    :type end_date: str
    :param day_counter: number of days back to slide the time window
    :type day_counter: int
    :param format_: The specified datetime format
    :type format_: str
    :returns: list
    """
    # We use dateutil.parser.parse for its robustness in accepting different
    # datetime formats
    until_param = dateutil.parser.parse(end_date) - \
        datetime.timedelta(days=day_counter)
    until_param_string = until_param.strftime(format_)

    since_param = until_param - datetime.timedelta(days=1)
    since_param_string = since_param.strftime(format_)

    return until_param, until_param_string, since_param, since_param_string
