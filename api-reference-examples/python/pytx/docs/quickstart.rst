.. _quickstart:

Quickstart
==========

ThreatExchange requires an access token in each request. An access token is in
the form of:

   <app-id>|<app-secret>

The app-id is public knowledge but your app-secret is sensitive. These values
are provided to you once you've obtained access to ThreatExchange.

pytx will try to find an access token to use or an access token can be passed to
pytx.access_token.access_token(). pytx needs an access token before it will
function and can properly make requests properly. Here are some examples of
how to provide your access token:

.. code-block :: python

  from pytx.access_token import access_token

  # Use environment variables to build the access token.
  # 1. Use the value of the 'TX_ACCESS_TOKEN' environment variable.
  # 2. Use the concatenation of the 'TX_APP_ID' and 'TX_APP_SECRET' environment variables.
  # There is no need to call access_token() if the environment variables are set.

  # 3. Use a .pytx file which contains your app-id and app-secret.
  # File should be: 'app-id|app-secret' on one line
  # pytx will use either '$PWD/.pytx' or ~/.pytx' if they are found.
  # There is no need to call access_token() if the environment variables are set.

  # 4. Use the concatenation of the app_id and app_secret parameters
  access_token(app_id='<app-id>', app_secret='<app-secret>')

  # 5. Use the first line of the file 'token_file'
  access_token(token_file='/path/to/token/file')


If you need to get the value of the access token pytx is using programmatically,
you can do something like the following:

.. code-block :: python

   from pytx.access_token import get_access_token
   print get_access_token()


If you would like to log debug information as pytx runs, you can setup the
logger by doing the following:

.. code-block :: python

   from pytx import setup_logger
   setup_logger('/path/to/my/log/file.log')


Once this is done there is nothing else to do. pytx will automatically log
information to that file. If the file cannot be written to expect some issues.
If you do not provide an argument to setup_logger, no logging will occur.


If you need to setup a proxy, custom headers, or adjust the verify argument for requests, you can use the connection() function to change them. More info can be found here:
http://docs.python-requests.org/en/latest/api/#requests.request

.. code-block :: python

   from pytx import connection()
   connection(headers=<your stuff here>,
              proxies=<your stuff here>,
              verify=<your stuff here>)


pytx uses classes as the primary method for developer interaction with the
ThreatExchange API. There are several main classes:

   - Malware
   - MalwareFamily
   - ThreatDescriptor
   - ThreatExchangeMember
   - ThreatIndicator
   - ThreatPrivacyGroup
   - ThreatTag

ThreatExchange allows you to upload new ThreatDescriptors. There are several
ways to do so:

.. code-block :: python

   from pytx import ThreatDescriptor
   from pytx.vocabulary import PrivacyType as pt

   td = ThreatDescriptor()
   td.indicator = "foo"
   td.privacy_type = pt.VISIBLE
   td.save()

.. code-block :: python

   from pytx import ThreatDescriptor
   from pytx.vocabulary import PrivacyType as pt
   from pytx.vocabulary import ThreatDescriptor as td

   result = ThreatDescriptor.new(params={td.INDICATOR: 'foo',
                                         td.PRIVACY_TYPE: pt.VISIBLE
                                        })

.. code-block :: python

   from pytx import ThreatDescriptor
   from pytx.vocabulary import PrivacyType as pt
   from pytx.vocabulary import ThreatDescriptor as td

   result = ThreatDescriptor.send(params={td.INDICATOR: 'foo',
                                          td.PRIVACY_TYPE: pt.VISIBLE
                                         },
                                  type_='POST'
                                 )

To query for objects in ThreatExchange, you can leverage any of the
classes like so:

.. code-block :: python

   from pytx import ThreatDescriptor
   from pytx.vocabulary import ThreatDescriptor as td
   from pytx.vocabulary import Types as t

   results = ThreatDescriptor.objects(text='www.facebook.com')
   for result in results:
       print result.get(td.CONFIDENCE)

   # type is type_ because type is a reserved word.
   results = ThreatDescriptor.objects(type_=t.IP_ADDRESS,
                                      text='127.0.0.1')
   for result in results:
       print result.get(td.INDICATOR)

When you query for objects you get a small summary which does not contain all of
the available fields. If you want to get all of the data about a specific
object, you can request it in one of two ways:

.. code-block :: python

   from pytx import ThreatDescriptor

   results = ThreatDescriptor.objects(text='www.facebook.com')
   for result in results:
       # Make another API call to get all of the fields
       result.details()
       print result.to_dict()

.. code-block :: python

   from pytx import ThreatDescriptor

   # Provide the list of fields in the .objects() call to save API calls.
   results = ThreatDescriptor.objects(text='www.facebook.com',
                                      fields=ThreatDescriptor._fields
                                     )
   for result in results:
       print result.to_dict()


When you query for objects, pytx will be default provide you with a generator
which returns instantiated objects to you. You can change the behavior in a few
ways:

