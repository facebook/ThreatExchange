pytx
=====================================================================

pytx (pie-tex) is a Python Library for interfacing with Facebook's ThreatExchange.

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

Documentation
-------------

For more information you can find documentation in the 'docs' directory, check
the Github wiki, or readthedocs (coming soon).
