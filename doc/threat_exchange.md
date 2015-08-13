# Facebook ThreatExchange API Documentation

<!---

WARNING! DO NOT REMOVE THE TRAILING SPACES AFTER THE HEADINGS IN THIS FILE
For example:

**Value:**  

These trailing spaces are used in Markdown to denote a line-break. They are
necessary to make the formatting look correct. Most editors will remove these
spaces by default.

-->

Threat intelligence comes to us in numerous types: a domain name used by a
botnet, a URL delivering malware, a file name written to disk by some malware.
These are disparate data and need different kinds of metadata to make them
useful to others.

To ensure consistency, the ThreatExchange APIs and its consumers use JSON
objects as their default currency. Using these APIs gives you a lot of things
for free:

* Field validation
* Type checking
* Persistence to Facebook's Open Graph
* Everyone else can use what you share and be better protected!

All objects are formatted maps using a predefined set of field names, with
expected value types.  They can be of arbitrary size and field order in the
map is, generally, not important. 

ThreatExchange is a subset of API endpoints within the larger ecosystem of
Facebook Graph APIs. Essential documentation for interacting with Facebook
platform Graph APIs are available at
https://developers.facebook.com/docs/graph-api.
This documentation covers key concepts: usage of access tokens for
authentication,
result pagination, and batching.  It is recommended to be familiar with the
basics of interacting with Facebook Graph APIs prior to trying out
ThreatExchange. 

### Changes in Platform version 2.4

There were a large number of changes made in Platform version 2.4. You may
continue to use Platform version 2.3, without those changes, until 8 Dec 2015.
On that day support for version 2.3 will be disabled.

The most important change in version 2.4 was was the introduction of the 
descriptor model. On version 2.3 and below, all data was stored on the 
indicator. Beginning with version 2.4, we split information into
objective and subjective categories. Objective information is data which 
everybody can see and agree upon. It may change over time, but everybody sees 
the same data. For example, the WHOIS registration for a domain name is
objective. Subjective information represents somebody's opinion on the data. 
Different people may have different opinions. For example, the status of a 
domain as being MALICIOUS or NON_MALICIOUS.

Objective information will remain stored on indicators. For the most part,
Facebook will be the only party updating objective information. Subjective 
information is now stored on a new structure called a descriptor. We have added
API calls to create, edit, and search for descriptors. Each AppID may have
one descriptor per indicator. Each descriptor has an edge connecting it
to a threat indicator. Each indicator has edges to one or more descriptors.

We currently do not support connections between descriptors. Connections
between indicators will remain the only way to associate threat information
for the time being. 


## Getting Access

