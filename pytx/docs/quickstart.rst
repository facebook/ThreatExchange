.. _quickstart:

Quickstart
==========

ThreatExchange requires an access token in each request. An access token is in
the form of:

   <app-id>|<app-secret>

The app-id is public knowledge but your app-secret is sensitive. These values
are provided to you once you've obtained access to ThreatExchange.

pytx will try to find an access token to use or an access token can be passed to
pytx.access_token.init(). pytx needs an access token before it will function and
can properly make requests properly. Here are some examples of how to provide
your access token:

.. code-block :: python

  from pytx import init

  # Use environment variables to build the access token.
  # 1. Use the value of the 'TX_ACCESS_TOKEN' environment variable.
  # 2. Use the concatenation of the 'TX_APP_ID' and 'TX_APP_SECRET' environment variables.
  # There is no need to call init() if the environment variables are set.

  # Use a .pytx file which contains your app-id and app-secret.
  # File should be: 'app-id|app-secret' on one line
  # pytx will use either '$PWD/.pytx' or ~/.pytx' if they are found.
  # There is no need to call init() if the environment variables are set.

  # 4. Use the concatenation of the app_id and app_secret parameters
  init(app_id='<app-id>', app_secret='<app-secret>')

  # 5. Use the first line of the file 'token_file'
  init(token_file='/path/to/token/file')


If you need to get the value of the access token pytx is using programmatically,
you can do something like the following:

.. code-block :: python

   from pytx.access_token import get_access_token
   print get_access_token()

pytx uses classes as the primary method for developer interaction with the
ThreatExchange API. There are three main classes:

   - ThreatIndicator
   - Malware
   - ThreatExchangeMember

ThreatExchange allows you to upload new ThreatIndicators. To do so, instantiate
a new ThreatIndicator object, provide the required attributes according to the
ThreatExchange documentation, and then save it like so:

.. code-block :: python

   from pytx import ThreatIndicator

   ti = ThreatIndicator()
   ti.indicator = "foo"
   ti.save()

To query for objects in ThreatExchange, you can leverage any of the three
classes like so:

.. code-block :: python

   from pytx import ThreatIndicator
   from pytx.vocabulary import ThreatIndicator as ti
   from pytx.vocabulary import Types as t

   results = ThreatIndicator.objects(text='www.facebook.com')
   for result in results:
       print result.get(ti.THREAT_TYPES)

   # type is type_ because type is a reserved word.
   results = ThreatIndicator.objects(type_=t.IP_ADDRESS,
                                     text='127.0.0.1')
   for result in results:
       print result.get(ti.INDICATOR)

When you query for objects you get a small summary which does not contain all of
the available fields. If you want to get all of the data about a specific
object, you can request it like so:

.. code-block :: python

   from pytx import ThreatIndicator
   from pytx.vocabulary import ThreatIndicator as ti

   results = ThreatIndicator.objects(text='www.facebook.com')
   for result in results:
       result.details()
       print result.to_dict()

Another way to achieve this without another API request is to use the 'fields'
argument to .objects() and specify all of the fields you wish to be included in
the results.

When you query for objects, pytx will be default provide you with a generator
which returns instantiated objects to you. You can change the behavior in a few
ways:

.. code-block :: python

   from pytx import ThreatIndicator
   from pytx.vocabulary import ThreatIndicator as ti

   # Return the full response instead of a generator.
   # Takes precedence over dict_generator.
   results = ThreatIndicator.objects(text='www.facebook.com',
                                     full_response=True)

   # Return a dictionary instead of an instantiated object.
   results = ThreatIndicator.objects(text='www.facebook.com',
                                     dict_generator=True)

This gives some flexibility to developers as to how they interact with the
response.

Behind-the-scenes all of the above examples use the pytx Broker to actually make
the requests. If you would prefer to use the Broker directly instead of
leveraging the classes you can do so:

.. code-block :: python

   from pytx.request import Broker
   from pytx.vocabulary import ThreatExchange as te

   b = Broker()
   url = te.URL + te.THREAT_INDICATORS
   params = {te.TEXT: "www.facebook.com"}
   response = b.get(url, params)

The Broker will also allow you to POST and DELETE if you need to.

One thing you might notice is the constant use of vocabulary. pytx comes with a
vocabulary which will allow you to write your code using class attributes so if
ThreatExchange ever changes a string your code will still function properly.
