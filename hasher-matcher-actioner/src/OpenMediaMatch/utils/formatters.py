from pythonjsonlogger import jsonlogger

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Outputs logs in a JSON format.
    """

    def add_fields(self, log_record, record, message_dict):
        log_record["level"] = record.__dict__.get("levelname")
        log_record["timestamp"] = self.formatTime(record)
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