.. code-block :: python

   from pytx import ThreatDescriptor
   from pytx.vocabulary import ThreatDescriptor as ti

   # Return the full response instead of a generator.
   # Takes precedence over dict_generator.
   results = ThreatDescriptor.objects(text='www.facebook.com',
                                      full_response=True)

   # Return a dictionary instead of an instantiated object.
   results = ThreatDescriptor.objects(text='www.facebook.com',
                                      dict_generator=True)

This gives some flexibility to developers as to how they interact with the
response.

All of the above class methods come with a 'retries' argument which takes an
integer. This tells pytx that if you receive a 500 or a 503 from ThreatExchange,
try again up until the number of retries has been reached or until you get a
200 (whichever comes first)..

Behind-the-scenes all of the above examples use the pytx Broker to actually make
the requests. If you would prefer to use the Broker directly instead of
leveraging the classes you can do so:

.. code-block :: python

   from pytx.request import Broker
   from pytx.vocabulary import ThreatExchange as te

   b = Broker()
   url = te.URL + te.THREAT_DESCRIPTORS
   params = {te.TEXT: "www.facebook.com"}
   response = b.get(url, params)

The Broker will also allow you to POST and DELETE if you need to.

You can also make Batch requests to the graph via pytx. Batch requests allow you
to submit multiple Graph requests in a single POST request. Here's an example:

.. code-block :: python

   import json
   from pytx import ThreatDescriptor, Batch
   from pytx.errors import pytxFetchError

   a = ThreatDescriptor.objects(text='foo',
                                request_dict=True)
   b = {'type': 'GET',
        'url': '{result=foo:$.data.0.id}'}
   try:
       result = Batch.submit(foo=a,
                             bar=b)
       print json.dumps(result, indent=4, sort_keys=True)
   except pytxFetchError, e:
       print e.message

There are several things to notice in this example. First, the call to find all
ThreatDescriptor objects with a text of "foo" has an argument of
"request_dict=True". By setting that to True, you are telling the objects call
that you'd like the dictionary generated instead of it actually submitting the
request to the Graph.

The second thing to notice is that the second request (b) is a manually crafted
dictionary. The URL is very cryptic (you can look this up in the Facebook Graph
API documentation_) but it is saying that for a URL you want the results from the
"foo" request and you want the first element's id from the data list.

.. _documentation: https://developers.facebook.com/docs/graph-api/making-multiple-requests#operations

The submit call for Batch is giving the name "foo" to request "a", and the name
"bar" to request "b". The submit call will accept N-number of unnamed arguments
and N-number of named arguments. Each one will be considered its own unique
request you want to include in the Batch. The only difference between the two is
that a named argument will be given a name in the request which can then be used
as a reference in other requests in the Batch like the example above.

One thing you might notice is the constant use of vocabulary. pytx comes with a
vocabulary which will allow you to write your code using class attributes so if
ThreatExchange ever changes a string your code will still function properly.

Error responses can be acquired and leveraged as a dictionary. Here is an
example:

.. code-block :: python

   from pytx import Malware
   from pytx.errors import pytxFetchError

   m = Malware()
   m.id = "19374-19841-4813-408"
   response = None
   try:
      m.details()
   except pytxFetchError, e:
      response = e.message

The response variable above will be a dictionary with the following keys:

    - code: the TX response code
    - fbtrace_id: the TX trace id for the request
    - message: the TX server message (what went wrong)
    - status_code: the server response status code
    - type: the TX error type
    - url: the request URL that generated the error

ThreatExchange also allows you to setup Webhooks to get Real-Time Updates on new
content added to ThreatExchange. pytx supports this through the RTUListener
class. This will allow you to quickly spin up a listener that you can point a
Webhook at. Here's a very basic example of how this works:

.. code-block :: python

   from pytx import RTUListener

   def my_callback(request):
       print "POST Data: {}".format(request)
       return "200 OK"

   my_listener = RTUListener(host='0.0.0.0',
                             port=1337,
                             listener_url='/threatexchange/',
                             get_response="hello",
                             callback=my_callback)
   my_listener.listen()

Here we've built our own custom callback function which will allow us to handle
each POST request notifying us of new data that was added to ThreatExchange. We
build up the listener, specifying the host, port, URL suffix we plan on using,
the custom GET response we configured for our Webhook, and the callback
function. The custom GET response is necessary so ThreatExchange can validate
the Webhook with your server. After that we start the listener. That's it!

You can also create your own SSLContext to pass into the RTUListener's
ssl_context attribute to ensure everything is over HTTPS:

.. code-block :: python

   import ssl

   ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
   ssl_context.load_cert_chain(certfile='<your_cert_file.pem',
                               keyfile='<your_key_file.key')

You should read the documentation on Webhooks to ensure you are whitelisting the
IPs associated with Facebook to prevent malicious attacks against your RTU
Listener:

https://developers.facebook.com/docs/graph-api/webhooks?hc_location=ufi#access
