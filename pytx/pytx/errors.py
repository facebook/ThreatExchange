class pytxInitError(Exception):
    """
    Exception for when we the developer doesn't init before instantiating an
    object.
    """

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class pytxValueError(Exception):
    """
    Exception for when we are given a value we are not expecting or is invalid.
    """

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class pytxFetchError(Exception):
    """
    Exception for when a GET or POST attempt fails.
    """

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message
