import dateutil.parser
import datetime

def convert_to_header(field):
    if (isinstance(field, basestring)):
        if field == "ID": return "_ID" # Trailing _ so as not to confuse Excel
        else: return field
    elif (isinstance(field, list)):
        return "_".join(field)

def get_data_field(field, result):
    try:
        if (isinstance(field, basestring)):
            field_value = result.get(field)
        elif (isinstance(field, list)):
            field_value = result.get(field[0])
            for i in range(1, len(field)):
                field_value = (field_value.get(field[i])
                    if field[i] in field_value.keys() else "")
        field_value = (field_value if type(field_value) == int
            else (field_value.encode('utf-8') if field_value else ""))
        return field_value
    except:
        e = sys.exc_info()[0]
        print e
        print field
        print field_value
        print result

def get_time_params(end_date, day_counter, format_):
    # We use dateutil.parser.parse for its robustness in accepting different
    # datetime formats
    until_param = dateutil.parser.parse(end_date) - \
        datetime.timedelta(days=day_counter)
    until_param_string = until_param.strftime(format_)

    since_param = until_param - datetime.timedelta(days=1)
    since_param_string = since_param.strftime(format_)

    return until_param, until_param_string, since_param, since_param_string
