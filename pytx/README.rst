pytx
=====================================================================

pytx (pie-tex) is a Python Library for interfacing with Facebook's ThreatExchange.

Build Status
------------

.. image:: https://img.shields.io/pypi/dm/pytx.svg
    :target: https://pypi.python.org/pypi/pytx/
    
.. image:: https://img.shields.io/pypi/v/pytx.svg
   :target: https://pypi.python.org/pypi/pytx

.. image:: https://img.shields.io/badge/python-2.7-blue.svg
    :target: https://pypi.python.org/pypi/pytx/

.. image:: https://img.shields.io/pypi/l/pytx.svg
    :target: https://pypi.python.org/pypi/pytx/
    
.. image:: https://readthedocs.org/projects/pytx/badge/?version=latest
    :target: https://readthedocs.org/projects/pytx/?badge=latest
                

Installation
------------

Use pip to install or upgrade pytx::

    $ pip install pytx [--upgrade]

Quick Example
-------------

.. code-block :: python

   from pytx import init
   from pytx import ThreatIndicator
   from pytx.vocabulary import ThreatIndicator as ti

   init('<app-id>', '<app-secret>')
   results = ThreatIndicator.objects(text='www.facebook.com')
   for result in results:
       print result.get(ti.THREAT_TYPES)

   # type is type_ because type is a reserved word.
   results = ThreatIndicator.objects(type_='IP_ADDRESS',
                                     text='127.0.0.1')
   for result in results:
       print result.get(ti.INDICATOR)


Documentation
-------------

For more information you can find documentation in the 'docs' directory, check
the Github wiki, or readthedocs (coming soon).
