# ThreatExchange Extensions

Originally, this library was meant specifically for Facebook's [ThreatExchange](https://developers.facebook.com/docs/threat-exchange/) platform. However, we think that the concept of open source trust and safety could benefit from a library that allows the infrastructure for sharing signals and hashes from many sources, and potentially apply many techniques. 

Not all techniques will make sense for all use cases, but there are several concepts like "Content", "Signal", and "Exchange" which we think are universally applicable. 

Using the pattern described here, you can quickly bundle content, signals, and APIs that can then be compatible with the threatexchange CLI, and Hasher-Matcher-Actioner tools.

This is meant for both existing users of those tools to test out new techniques to improve their ability to detect harm, but also for researchers and the general public to create  improved techniques, which could then be rapidly adopted by existing exchange programs if shown to be effective.

## What's in This Directory
A number of extensions that require additional libraries to be installed, but are common or interesting enough to be maintained along with the core library. If you install all of the "extras_require" in setup.py, you'll have all the tools you need to run all the extensions.

# Creating Extensions
You can create your own extensions easily, and we encourage you to do so!

## A Note on Name Collisions
ContentType, SignalType, and SignalExchangeAPI all require a unique string name to enable the various lookups. There will be a challenge for extension writers to choose short, human-friendly names that have not already been used by others. As long as a runtime does not have two types with the same short name, it will still work properly. To aid with finding a free name, we'll try and keep a list of extensions here with their names. Feel free to reach out to threatexchange@fb.com to get your extension listed here.

| Type | Package Name | Name | Note |
| ------------- | ------------- | ------------- | ------------- |
| Signal | threatexchange | raw_text | Match strings with strings 
| Signal | threatexchange | trend_query | Simple regex on strings 
| Signal | threatexchange | url | Match known URLs
| Signal | threatexchange | pdq | Photo scanning with PDQ
| Signal | threatexchange | url_md5 | Match hashes of known URLs
| Signal | threatexchange | video_md5 | MD5 of video
| Signal | threatexchange.extensions.pdq_ocr | pdq_ocr | photos+text (memes)
| Signal | threatexchange.extensions.text_tlsh | text_tlsh | tlsh scanning on text
| Signal | threatexchange.extensions.vpdq | vpdq | vPDQ video hashing
| Signal | [tx-extension-clip](https://pypi.org/project/tx-extension-clip/) | clip | [CLIP](https://github.com/openai/CLIP) image embedding with a preloaded model
| Signal | TBD | tmk_pdqf | The planned name for TMK+PDQF video hashing 
| Signal | [threatexchange_photodna](https://github.com/TechnologyCoalitionOrg/) | photodna | Microsoft PhotoDNA hashing (PhotoDNA license required, see [Microsoft](https://www.microsoft.com/en-us/PhotoDNA/Contact-Us) or the [Tech Coalition](https://www.technologycoalition.org/contact)).
| Content | threatexchange | text | Text files and strings
| Content | threatexchange | photo | Photo formats
| Content | threatexchange | video | Video formats
| Content | threatexchange | url | urls
| Content | threatexchange.extensions.pdf | pdf | PDF content extraction
| API | threatexchange | fb_threatexchange | Meta's Graph API ThreatExchange
| API | threatexchange | stopncii | StopNCII.org
| API | threatexchange | sample | Static sample signals
| API | threatexchange | local_file | Load content from a file
| API | threatexchange | ncmec | NCMEC hash API
| API | N/A | iwf | Reserved to prevent confusion with IWF API

## Writing a ThreatExchange Expansion Module
Using the interfaces for SignalType, ContentType, and SignalExchangeAPI, create classes that extend as many of those as you think should be bundled together. 

Next, in a module (`__init__.py` is fine), you'll want to have a variable named `TX_MANIFEST` that is assigned a `ThreatExchangeExtensionManifest` object. From there, simply list all the objects that you've implemented.

```
# maybe in __init__.py...

from threatexchange.expansions.manifest import ThreatExchangeExtensionManifest

from threatexchangecontributions.myproject.signals import FooSignal, BarSignal
from threatexchangecontributions.myproject.contents import BazContent
from threatexchangecontributions.myproject.apis import ZedAPI

TX_MANIFEST = ThreatExchangeExtensionManifest(
    signal_types=(FooSignal, BarSignal),
    content_types=(BazContent,),
    apis=(ZedAPI,)
)
```

### PyPi Packaging and Naming
PEP423 suggests "threatexchangecontributions.X" as potential package name, but that is quite lengthy. We're worried people will get confused about who maintains extensions if they are named "threatexchange" or "threatexchange.extensions" (the extensions in this directory are maintained by this project). If you want to try and link your package name to the project without going for the wordy version, "tx_extensions.X" appears to be free real estate in pypi (though tx is an unrelated package). 

### Handling Dependencies on Other Extensions or Libraries
If your extension will function correctly without another extension (for example an API that can fetch some signal types without the SignalType), we suggest making a decision between having your library work without it (for example, by checking whether that SignalType is importable), or by simply making it required. If distributing your extension via pypi, using extra requires for the additional functionality seems to be a good compromise.

If your SignalType requires modules be available to work at all, we suggest making those modules required if there's not an easy fallback.

Here's an common example with FAISS:

```
class MyCoolSignalType(SignalType):
    @classmethod
    def get_index_cls(cls) -> t.Type[index.SignalTypeIndex]:
        return _INDEX_CLS
   ...

class FallbackIndex(TrivialLinearSearchHashIndex):
    _SIGNAL_TYPE = MyCoolSignalType

# I'm sure I'll enjoy debugging this later!
try:
    from myextension import faiss_backed_index
    _INDEX_CLS = faiss_backed_index.MyCoolFAISSBackedIndex
except ImportError:
    _INDEX_CLS = FallbackIndex
```

## Testing Your Module from the threatexchange CLI
Both HMA and the `threatexchange` CLI are backed by the same underlying libraries, so the fastest way to test your expansion is using the CLI.

It will also sanity check to make sure you don't have collisions with existing modules

```
# Provide the path to the module with TX_MANIFEST
$ threatexchange config extensions add threatexchangecontributions.myproject
Added my.module.name:
  Signals:
    foo - FooSignal
    bar - BarSignal
  Contents:
    baz - BazContent
  APIs:
    zed - ZedAPI

# What do I have?
$ threatexchange config extensions list
threatexchangecontributions.myproject

# I don't want this anymore!
$ threatexchange config extensions remove threatexchangecontributions.myproject

# Oh no I broke everything and am filled with sadness and regret!
$ rm ~/.threatexchange  # factory reset
```

There is also a helper for testing new implementations of SignalType in `/threatexchange/signal_type/tests/signal_type_test_helper.py`. We strongly recommend you use this test to prove your SignalType implementation works as expected.
