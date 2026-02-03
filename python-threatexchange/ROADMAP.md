This file gives some high level suggestions and ongoing direction for the repository, and larger projects that might need help to complete, if you are a developer interested in donating more time.

As of 8/2025, python-threatexchange is not in very active development, as most energy is being invested in one of the projects built on top of it: [Hasher-Matcher-Actioner (HMA)](https://github.com/facebook/ThreatExchange/tree/main/hasher-matcher-actioner)

Thus, many of these suggest next steps have a relationship with HMA.


# Most Needed
## Migrating Core Interfaces from HMA -> pytx
Issue: https://github.com/facebook/ThreatExchange/issues/1754

The current version of HMA is much newer than pytx, and so our original attempts at the interface, used by the `tx` CLI, turned out not to map well in production. 

While rebuilding HMA, we redid the core interfaces for storage and matching. The current CLI implementation of the first implementation of these interfaces (giant pickle files) also has many problems.

Completing the migration of these interfaces, and then redoing the `tx` implementation of these interfaces will allow future contributors to test database improvements or database alternatives (such as native AWS implementations) on the `tx` CLI, allowing a more cohesive `tx` <-> hma experience.

## Complete PDQ Index Redo migration
Issue: https://github.com/facebook/ThreatExchange/issues/1613

The default PDQ index is both complex, and also has at least some bugs that might reduce recall. We did a redo with more comprehensive testing, but it's still not enabled by default.

## Increasing robustness and coverage of testing
Issue: TBD

Especially as HMA increases adoption, making sure that the core functionality inheiriting from pytx is well-covered by regression tests will help increase the reliability of that system. If you are able to donate time on other projects, make sure to include strong automated testing. 

# Expansions that could expand the capabilities of HMA
## Building a new base interface for "Classifier"
Issue: https://github.com/facebook/ThreatExchange/issues/1864

pytx was built with hashing and matching first, but many companies need help adopting services that don't share embeddings directly, such as Google's content safety API, or Amazon Rekognition, or even a self-trained image or video classifier.

We can support these with a new core interface alonside SignalType, ContentType, and ExchangeAPI: `Classifier` / `ClassifierType` (to your preference).

The entirety of the core pytx offering, taking an image -> hashing it -> comparing it to known indexed hashes -> returning "Match" or "No Match" is actually itself a type of classifier, so the first implementation might just be bunding that service. Considering use the the matching core interface from HMA as inspiration.  

Interfaces tend to be the hardest thing to get right, and tend to be hard to change, so this will involve a lot of discussion.
