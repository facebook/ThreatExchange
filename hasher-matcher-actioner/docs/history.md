# History: HMA 1.0 (AWS HMA) -> HMA 2.0 (Open Media Match):

In March of 2024, [we archived](https://github.com/facebook/ThreatExchange/tree/HMA_1.0_archive/hasher-matcher-actioner) the original version of HMA, and replaced it with a full rewrite, which is what you'll find here. Below you can find our reasoning for doing so.

## Predecessor project: Hasher-Matcher-Actioner 1.0

HMA 1.0 was an earlier effort to build an offering based on open source components that could be picked up and deployed in a turn-key fashion for the purposes of hashing and matching content against databases of known harmful material at scale. However, we got feedback from industry that the lack of flexibility and hard dependencies on Amazon Web Services for critical components prevented several potential users from being able to deploy it. Additionally, the high number of dependencies needed to provide the robust functionality have become a maintenance burden over time.

With Open Media Match (HMA 2.0), we propose to build a new, entirely open source offering of composable components. We will drop the UI element and focus entirely on the backend API, we will eschew as many dependencies as possible, including those to specific cloud environments like AWS in favor of a containerized solution, and aim to be as infrastructure-agnostic as possible.

## Compare and contrast to HMA

| HMA 1.0 (AWS Deployed)                                          | HMA 2.0 (Docker image only)                                                |
| --------------------------------------------------------------- | -------------------------------------------------------------------------- |
| Heavy AWS dependencies: VPC, DynamoDB, Lambda, API Gateway, ... | OSS dependencies only                                                      |
| Opinionated: only supported by included Terraform scripts       | Runs in any Docker based infra                                             |
| Service capabilities provided by AWS Lambda                     | Service capabilities provided by composable and repackageable components   |
| AWS only, needs its own S3 buckets and DynamoDB tables          | Integrates anywhere Docker can be used, or under self-managed Python/Flask |
| Includes a GUI and API                                          | API only                                                                   |
| Scales automatically                                            | Doesn't auto-scale but can be auto-scaled                                  |

## Motivations

### Simpler setup and Time-to-Evaluation

While HMA 1.0 in theory was only a single terraform command to stand up an instance, in practice, getting the AWS infrastructure in place, and potentially jumping through many hoops to make it play nicely with your existing AWS infrastructure prevented evaluating the functionality to see if it was worth spending the time to complete an integration. We have found that many users want a way to evaluate the capabilities as fast as possible, which the Terraform and AWS dependencies are at odds with.

With HMA 2.0, we will specifically focus on this evaluation step, potentially allowing users to evaluate on a single machine - even a developer laptop.

### Reduce barriers to adoption

The ThreatExchange team originally chose the AWS dependency as part of scaling targets (4,000 QPS hash lookups), for an initial industry partner that could use AWS.

Since release, while some industry and NGO partners have been able to deploy and use AWS HMA, other industry partners have given feedback that the hard AWS dependency is not reconcilable with their business and technical constraints on what third-party software they can run, and where they can run it.

With HMA 2.0, we are limiting the number of dependencies and removing reliance on cloud-specific infrastructure.

### Facilitate external integrations

Hasher-Matcher-Actioner includes a GUI tool for interacting with the matching service and managing the hash database, but it's a standalone offering tightly coupled to HMA, and doesn't facilitate integration with either a client's internally-built tools or with an open source harmful-content management tool.

### Improve the Python-ThreatExchange Interfaces

Python-ThreatExchange was envisioned as a compatibility layer for trust and safety teams, academics, and open source contributors to make sharing improvements easier. However, to deploy and use these systems are either too tightly bound with HMA (AWS) or the CLI, and so make selective and compositional use of the library difficult. The design of HMA 2.0 will aim to standardize the core HMA steps (Fetching, Storing, Indexing, Hashing, Matching, Recording review results) in a way that makes them easier to partially adopt.

See [#1247](https://github.com/facebook/ThreatExchange/issues/1247) for more detail.
