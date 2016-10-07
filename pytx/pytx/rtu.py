from flask.views import View
from flask import Flask, request


class RTUListener(object):

    """
    This class will allow you to quickly instantiate a listener for Real-Time
    Updates from ThreatExchange.
    """

    def __init__(self,
                 get_response=None,
                 host=None,
                 port=None,
                 listener_url=None,
                 callback=None,
                 debug=False):

        self.get_response = get_response
        self.host = host
        self.port = port
        self.debug = debug
        self.listener_url = listener_url
        self.callback = callback

    def listen(self, host=None, port=None, debug=None):
        host = host or self.host
        port = port or self.port
        debug = debug if debug is not None else self.debug
        lv = ListenerView(callback=self.callback,
                          get_response=self.get_response)
        self.app = Flask(__name__)
        self.app.add_url_rule(self.listener_url,
                              view_func=lv.as_view(
                                  self.listener_url.replace('/', '')
                              )
                              )
        self.app.run(
            debug=debug,
            host=host,
            port=port,
        )


class ListenerView(View):
    """
    Main class for handling listening and responding.
    """

    methods = ['GET', 'POST']
    get_response = 'hello'

    def __init__(self, callback=None, get_response=None):
        # TODO: These are not sticking
        self.callback = callback or self.default_callback
        self.get_response = get_response or self.get_response

    def dispatch_request(self):
        if request.method == 'POST':
            return self.callback(response='foo')
        return self.get_response

    def default_callback(self, response):
        print 'Response: %s' % response
        return '200 OK'
