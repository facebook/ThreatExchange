from flask.views import View
from flask import Flask, request


class RTUListener(object):

    """
    This class will allow you to quickly instantiate a listener for Real-Time
    Updates from ThreatExchange. ThreatExchange will send a GET request to
    confirm connectivity and will expect a string in the response which is
    similar to the one you configure in your Webhook. This class also allows you
    to specify a callback function. This function will receive the POST request
    (push notification) from ThreatExchange allowing you to handle incoming data
    as you see fit.

    :param get_response: What to respond with when a GET request is made.
    :type get_response: str
    :param host: The IP to bind the listener to.
    :type host: str
    :param port: The port to bind the listener to.
    :type port: int
    :param listener_url: URL suffix to listen on (ex: /foo/)
    :type listener_url: str
    :param callback: Custom function you wish to use for POST requests.
    :type callback: class
    :param ssl_context: Custom ssl.SSLContext for using Flask over TLS.
    :type ssl_context: :class: `ssl.SSLContext`
    :param debug: Enable Flask debug mode (False by default)
    :type debug: bool
    """

    def __init__(self,
                 get_response=None,
                 host=None,
                 port=None,
                 listener_url=None,
                 callback=None,
                 ssl_context=None,
                 debug=False):

        self.get_response = get_response
        self.host = host
        self.port = port
        self.debug = debug
        self.listener_url = listener_url
        self.callback = callback
        self.ssl_context = ssl_context

    def listen(self, host=None, port=None, debug=None):
        """
        Begin listening for incoming requests. Allows you to set a custom host,
        port, and enable debug mode if you didn't already specify those when
        instantiating the RTUListener object.

        :param host: The IP to bind the listener to.
        :type host: str
        :param port: The port to bind the listener to.
        :type port: int
        :param debug: Enable Flask debug mode (False by default)
        :type debug: bool
        """

        host = host or self.host
        port = port or self.port
        debug = debug if debug is not None else self.debug

        # Setup the app and add the custom URL rule for the listener.
        self.app = Flask(__name__)
        self.app.add_url_rule(self.listener_url,
                              view_func=ListenerView.as_view(
                                  self.listener_url.replace('/', ''),
                                  callback=self.callback,
                                  get_response=self.get_response
                              )
                              )
        self.app.run(
            debug=debug,
            host=host,
            port=port,
            ssl_context=self.ssl_context,
        )


class ListenerView(View):
    """
    Main class for handling listening and responding. The default GET response
    is 'hello'.
    """

    methods = ['GET', 'POST']
    get_response = 'hello'

    def __init__(self, callback=None, get_response=None):
        self.callback = callback or self.default_callback
        self.get_response = get_response or self.get_response

    def dispatch_request(self):
        """
        This must be here for the Flask View to work. We verify that we got POST
        data and send it to the callback function, otherwise we assume it was a
        GET and respond with the configured GET response.
        """

        if request.method == 'POST':
            return self.callback(request=request.get_json(force=True))
        return self.get_response

    def default_callback(self, request):
        """
        Basic default callback if no other callback is defined. We consume the
        request and print it for viewing. We have to return something here for
        the Flask listener to work and respond to the client request. If an
        issue occurs prior to the '200 OK' response, Flask handles it.

        :param request: The request data.
        :type request: dict
        """

        print('POST Data: {0}'.format(request))
        return '200 OK'
