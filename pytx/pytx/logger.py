import logging

__LOG = None


def do_log():
    """
    Should we log?
    """
    global __LOG
    if __LOG is None:
        return False
    else:
        return True


def log_message(message):
    """
    Logs a message to the logger.
    """

    if do_log():
        __LOG.debug(message)
    return


def setup_logger(log_file=None):
    """
    Set a log file to log messages to. Useful for debugging.

    :param log_file: A file to log to.
    :type log_file: str
    """
    global __LOG

    if log_file is not None:
        __LOG = logging.getLogger('pytx')
        __LOG.setLevel(logging.DEBUG)
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '%(asctime)s : %(name)s : %(levelname)s : %(message)s'
        )
        fh.setFormatter(formatter)
        __LOG.addHandler(fh)
