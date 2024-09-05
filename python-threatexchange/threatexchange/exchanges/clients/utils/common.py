from requests.adapters import HTTPAdapter


class TimeoutHTTPAdapter(HTTPAdapter):
    """
    Plug into requests to get a well-behaved session that does not wait for eternity.
    H/T: https://findwork.dev/blog/advanced-usage-python-requests-timeouts-retries-hooks/#setting-default-timeouts
    """

    def __init__(self, *args, timeout=5, **kwargs):
        self.timeout = timeout
        super().__init__(*args, **kwargs)

    def send(self, request, *, timeout=None, **kwargs):
        if timeout is None:
            timeout = self.timeout
        return super().send(request, timeout=timeout, **kwargs)