pytx
=====================================================================

pytx (pie-tex) is a Python Library for interfacing with Facebook's ThreatExchange.

Build Status
------------

.. image:: https://travis-ci.org/facebook/ThreatExchange.svg
    :target: https://travis-ci.org/facebook/ThreatExchange

.. image:: https://img.shields.io/pypi/dm/pytx.svg
    :target: https://pypi.python.org/pypi/pytx/

.. image:: https://img.shields.io/pypi/v/pytx.svg
   :target: https://pypi.python.org/pypi/pytx

.. image:: https://img.shields.io/badge/python-2.7-blue.svg
    :target: https://pypi.python.org/pypi/pytx/

.. image:: https://img.shields.io/pypi/l/pytx.svg
    :target: https://pypi.python.org/pypi/pytx/

.. image:: https://readthedocs.org/projects/pytx/badge/?version=latest
    :target: https://pytx.readthedocs.org/


Installation
------------

Use pip to install or upgrade pytx::

    $ pip install pytx [--upgrade]

Quick Example
-------------

.. code-block :: python

   from pytx.access_token import access_token
   from pytx import ThreatDescriptor
   from pytx.vocabulary import ThreatDescriptor as td

   access_token('<app-id>', '<app-secret>')
   results = ThreatDescriptor.objects(text='www.facebook.com')
   for result in results:
       print result.get(td.CONFIDENCE)

   # type is type_ because type is a reserved word.
   results = ThreatDescriptor.objects(type_='IP_ADDRESS',
                                      text='127.0.0.1')
   for result in results:
       print result.get(td.INDICATOR)

Documentation
-------------

For more information you can find documentation in the 'docs' directory, check
the Github wiki, or readthedocs_.

.. _readthedocs: https://pytx.readthedocs.org

See Also
-------------

We now offer tag-based, descriptor-focused reference designs in

* **Python**: <https://github.com/facebook/ThreatExchange/blob/main/hashing/te-tag-query-python>
* **Ruby**: <https://github.com/facebook/ThreatExchange/blob/main/hashing/te-tag-query-ruby>
* **Java**: <https://github.com/facebook/ThreatExchange/blob/main/hashing/te-tag-query-java>

The common context to all these is that since early 2018 ThreatExchange has moved beyond malware/phishing into cross-company integrity-signal sharing. This newer tooling largely overlaps the old (such as pytx), but with an added focus on more interactive tooling for a broader, more diverse userbase; a strong threat-descriptor focus (vs malware analyses); and enhanced support for cross-company feedback mechanisms.