If you haven't already, begin by requesting access to ThreatExchange at
[https://threatexchange.fb.com](https://threatexchange.fb.com).



## Querying For Data

Queries into ThreatExchange are HTTP GET requests to one of the following URLs

    https://graph.facebook.com/malware_analyses
    https://graph.facebook.com/threat_exchange_members
    https://graph.facebook.com/threat_indicators
	  https://graph.facebook.com/threat_descriptors
    https://graph.facebook.com/<object-id>
    https://graph.facebook.com/<object-id>/<connection-type>

### /malware\_analyses

This API call enables searching for malware stored in ThreatExchange.  With this
call you can search for malware by free text (including file hashes) or all
malware uploaded in a specific time window.  Combinations of these query types
are also allowed.

The following query parameters are available (bold params are required):

* **access\_token** - The key for authenticating to the API.  It is a
concatenation of &lt;your-app-id&gt;|&lt;your-app-secret&gt;.  For example,
if our app ID was 555 and our app secret aSdF123GhK, our access\_token would
be "555|aSdF123GhK".
* limit - Defines the maximum size of a page of results. The maximum is 1,000.
* text - Freeform text field with a value to search for.  This can be a file
hash or a string found in other fields of the objects.
* strict\_text - When set to 'true', the API will not do approximate matching
on the value in text
* since - Returns malware collected after a timestamp
* until - Returns malware collected before a timestamp

Example query for all malware in a 12 hour window:

    https://graph.facebook.com/malware_analyses?access_token=555|aSdF123GhK&since=1391813489&until=1391856689

Data returned:

    {
      "data": [
        {
          "added_on": "2014-02-08T03:36:43+0000",
          "status": "UNKNOWN",
          "md5": "96511dae4736339de9c0f2ccdf5cce0e",
          "sha1": "2d02c39d9114e13e1381eb3a4254a40817eae9e9",
          "sha256": "6d1499148b8bc19aa3a5c29528c44705f8e6fb9954ce5dd0d908198778db6e34",
          "victim_count": 5,
          "id": "552682878160840"
        },
        ...
      ]
      "paging": {
        "cursors": {
          "before": "MA==",
          "after": "OTk5"
        },
        "next": "https://graph.facebook.com/malware_analyses?pretty=0&since=1391813489&until=1391856689&limit=1000&after=OTk5"
      }
    }

### /threat\_exchange\_members

Returns a list of current members of the ThreatExchange, alphabetized by
application name. Each application may also include an optional contact
email address. You can set this address, if desired, under the settings
panel for your application. See https://developers.facebook.com/apps/.

The following query parameter is required:

* **access\_token** - The key for authenticating to the API. It is a
concatenation of &lt;your-app-id&gt;|&lt;your-app-secret&gt;. For example,
if our app ID was 555 and our app secret aSdF123GhK, our access\_token would
be "555|aSdF123GhK".

Example query:

    https://graph.facebook.com/threat_exchange_members?access_token=555|aSdF123GhK

Data returned:

    {
      "data": [
        {
          "id": "820763734618599",
          "email": "threatexchange@support.facebook.com",
          "name": "Facebook ThreatExchange"
        },
        ...
      ]
    }


### /threat\_indicators

This API call enables searching for indicators of compromise stored in
ThreatExchange.  With this call you can search for indicators by free text,
type, or all in a specific time window.  Combinations of these query types
are also allowed.

The following query parameters are available (bold parameters are required):

* **access\_token** - The key for authenticating to the API.  It is a
concatenation of &lt;your-app-id&gt;|&lt;your-app-secret&gt;. For example,
if our app ID was 555 and our app secret aSdF123GhK, our access\_token would
be "555|aSdF123GhK".
* limit - Defines the maximum size of a page of results. The maximum is 1,000.
* text - Freeform text field with a value to search for.  This can be a file
hash or a string found in other fields of the objects.
* strict\_text - When set to 'true', the API will not do approximate matching
on the value in text
* threat\_type - The broad threat type the indicator is associated
with (see the full list of values below)
* type - The type of indicators to search for (see the full list of types below)
* since - Returns malware collected after a timestamp
* until - Returns malware collected before a timestamp

Example query for all malicious IP addresses that are proxies:

    https://graph.facebook.com/threat_indicators?access_token=555|aSdF123GhK&type=IP_ADDRESS&text=proxy

The data returned by this API call changed in Platform version 2.4.
Data returned in Platform v2.3:

    {
      "data": [
        {
          "added_on": "2015-02-25T14:46:37+0000", 
          "confidence": 50, 
          "description": "Localhost IP", 
          "indicator": "127.0.0.1", 
          "severity": "INFO", 
          "share_level": "GREEN", 
          "status": "NON_MALICIOUS", 
          "type": "IP_ADDRESS", 
          "threat_types": [
            "MALICIOUS_IP"
          ], 
          "id": "804745332940593"
        }
      ], 
      "paging": {
        "cursors": {
          "before": "MA==", 
          "after": "MA=="
        }
      }
    }

Data returned in Platform v2.4:

    {
      "data": [
        {
          "indicator": "127.0.0.1",
          "type": "IP_ADDRESS",
          "id": "804745332940593"
        }
	  ],
      "paging": {
        "cursors": {
          "before": "MA==", 
          "after": "MA=="
        }
      }
    }


### /threat\_descriptors

The API call enables searching for subjective opinions on indicators
of compromise stored in ThreatExchange. With this call you can search
by free text, type, submitter, or all in a specific time window. Combinations
of these query types are also allowed. This call is only permitted on 
Platform version 2.4.

* **access\_token** - The key for authenticating to the API.  It is a
concatenation of &lt;your-app-id&gt;|&lt;your-app-secret&gt;. For example,
if our app ID was 555 and our app secret aSdF123GhK, our access\_token would
be "555|aSdF123GhK".
* limit - Defines the maximum size of a page of results. The maximum is 1,000.
* owner - The AppID of the person who submitted the data.
* text - Freeform text field with a value to search for.  This can be a file
hash or a string found in other fields of the objects.
* strict\_text - When set to 'true', the API will not do approximate matching
on the value in text
* threat\_type - The broad threat type the indicator is associated
with (see the full list of values below)
* type - The type of indicators to search for (see the full list of types below)
* since - Returns malware collected after a timestamp
* until - Returns malware collected before a timestamp

Example query for all IP addresses submitted by Facebook Administrator 
which contain the word "proxy":

  https://graph.facebook.com/threat_descriptors?access_token=555|asDF&type=IP_ADDRESS&owner=820763734618599&text=proxy

Data returned:

	{
	  "data": [
	    {
	      "id": "864036000343976",
	      "indicator": {
	        "indicator": "127.0.0.1",
	        "type": "IP_ADDRESS",
	        "id": "961490387234997"
	      },
	      "owner": {
	        "id": "820763734618599",
	        "email": "threatexchange@support.facebook.com",
	        "name": "Facebook Administrator"
	      },
	      "type": "IP_ADDRESS",
	      "raw_indicator": "127.0.0.1",
	      "description": "TOR Proxy IP Address",
	      "status": "UNKNOWN"
	    },


### /&lt;object\_id&gt; - Malware Objects

This API call is for directly accessing a specific Open Graph malware object.
It gives you the ability to see additional data, including the file itself.

The following query parameters are available (bold parameters are required):

* **access\_token** - The key for authenticating to the API.  It is a
concatenation of &lt;your-app-id&gt;|&lt;your-app-secret&gt;.  For example,
if our app ID was 555 and our app secret aSdF123GhK, our access\_token would
be "555|aSdF123GhK".
* fields - A comma-delimited string of any combination of the following:
	* added\_on - When the malware was added to the graph, in ISO 8601 date format;
	* crx - The Google Chrome Extension ID (if applicable);
	* id - The malware's unique ThreatExchange ID;
	* imphash - The ImportHash for the sample;
	* md5 - The MD5 hash for the sample;
	* password - The password used to decompress the sample file;
	* pe\_rich\_header - The PE Rich Header hash for the sample (VC++ compiled
 portable executables only)
	* sample - A base64 encoded zip compressed blob of the sample file (requires
 the value in the password field to decompress);
	* sha1 - The SHA1 hash for the sample;
	* sha256 - The SHA256 hash for the sample;
  * share\_level - A designation of how the indicator may be shared based on
  the US-CERT\'s Traffic Light Protocol, https://www.us-cert.gov/tlp/
	* ssdeep - The SSDeep hash for the sample;
  * status - Indicates if the sample is labeled as malicious;
  * submitter\_count - The number of members that have submitted the indicator;
	* victim\_count - The number of known victims infected with the sample; and
	* xpi - The Mozilla Firefox Extension ID (if applicable).

Example query for a specific malware sample: 518964484802467

    https://graph.facebook.com/518964484802467/?access_token=555|aSdF123GhK&fields=added_on,id,status,md5,sha1,sha256

Data returned:

    {
      "added_on": "2014-02-10T08:15:08+0000",
      "id": "518964484802467",
      "md5": "31a345a897ef34cf2a5ce707d217ac6b",
      "sha1": "bc45693e681244bef57bc2e20bff0ff9e32e2105",
      "sha256": "2b7f45684ed8a86f446a0a835debaf9b3dda7d38f74d672eb5237ca2001add1e",
      "status": "UNKNOWN"
    }

**Connections**

ThreatExchange APIs support finding objects connected to malware objects.  For malware
we support the following connections:

* dropped - A list of malware objects installed or 'dropped' by this object;
* dropped\_by - A list of the malware objects that installed or 'dropped'
this object;
* families - A list of malware families the malware is associated with; and
* threat\_indicators - A list of threat indicators associated with this object.

Example query for a specific malware sample: 518964484802467

    https://graph.facebook.com/518964484802467/dropped/?access_token=555|aSdF123GhK

Data returned:

    {
      "data": [
        {
          "added_on": "2014-05-17T08:50:23+0000",
          "crx": "imidebfpiccjhkmkliilncodnlcijpnl",
          "status": "MALICIOUS",
          "victim_count": 1,
          "id": "636198259806586"
        },
        ...
      ]
    }

### /&lt;object\_id&gt; - Malware Family Objects

This API call is for directly accessing a specific Open Graph malware family 
object. It gives you the ability to see additional data, including the file
itself.

The following query parameters are available (bold parameters are required):

* **access\_token** - The key for authenticating to the API.  It is a
concatenation of &lt;your-app-id&gt;|&lt;your-app-secret&gt;.  For example,
if our app ID was 555 and our app secret aSdF123GhK, our access\_token would
be "555|aSdF123GhK".
* fields - A comma-delimited string of any combination of the following:
	* added\_on - When the family was added to the graph, in ISO 8601 date format;
	* aliases - A list of additional names for the family;
  * description - A brief explanation of the family;
  * family\_type - The kind of family, see the list of family types defined 
  below;
	* id - The malware's unique ThreatExchange ID;
  * malicious - Indicates if the family is labeled as malicious;
  * name - The name of the family;
	* sample\_count - A count of family members.

Example query for a specific malware sample: 812860802080929

    https://graph.facebook.com/812860802080929/?access_token=555|aSdF123GhK&fields=added_on,id,name,status

Data returned:

    {
      "added_on": "2014-07-03T02:25:18+0000",
      "family_type": "IMP_HASH",
      "description": "md5deep Automatic family based on PE Import Hash",
      "malicious": "NON_MALICIOUS",
      "name": "ImpHash for md5deep v4.4",
      "id": "812860802080929"
    }

**Connections**

ThreatExchange APIs support finding objects connected to malware family 
objects.  For families we support the following connections:

* variants - A list of malware samples belonging to a family.

Example query for a specific malware sample: 518964484802467

    https://graph.facebook.com/518964484802467/dropped/?access_token=555|aSdF123GhK

Data returned:

    {
      "data": [
        {
          "added_on": "2014-05-17T08:50:23+0000",
          "crx": "imidebfpiccjhkmkliilncodnlcijpnl",
          "status": "MALICIOUS",
          "victim_count": 1,
          "id": "636198259806586"
        },
        ...
      ]
    }


### /&lt;object\_id&gt; - Threat Indicator Objects

This API call is for directly accessing a specific threat indicator
object in ThreatExchange.  It gives you the ability to see additional data.

The following query parameters are available under Platform version 2.3
(bold parameters are required):

* **access\_token** - The key for authenticating to the API.  It is a
concatenation of &lt;your-app-id&gt;|&lt;your-app-secret&gt;.  For example,
if our app ID was 555 and our app secret aSdF123GhK, our access\_token would
 be "555|aSdF123GhK".
* fields - A comma-delimited string of any combination of the following:
  * added\_on - Timestamp when the indicator was added, in ISO 8601 date format;
  * confidence - A score for how confident we are that the indicator is bad
 ranges from 0 to 100;
  * description - A human readable description of the indicator;
  * expired\_on - Timestamp when the indicator expired, in ISO 8601 date
  format, can be in the future;
  * id - The indicator's unique Open Graph ID;
  * indicator - The indicator itself;
  * passwords - Any passwords associated with the indicator;
  * report\_urls - Links to reports about the indicator;
  * severity - A rating of how severe the indicator is when found in an
  incident, see values defined below;
  * share\_level - A designation of how the indicator may be shared based
  on the US-CERT\'s Traffic Light Protocol, https://www.us-cert.gov/tlp/
  * status - Indicates if the indicator is labeled as malicious;
  * submitter\_count - The number of members that have submitted the indicator;  
  * threat\_types - A list of broad threat types the indicator is associated
   with, see values defined below;
  * type - The kind of indicator, see values defined below in the "Type Field Values" section.
  
The following query parameters are available under Platform version 2.4
(bold parameters are required):

* **access\_token** - The key for authenticating to the API.  It is a
concatenation of &lt;your-app-id&gt;|&lt;your-app-secret&gt;.  For example,
if our app ID was 555 and our app secret aSdF123GhK, our access\_token would
 be "555|aSdF123GhK".
* fields - A comma-delimited string of any combination of the following:
  * id - The indicator's unique Open Graph ID;
  * indicator - The indicator itself;  
  * type - The kind of indicator, see values defined below in the "Type Field Values" section.

Example query for a specific indicator: 788497497903212:

    https://graph.facebook.com/788497497903212/?access_token=555|aSdF123GhK&fields=type,threat_types,description,indicator,added_on

Data returned under Platform version 2.3:

    {
          "added_on": "2015-02-11T21:10:21+0000", 
          "description": "Facebook", 
          "indicator": "facebook.com",  
          "type": "DOMAIN", 
          "threat_types": [
            "UNKNOWN"
          ], 
          "id": "788497497903212"
        }

Data returned under Platform version 2.4:

	{
	  "indicator": "115.78.122.38",
	  "type": "IP_ADDRESS",
	  "id": "847320048638546"
	}


**Connections**

The API supports finding objects connected to threat indicator objects.
For indicators, the following are supported:

* malware\_analyses - A list of malware objects associated with this object;
* related - A list of other threat indicators related to this object.

Under Platform version 2.4, you can also access the connection:

* descriptors - A list of subjective opinions about this indicator

Example query for malware analyses related to a specific indicator: 
768629009848617

    https://graph.facebook.com/768629009848617/malware_analyses/?access_token=555|aSdF123GhK

Data returned:

    {
      "data": [
        {
          "added_on": "2014-06-05T19:52:11+0000",
          "md5": "7914a485bdc6df7103e7cae379f7a152",
          "sha1": "fd1b83fc4c1f5b5a68ddfdec8ba97d59d78e6065",
          "sha256": "ab402de2c79ad620a84cf651d7cf4f8287acf8564a8c551e5b39bb82813abbc6",
          "status": "MALICIOUS",
          "victim_count": 0,
          "id": "673692009351404"
        },
        ...
      ]
    }
    
Example query for descriptors related to a specific indicator:

     https://graph.facebook.com/852121234856016/descriptors/?access_token=555|aSdF123GhK

Data returned:
     
     {
       "data": [
      {
        "id": "811927545529339",
        "indicator": {
          "indicator": "test1434227164.evilevillabs.com",
          "type": "DOMAIN",
          "id": "852121234856016"
        },
        "owner": {
          "id": "588498724619612",
          "name": "Facebook CERT ThreatExchange"
        },
        "type": "DOMAIN",
        "raw_indicator": "test1434227164.evilevillabs.com",
        "description": "This is our test domain. It's harmless",
        "status": "NON_MALICIOUS"
      },
      {
        "id": "799906626794304",
        "indicator": {
          "indicator": "test1434227164.evilevillabs.com",
          "type": "DOMAIN",
          "id": "852121234856016"
        },
        "owner": {
          "id": "682796275165036",
          "name": "Facebook Site Integrity ThreatExchange"
        },
        "type": "DOMAIN",
        "raw_indicator": "test1434227164.evilevillabs.com",
        "description": "Malware command and control",
        "status": "MALICIOUS"
      }
    ],
    "paging": {
      "cursors": {
        "before": "ODExOTI3NTQ1NTI5MzM5",
        "after": "Nzk5OTA2NjI2Nzk0MzA0"
      }
    }
  }


### /&lt;object\_id&gt; - Threat Descriptor Objects

This API call is for directly accessing a specific threat descriptor
object in ThreatExchange. It is only available under Platform version 2.4.

The following query parameters are available (bold parameters are required):

* **access\_token** - The key for authenticating to the API.  It is a
concatenation of &lt;your-app-id&gt;|&lt;your-app-secret&gt;.  For example,
if our app ID was 555 and our app secret aSdF123GhK, our access\_token would
 be "555|aSdF123GhK".
* fields - A comma-delimited string of available fields. The available fields
changed between Platform v2.3 and v2.4. Fields available under v2.4:
  * confidence - A confidence rating on the status field, ranges from 0 to 100;
  * description - A human readable description of the indicator;
  * expired\_on - Timestamp when the indicator expired, in ISO 8601 date
  format, can be in the future;
  * id - The descriptor's unique ThreatExchange ID;
  * indicator - The indicator object being described, see threat indicator object for details;
  * last\_updated - When the descriptor was last updated, in ISO 8601 date format;
  * owner - The ThreatExchange application that created the descriptor, see owner object for details;
  * precision - The degree of accuracy of the indicator;
  * raw\_indicator - The un-altered indicator, as submitted by the owner, that is the subject of the descriptor;
  * review\_status - Describes how the indicator was vetted;
  * report\_urls - Links to reports about the indicator;
  * severity - A rating of how severe the indicator is when found in an
  incident, see values defined below;
  * share\_level - A designation of how the indicator may be shared based
  on the US-CERT\'s Traffic Light Protocol, https://www.us-cert.gov/tlp/;
  * status - Indicates if the indicator is labeled as malicious;  
  * threat\_type - The broad threat types the indicator is associated
   with, see values defined below;
  * type - The kind of indicator, see values defined below in the "Type Field Values" section.

Example query for a specific descriptor: 777900478994849

  https://graph.facebook.com/777900478994849?access_token=555|asdF123
  
	{
	  "id": "777900478994849",
	  "indicator": {
	    "indicator": "http://test1435342443.evilevillabs.com/test.php",
	    "type": "URI",
	    "id": "841478115929947"
	  },
	  "owner": {
	    "id": "682796275165036",
	    "name": "Facebook Site Integrity ThreatExchange"
	  },
	  "type": "URI",
	  "raw_indicator": "http://test1435342443.evilevillabs.com/test.php",
	  "description": "Test Description",
	  "status": "UNKNOWN"
	}


## Submitting New Data

You may submit data to the graph via an HTTP POST request to either of the 
following URLs:

    https://graph.facebook.com/threat_indicators
	  https://graph.facebook.com/threat_descriptors

Both endpoints are supported in Platform version 2.4, but you should migrate
your code to the second version. Both calls are actually creating threat
descriptor objects. The first call will return the ID of the indicator
associated with your descriptor. The second call will return the ID of the
descriptor. The call to /threat\_indicators will be deprecated in a future 
version of the Platform API.

The following submission parameters are available (bold parameters are required):

* **access\_token** - The key for authenticating to the API.  It is a
concatenation of &lt;your-app-id&gt;|&lt;your-app-secret&gt;.  For example,
if our app ID was 555 and our app secret aSdF123GhK, our access\_token would
be "555|aSdF123GhK";
* confidence - A confidence rating on the status field, from 0 to 100;
* **description** - A short summary of the indicator and threat;
* expired\_on - Time the indicator is no longer considered a threat, in
ISO 8601 date format;
* **indicator** - The indicator data being submitted;
* precision - The degree of accuracy of the indicator, see the Precision enum described below in the "Other Schema Field Enums" section;
* **privacy\_type** - The kind of privacy for the indicator, see values
  defined below;
* privacy\_members - Some types of privacy require you to specify who can
  or cannot see the indicator;
* review\_status - Describes how the indicator was vetted, see the Review Status enum described below in the "Other Schema Field Enums" section; 
* severity - A rating of how severe the indicator is when found in an incident,
see values defined below;
* **share_level** - A designation of how the indicator may be shared based on the
US-CERT\'s Traffic Light Protocol, https://www.us-cert.gov/tlp/;
* **status** - Indicates if the indicator is labeled as malicious;
* threat\_type - The broad threat type the indicator is associated with,
see values defined below;
* **type** - The kind of indicator being described, see values defined below in the "Type Field Values" section.


Example submission of a malicious domain:

    https://graph.facebook.com/threat_indicators?access_token=555|aSdF123GhK

    POST DATA:
      indicator=evil-domain.biz
      &type=DOMAIN
      &threat_type=MALICIOUS_DOMAIN
      &status=MALICIOUS
      &description=This%20domain%20was%20hosting%20malware
      &privacy_type=VISIBLE


Data returned:

    {
      "id": "853037291373757",
      "success": true
    }


## Setting Privacy In ThreatExchange

All submissions to the ThreatExchange API require setting a privacy type.
This choice can limit the visibility of any indicator, if desired.
ThreatExchange supports two levels of visibility:

* allow all members;
* allow specific members;

The desired privacy setting on an indicator is specified by the values in two
fields at the time of a create or edit submission to the API:

**Name: PRIVACY\_TYPE**  
**Type: enumerated string**  
**Value: One of**  

* VISIBLE - All members of ThreatExchange can see the indicator
* HAS\_WHITELIST - Only those AppIDs specified in PRIVACY\_MEMBERS can see the
indicator.

**Name: PRIVACY\_MEMBERS**  
**Type: list of App IDs**  
**Value:**  

* A comma-delimited list of AppIDs allowed to view an
indicator in accordance with the PRIVACY\_TYPE.  NOTE:  When limiting
visibility, it is not necessary to include your own AppID. It will be added
automatically if necessary.


Example submission of a malicious domain with the privacy set to just two members

    https://graph.facebook.com/threat_indicators?access_token=555|aSdF123GhK

    POST DATA:
      indicator=evil-domain.biz
      &type=DOMAIN
      &threat_type=MALICIOUS_DOMAIN
      &status=MALICIOUS
      &description=This%20domain%20was%20hosting%20malware
      &privacy_type=HAS_WHITELIST
      &privacy_members=123456789,9012345678


## Editing Existing Data

Existing data can be edited via an HTTP POST request to the following URL

    https://graph.facebook.com/<object_id>

You can use this format to update an indicator or a descriptor. The code
will automatically update the descriptor for you.  The fields available for editing are identical to the fields listed in the indicator and descriptor submission fields earlier in this documentation.

Example of flagging data as a false positive:

    https://graph.facebook.com/853037291373757?access_token=555|aSdF123GhK

    POST DATA:
      status=NON_MALICIOUS
      &description=Not%20malicious


Data returned:

    {
      "success": true
    }

## Submitting Connections Between Data

We support creating connections (aka edges) between pieces of data to express
relationships.  Examples of when this can be useful are for describing
URL re-direct chains or domain to IP address relationships.  However,
we support connecting any type of data to any other type.  Connections can
be created via an HTTP POST request to the following URL

    https://graph.facebook.com/<object_id>/related

In the example below we will create a connection between between the
facebook.com domain object (788497497903212) and the 173.252.120.6 IP address
object (1061383593887032), which facebook.com can resolve to via DNS.

    https://graph.facebook.com/788497497903212/related

    POST DATA:
      related_id=1061383593887032

Data returned:

    {
      "success": true
    }


NOTE: Currently, this is not supported for malware objects or threat 
descriptors, but will be in the near future.


## Deleting Data

We currently support true deletes via the API
**only for connections between data**.  A connection can be deleted via an
HTTP DELETE request to the following URL

    https://graph.facebook.com/<object_id>/related?related_id=<object_id_2>


For the data itself, we do not support true deletes.  If you wish to indicate
data is no longer valid, set the **expired\_on** field for automatic
soft-deletes and the **status** field to **NON\_MALICIOUS** for handling false
positive cases.


## Schema Core Fields

The following fields are present on all indicators returned by the API.
An indicator will be considered invalid if missing any of these fields, except
for the ID field, which the API will auto-generate for you.

**Name: THREAT\_TYPE**  
**Type: enumerated string list**  
**Description: Describes a high-level type of threat described in the
indicator submission.**  
**Value: One, or more, of**  

* BAD_ACTOR - details on a presumed bad actor (e.g. botherder, spammer)
* COMPROMISED_CREDENTIAL - The credential compromised by an attack (must be already publicly accessible)
* COMMAND_EXEC - an OS command line entry, with parameters
* MALICIOUS_AD - a malicious advertisement
* MALICIOUS_CONTENT - a malicious post, image, or document used in an attack
* MALICIOUS_DOMAIN - a domain that's on someone's blacklist
* MALICIOUS_INJECT - for victim check-ins to a botnet sinkhole
* MALICIOUS_IP - an IP that's on someone's blacklist
* MALICIOUS_URL - a URL that's on someone's blacklist
* MALWARE_ARTIFACTS - describes an taken by malware (e.g. reg key created,
files installed, etc)
* MALWARE_SAMPLE - a specific malware binary
* PROXY_IP - for IPs known to be proxies or VPNs
* SIGNATURE - Represents some kind of signature for detecting a threat
* SMS_SPAM - SMS spam report
* WEB_REQUEST - A full web request with GET query parameters
* WHITELIST_DOMAIN - Domain name on someone's whitelist
* WHITELIST_IP - IP address on someone's whitelist
* WHITELIST_URL - URL on someone's whitelist

**Name: CONFIDENCE**  
**Type: Bounded floating-point number**  
**Description: A confidence score, i.e. how confident you should be that
the indicator is bad**  
**Value: 0 → 100, with the following interpretation**  

* LOW - 0 → 25
* MEDIUM - 26 → 75
* HIGH - 76 → 100

**Name: PRIVACY\_TYPE**
**Type: Enumerated string**
**Description: **
**Value: One of**

* HAS\_WHITELIST - Only the ThreatExchange IDs specified in the PRIVACY\_MEMBERS field will be able to see the data
* VISIBLE - All ThreatExchange members will be able to see the data

**Name: SEVERITY**  
**Type: Enumerated string**  
**Description: How severe the indicator is if it's found on a system or in traffic**  
**Value: One of**  

* INFO
* WARNING
* SUSPICIOUS
* SEVERE
* APOCALYPSE

**Name: SHARE\_LEVEL**  
**Type: Enumerated string**  
**Description: A designation of how the indicator may be shared based on
the US-CERT\'s Traffic Light Protocol, https://www.us-cert.gov/tlp/**  
**Value: One of**  

* WHITE
* GREEN
* AMBER
* RED

**Name: STATUS**  
**Type: enumerated string**  
**Value: One of**  

* MALICIOUS
* NON_MALICIOUS
* SUSPICIOUS
* UNKNOWN

**Name: ID**  
**Type: Integer**  
**Description: The unique ID for the indicator, as designated by Facebook's
Graph API**  
**Value:**  

* An integer, e.g. 510652279005033.

## Type Field Values

The following is the list of different values we support in the 'type'
field for threat indicator submissions.  The limitations or format
expectations described along with each one will be applied to the
'indicator' field on submission to the ThreatExchange API.

**Name: ADJUST_TOKEN**  
**Type: String**  
**Description: A modification to token permissions in the Windows
operating system**.  
**Value:**  

* A string with the token name that was modified. For example, 'Debug' or
'Change Notify'.

**Name: API_KEY**  
**Type: String**  
**Description: An API key being using by a malware actor**  
**Value:**

* A string, e.g. JH52anj9snaQ.

**Name: AS_NUMBER**  
**Type: String**  
**Description: An autonomous system number (ASN)**  
**Value:**  

* A valid ASN. For example, 32934 (FACEBOOK)

**Name: AS_NAME**  
**Type: String**  
**Description: An autonomous system's name**  
**Value:**  

* A valid ASN's name. For example, 'AMAZON-AES', 'FACEBOOK', or 'HETZNER'.

**Name: BANNER**  
**Type: string**  
**Value: A banner reply from a server**  

* A banner reply from a server. For example, 'Apache/2.2.22 (Ubuntu) Server
at localhost Port 80'

**Name: CHECKSUM_CRC16**  
**Type: String**  
**Value:**  

* A CRC16 checksum.

**Name: CMD_LINE**  
**Type: string**  
**Value:**  

* A command line executed in an operating system. For example,
'cmd.exe C:\tmp\malware.exe'

**Name: COOKIE_NAME**  
**Type: string**  
Value:

* The name of an HTML cookie used. For example, 'login_name'.

**Name: COUNTRY**  
**Type: string**  
**Value:**  

* The ISO di-graph alpha code for a country. For example, 'US'
for The United States. Note that there is a separate field for **LOCATION**.

**Name: CRX**  
**Type: string**  
**Value:**  

* A Chrome extension ID, e.g. 'aohghmighlieiainnegkcijnfilokake'.

**Name: DEBUG_STRING**  
**Type: string**  
**Value:**  

* A text string found in a binary file, e.g.
'd:\admin\projects\test\test.pdb'.

**Name: DEST_PORT**  
**Type: integer**  
**Value:**  

* Network port for the destination host, e.g. '443'.

**Name: DEVICE_IO**  
**Type: string**  
**Value:**  

* I/O of a device by a process.

**Name: DIRECTORY_QUERIED**  
**Type: string**  
**Value:**  

* A string of a file path queried by a process, e.g. 'C:\Windows\tmp'.

**Name: DOMAIN**  
**Type: string**  
**Value:**  

*  A valid Internet domain name, e.g. 'facebook.com'.

**Name: EMAIL_ADDRESS**  
**Type: string**  
**Value:**  

*  A valid email address, e.g. 'postmaster@facebook.com'.

**Name: EVENT_ID**  
**Type: string**  
**Value:**  

*  An event ID, if generated externally, e.g. 'SpamRep Message-Id'.

**Name: FILE_CREATED**  
**Type: string**  
**Value:**  

*  File created by a process, e.g. 'C:\Temp\bot.exe'.

**Name: FILE_DELETED**  
**Type: string**  
**Value:**  

*  File deleted by a process, e.g. 'C:\Temp\bot.exe'.

**Name: FILE_MOVED**  
**Type: string**  
**Value:**  

*  File moved by a process, e.g. 'C:\Temp\bot.exe'.

**Name: FILE_NAME**  
**Type: string**  
**Value:**  

*  A file name on a system, can include path, e.g. 'C:\Temp\bot.exe'.

**Name: FILE_OPENED**  
**Type: string**  
**Value:**  

*  File opened by a process, e.g. 'C:\Temp\bot.exe'.

**Name: FILE_READ**  
**Type: string**  
**Value:**  

*  File read by a process, e.g. 'C:\Temp\bot.exe'.

**Name: FILE_WRITTEN**  
**Type: string**  
**Value:**  

*  File written by a process, e.g. 'C:\Temp\bot.exe'.

**Name: GET_PARAM**  
**Type: string**  
**Value:**  

*  A GET query parameter name, e.g. 'search' or 'user'.

**Name: HASH_IMPHASH**  
**Type: string**  
**Value:**  

*  An ImportHash of a PE32 or PE64 file, e.g.
'f34d5f2d4577ed6d9ceec516c1f5a744'.
See http://blog.virustotal.com/2014/02/virustotal-imphash.html for more details.

**Name: HASH_MD5**  
**Type: string**  
**Value:**  

*  An MD5 hash of a file, string, etc, e.g. '286755fad04869ca523320acce0dc6a4'.

**Name: HASH_SHA1**  
**Type: string**  
**Value:**  

*  A SHA1 hash of a file, string, etc, e.g.
'c8fed00eb2e87f1cee8e90ebbe870c190ac3848c'.

**Name: HASH_SHA256**  
**Type: string**  
**Value:**  

*  A SHA256 hash of a file, string, etc, e.g.
'6b3a55e0261b0304143f805a24924d0c1c44524821305f31d9277843b8a10f4e'.

**Name: HASH_SSDEEP**  
**Type: string**  
**Value:**  

*  An SSDeep hash of a file, e.g.
'768:ZY1jwLjYVmvZDnaB86WaRgAnL4PaxsJc2U0YjpsqANH+Y3b/JgKDiip47502Do1:ZY18LjYUvZDkIrPaxsJ3bxgPcP1'.  See http://www.forensicswiki.org/wiki/Ssdeep for more details.

**Name: HTML_ID**  
**Type: string**  
**Value:**  

*  The value of an ID attribute on an HTML or XHTML tag that identifies malicious or injected markup. For example, 'my-injected-ad'.

**Name: HTTP_REQUEST**  
**Type: string**  
**Value:**  

*  The raw GET <uri>, HEAD <uri>, POST <uri>, e.g. 'GET /index.html HTTP/1.1'.

**Name: IP_ADDRESS**  
**Type: string**  
**Value:**  

*  An IP address, version agnostic, e.g. '127.0.0.1' or 'fe80::202:c9ff:fe54:5952'.

**Name: IP_SUBNET**  
**Type: string**  
**Value:**  

*  A CIDR Mask, version agnostic, e.g. '128.0.0.0/24' or 'fe80::202:c9ff:fe54:5952/64'.

**Name: ISP**  
**Type: string**  
**Value:**  

*  An Internet service provider, e.g. 'MyInternetServiceProvider Inc.'.

**Name: LATITUDE**  
**Type: float**  
**Value:**  

*  The latitude for a location, as degrees dotted decimal e.g. 37.484924.

**Name: LAUNCH_AGENT**  
**Type: string**  
**Value:**  

*  The name of a LaunchAgent on OS X, e.g. '/System/Library/LaunchAgents/com.apple.quicklook.plist'.

**Name: LOCATION**
**Type: string**
**Value:**

*  The name of a physical location, such as "Menlo Park, CA". Note that there is
a separate field **COUNTRY**.

**Name: LONGITUDE**  
**Type: float**  
**Value:**  

*  The longitude for a location, as degrees dotted decimal e.g. , -122.148287.

**Name: MALWARE_NAME**  
**Type: string**  
**Value:**  

*  The common name for a piece of malware, e.g. 'Zeus'.

**Name: MEMORY_ALLOC**  
**Type: string**  
**Value:**  

*  The process file name that had memory allocated, e.g. 'C:\Temp\bot.exe'.

**Name: MEMORY_PROTECT**  
**Type: string**  
**Value:**  

*  The process file name that had memory permissions altered,
e.g. 'C:\Temp\bot.exe'.

**Name: MEMORY_READ**  
**Type: string**  
**Value:**  

*  The process file name that read memory from a process, e.g. 'C:\Temp\bot.exe'.

**Name: MEMORY_WRITTEN**  
**Type: string**  
**Value:**  

*  The process file name that had its memory written to, e.g. 'C:\Temp\bot.exe'.

**Name: MUTANT_CREATED**  
**Type: string**  
**Value:**  

*  Mutex created by a process, e.g. 'bot-installed'.

**Name: MUTEX**  
**Type: string**  
**Value:**  

*  A symbol defined in an OS for synchronization.


**Name: NAME_SERVER**  
**Type: string**  
**Value:**  

*  The host name that belongs to a name server, e.g. 'ns1.facebook.com'.

**Name: OTHER\_FILE\_OP**  
**Type: string**  
**Value:**  

*  Miscellaneous operations performed on a file, e.g. 'C:\Temp\bot.exe'.

**Name: PASSWORD**  
**Type: string**  
**Value:**  

* A password value, **must** be provided as an MD5 hash.

**Name: PASSWORD_SALT**  
**Type: string**  
**Value:**  

* A salt for hashing a password.

**Name: PAYLOAD_DATA**  
**Type: string**  
**Value:**  

* A piece of malicious content (e.g. an image or a document), Base64 encoded.

**Name: PAYLOAD_TYPE**  
**Type: string**  
**Value:**  

*  The MIME type format of the content in the PAYLOAD_DATA field,
e.g. 'image/jpeg'.

**Name: POST_DATA**  
**Type: string**  
**Value:**  

*  Data sent in a POST request, e.g. 'user=1234&content=this%20is%20a%20test'.

**Name: PROTOCOL**  
**Type: string**  
**Value:**  

*  The type of data protocol, e.g. 'tcp', 'ftp'.

**Name: REFERER**  
**Type: string**  
**Value:**  

*  The URI appearing in an HTTP referrer header, e.g. 'http://www.facebook.com/'.

**Name: REGISTRAR**  
**Type: string**  
**Value:**  

*  The registrar for a domain, e.g. 'REGISTER.COM, INC.'

**Name: REGISTRY_KEY**  
**Type: string**  
**Value:**  

*  The name of a registry key in Microsoft Windows,
e.g. 'HKEY_USERS\Software\Microsoft\Visual Basic'.

**Name: REG\_KEY\_CREATED**  
**Type: string**  
**Value:**  

*  Registry key created, e.g. 'HKEY_USERS\Software\Microsoft\Visual Basic'.

**Name: REG\_KEY\_DELETED**  
**Type: string**  
**Value:**  

*  Registry key deleted, e.g. 'HKEY_USERS\Software\Microsoft\Visual Basic'.

**Name: REG\_KEY\_ENUMERATED**  
**Type: string**  
**Value:**  

*  Registry key enumerated by a process,
e.g. 'HKEY_USERS\Software\Microsoft\Visual Basic'.

**Name: REG\_KEY\_MONITORED**  
**Type: string**  
**Value:**  

*  Registry key monitored, e.g. 'HKEY_USERS\Software\Microsoft\Visual Basic'.

**Name: REG\_KEY\_OPENED**  
**Type: string**  
**Value:**  

*  Registry key opened, e.g. 'HKEY_USERS\Software\Microsoft\Visual Basic'.

**Name: REG\_KEY\_VALUE\_CREATED**  
**Type: string**  
**Value:**  

*  Registry key value created,
e.g. 'HKEY\_LOCAL\_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Run'.

**Name: REG\_KEY\_VALUE\_DELETED**  
**Type: string**  
**Value:**  

*  Registry key value deleted,
e.g. HKEY\_LOCAL\_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Run'.

**Name: REG\_KEY\_VALUE\_MODIFIED**  
**Type: string**  
**Value:**  

*  Registry key value modified,
e.g. HKEY\_LOCAL\_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Run'.

**Name: REG\_KEY\_VALUE\_QUERIED**  
**Type: string**  
**Value:**  

*  Registry key value queried,
e.g. HKEY\_LOCAL\_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Run'.

**Name: SIGNATURE**  
**Type: string**  
**Value:**  

*  The signature string for detecting a threat.

**Name: SOURCE_PORT**  
**Type: integer**  
**Value:**  

*  Network port of the originating host, e.g. 13456.

**Name: TELEPHONE**  
**Type: string**  
**Value:**

*   The full, international version of a telephone number, e.g. +12225551212

**Name: URI**  
**Type: string**  
**Value:**  

*  A URI, e.g. 'http://www.facebook.com/some_page.php?test=yes'
or '/index.html'.

**Name: USER_AGENT**  
**Type: string**  
**Value:**  

*  A browser's user agent string, e.g.
'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:26.0) Gecko/20100101 Firefox/26.0'.

**Name: VOLUME_QUERIED**  
**Type: string**  
**Value:**  

*  Volume query action by a process.

**Name: WEBSTORAGE_KEY**  
**Type: string**  
**Value:**  

*  The name of a key used in HTML5 local or session storage, e.g. 'malware\_session\_data'.

**Name: WEB_PAYLOAD**  
**Type: string**  
**Value:**  

*  The base64 encoded raw payload of a web request (with headers), e.g.

     R0VUIGh0dHA6Ly9za2V0Y2h5LWRvbWFpbi5iaXovaW1nLTcxNzAwMy5qcGcgSFRUUC8xLjEKSG9zdDogc2tldGNoeS1kb21haW4uYml6ClVzZXItQWdlbnQ6IHdlYmNvbGxhZ2UvMS4xMzVhCgp0ZXN0IGRhdGEK

     decodes to

     GET http://sketchy-domain.biz/img-717003.jpg HTTP/1.1
     Host: sketchy-domain.biz
     User-Agent: webcollage/1.135a

     test data

**Name: WHOIS_NAME**  
**Type: string**  
**Value:**  

*  The name in whois information, e.g. 'Domain Administrator'.

**Name: WHOIS_ADDR1**  
**Type: string**  
**Value:**  

*  The first address line in whois information, e.g. '1601 Willow Road'.

**Name: WHOIS_ADDR2**  
**Type: string**  
**Value:**  

*  The second address line in whois information, e.g. 'Menlo Park, CA 94025'.

**Name: XPI**  
**Type: string**  
**Value:**  

*  A Firefox addon ID, e.g. '{e968fc70-8f95-4ab9-9e79-304de2a71ee1}'.


## Other Schema Field Enums

**Name: PRECISION**  
**Type: enumerated string**  
**Value:**  

*  Defines how accurately the indicator detects its intended target, victim or actor, one of:
  * UNKNOWN
  * LOW
  * MEDIUM
  * HIGH
  
**Name: REVIEW\_STATUS**  
**Type: enumerated string**  
**Value:**  

*  Defines how the indicator was vetted, one of:
  * UNKNOWN
  * UNREVIEWED
  * PENDING
  * REVIEWED\_MANUALLY
  * REVIEWED\_AUTOMATICALLY

**Name: SIGNATURE_TYPE**  
**Type: enumerated string**  
**Value:**  

*  Defines the type of signature being described, one of:
  * BRO
  * REGEX_URL
  * SNORT
  * SURICATA
  * YARA

