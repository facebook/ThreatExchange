# Goals and non-goals

## Goals

### Deployment & Use

- No dependencies on any specific cloud provider (it should be possible to deploy in AWS, Google Cloud, on-prem, etc)
- Should have a single-box (including developer laptop) deployment for testing and development.
- The primary means of interacting should be API-based, to focus on integration to existing partner platform stacks
- Support an unnamed proposed human review tool being pitched by an industry partner.
- Have a minimum of third-party dependencies to simplify long-term maintenance.

### Support the “Evaluation Step” for Platforms Onboarding to Signal Sharing Programs

Should contain enough functionality to do the “evaluation step” for joining new cross-industry programs. This means:

- Single instance/machine deployment
- With smallest possible configuration, can independently contact the external API, download all data, and prepare indices.
- Clear way to tell if an instance has completely downloaded and prepared all data for matching.
- Handle modest test traffic from the single instance
  - On the scale of all human reviews: 1-10 qps
  - On the scale to reliably detect 1-per-million harms within 1 week of sampled production traffic (~4.6M samples over 1 week => 0.13 qps)
- Produce a logfile or simple-to-pass-to-manual-review output at the end of that week

### Key Features

- Supports all core interfaces of python-ThreatExchange: SignalType, ContentType, SignalExchangeAPI
- End-to-end lifecycle support for cross-industry programs
- Full implementation for a limited number of SignalTypes and ContentTypes
  - Image + PDQ
  - Video + MD5
  - Naive Hashing + Naive SignalType index build & match to support testing new SignalTypes, though potentially with a very inefficient implementation.
- Quick disable/enable for matching on single Signals and hash lists
- Simple API for forming hash lists and recording review results

### Functional Requirements

- Single box instance
  - Be able to fetch, store, index at least 10M PDQ hashes
    - Use less than 8GB memory at peak
    - Use less than 100GB disk
    - No GPU requirement
  - On to-be-defined target hardware:
    - Handle >1 qps image lookups (hashing + matching)
    - Handle >1 qps video hash lookups (matching)
  - Multi-instance deployment, with horizontal scaling:
    - 1000 qps image hash + match should be possible
    - 100M PDQ hash index should be possible
    - <1d latency on fetching & indexing signals from external sources
    - <10 minute latency on being able to match newly-added hashes
    - <10 minute latency on being able to stop matching disabled hashes
    - <10¢ / 1000 images scanned (<$100 / 1M images) - no more than 10x more expensive than AWS HMA

## Stretch Goals

### Live Content Clustering

An HMA 2.0 instance that is being used to scan live traffic on a platform has all of the data needed to automatically generate clusters of content, and allow measurement of viral content. Storage costs for such as system scale with the number of hours or days supported. This could quickly unlock valuable capabilities for a platform:

- Grouping human review by similar content
- Automated flagging of high-virality content for review
- Review prioritization based on instances on platform
- Network discovery tooling
- Deduping jobs in a review queue

### Retroaction (aka Live Traffic Replay)

Similar to Live Content Clustering, it’s common that content might already have been uploaded to a platform before it might be manually flagged and reviewed. Your platform may want to be able to match content _after_ it has already been uploaded. HMA 2.0 has all the interfaces needed to implement this natively.

## Non-goals

### User Interface

Adding in a user interface would require taking on significant additional dependencies, and may not be used by all users. For now, we plan on only providing a UI in the AWS-deployed version of Hasher-Matcher-Actioner. This version uses an API (and some CLI helpers) as the main interface.

### Actioning Interface / Combining Classification Signals

HMA (AWS) provided a way to rewrite “Action Rules” that trigger after content has been classified by HMA during a match. This allows combining multiple classification signals or triggering multi-step verification. However, we are holding off on any interface for HMA 2.0 for now.

### Complex Video Lookup (e.g. vPDQ)

There are types of content lookups that require bespoke or customized indexing solutions. vPDQ, for example, generates variable-length hashes that need to be stored in multiple formats to do a complete lookup. We are choosing to punt on this implementation, though the “Naive” SignalType implementation would allow using vPDQ at very low scales.

### High Scale

If you are at the scale where you need greater than 1000qps of lookups, or high scale video matching, the complexity to support it starts to require large dedicated teams to build and support that complexity. If you’ve made it here, your platform is very likely a successful one and it makes sense to start building bespoke solutions tailored to your infrastructure and content. You may also be near the threshold where you are experimenting with your own detection systems and proprietary embeddings, which may need different solutions than the ones presented in HMA 2.0.
