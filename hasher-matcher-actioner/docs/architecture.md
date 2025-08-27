# Architecture

## The Stack

### Python Libraries

#### `python-threatexchange`

The core functionality is a Python package, evolved from the existing python-threatexchange package (`py-tx`). This package contains a Python library which implements all of the core functionality:

- Computation of image hashes using PDQ
- Compute hashes/signatures using other algorithms (e.g. MD5 for video)
- Management and curation of a local database of hashed content
- Exchange of hash lists (with third parties (NCMEC, GIFCT, StopNCII, ThreatExchange, others)
- Similarity search of candidate content hashes to known content

This library could be consumed purely as a component in a hypothetical in-house media matching system, but what is more likely is that it will be deployed as a service using the included REST API, built upon Flask, and managed via the included CLI.

#### Open Media Match Library

If you wish to deploy HMA manually (without the container) or roll your own container using an alternative container technology to Docker, HMA can be used as a library, which may require some additional customization to work for your environment.

#### API and CLI

The API and the CLI simply expose the functionality of the library as an HTTP REST service and as a command line tool, respectively. These are built into the Python package: Install the Open Media Match package and you get the library, the API, and the CLI all in one.

#### Docker Container

For convenience and simplicity, we also distribute the API service as a Docker container image. This allows rapid, low-dependency deployment into development and production environments based on a recommended and supported Python stack.

#### Service Dependencies

The only dependency is the database, for which we use Postgres.

Depending on your deployment scenario (read on), you will most likely also need a reverse proxy, Layer 7 router, or application load balancer (depending on your preferred terminology) to handle TLS termination, authentication and authorization, request routing, and maybe even caching. For example:

- Nginx
- Træfik
- Kubernetes ingress controller
- Apache HTTPD
- Amazon Application Load Balancer
- Azure Application Gateway

If you're operating at the scale where this becomes necessary, you will more than likely already have your own preferred solution here.

## Deployment scenarios and scaling strategies

### Single instance

![Single instance deployment](diagrams/deployment-strategy-single-instance.svg)

It's entirely possible to run everything on one machine. This has the advantage of being the easiest to set up and configure and is appropriate for:

- Evaluation, local development and testing
- Production environments with low traffic levels, low time-sensitivity, or otherwise relaxed availability constraints (i.e. you can tolerate the service being down for a short time)
- Keeping costs and complexity to a minimum

A single-instance Postgres can be run as a sidecar container next to the API server container, in the host OS, or on another machine.

### Redundant instances

![Redundant instance deployment](diagrams/deployment-strategy-redundant-instances.svg)

A typical production environment would require some degree of redundancy such that the loss of one server doesn't cause a service outage. In this scenario, you would run two identically sized Docker containers, on two separate Docker or Kubernetes hosts, with the Postgres database service in a third location with a redundancy strategy of its own.

Database redundancy is hard, and dependent on uptime constraints, budget, and engineering bandwidth available to support such a setup. Hosted managed Postgres services are also available on the market, e.g. Amazon RDS and Azure Database for PostgreSQL.

### Vertical scale-up

Building on the above, as traffic grows, the containers can simply be resized to accommodate the additional demand, by allocating them additional CPU cores and memory.

### Horizontal scale-out - split roles

![Split role deployment](diagrams/deployment-strategy-split-roles.svg)

At the higher end of the scaling curve, it becomes advantageous to run the API in a split-role pattern. This simply means having disjoint sets of instances in role groups where each role group is dedicated to one particular functional area of HMA.

These roles are:

#### Hashers

The hashers simply take content (images) in, and spit out PDQ hashes. This makes them simple, stateless, and dependency-free (no database connection is required!). They are also the most computationally demanding, due to needing to decompress, decode, and digest image files.

#### Matchers

Matchers connect to the database as read-only clients, monitor for new additions, and periodically rebuild their (in-memory) FAISS indices.

Their inputs are the hashes of candidate images (most likely having just had their hash computed by the adjacent hasher nodes), and their outputs are the hits in the similarity index fused with any relevant metadata about the match (severity, violation type, source of hash etc), as pulled from the database.

#### Curators

The curators handle all functions related to editing the contents of the database such as:

- Importing hash lists from the ThreatExchange
- Adding newly-identified violating content
- Editing the metadata of known content
- Removing, disabling or tombstoning content to be excluded from matching

A split-role deployment pattern allows each role to be scaled independently. We expect that sites will differ in how they scale depending on their traffic patterns, database sizes, update frequency, throughput, uptime and latency requirements.

Routing of incoming API requests to the correct role group backend is made as simple as possible by the design of the API, which follows least-surprise principles and is compatible with simple path-based routing.

## Request/Response flows

Two concurrent API call flows are illustrated here. From the left, we have the hashing/matching flow that would typically be called at high frequency in the content upload path for real-time or near-real-time scanning of uploaded content. From the right, we have administrative actions from the site operators who are updating the database of known violating content.

![Match request/response flow](diagrams/match-request-response-flow.svg)

## Backend

### Database Schema

![Database schema](diagrams/database-schema.svg)

### Indexing: FAISS

[FAISS](https://github.com/facebookresearch/faiss) is an open source library that provides efficient solutions for similarity search and clustering of dense vectors. This is particularly well-suited to media similarity search. We start with a simple table which maps content IDs to their PDQ hash:

| Bank Content ID: `int64` | Hash: `vec[int8]`    |
| ------------------------ | -------------------- |
| 1001                     | `[32, 123, 43, ...]` |
| 1002                     | `[312, 33, 12, ...]` |
| ...                      | `...`                |

Note that in this example we're using PDQ hashes, but any hash that decomposes to a vector of numbers will work just as well.

Given the above table, the FAISS index can be built which provides high performance nearest-neighbor lookups from the hash to the matching content IDs. During matching, the FAISS index is queried with a vector which, for example, could be the PDQ hash of a photo that we want to check for similarity to any of our known content. The results of the query are the vectors (hashes) in the index which are within a specified threshold distance to the queried one vector, as well as their ID. There are different functions for distance evaluation that can be used, such as euclidean and cosine.

In HMA, the hash lists are populated by the Curator, and the FAISS indices are periodically rebuilt, in-memory, by the Matchers.

At match time, the index returns the matching vectors and their associated content IDs. These IDs are then used to pull the full set of content metadata from the database which will inform the client system as to what exactly the candidate photo matched against.

It should also be possible to split the index from the matcher, and substitute FAISS with other Vector Database technologies if you are looking to use HMA as a library or are customizing it further. Some example databases that will likely work:

- Pinecone
- Milvus
- Pgvector
- Vertex AI

### Data exchange: python-threatexchange

Under the hood, HMA builds on the core interfaces of python-ThreatExchange. The key ones being:

- **SignalExchangeAPI**: Frameworks for connecting to external sources of trust & safety information and translating them to a common compatibility layer
- **SignalType**: A technique using serialized information (signals, hashes, embeddings, etc) to flag or match content
- **ContentType**: How to map which signals are relevant to content on your platform

HMA will allow you to add more instances of these interfaces (which allows customizing its behavior to your platform, say for example by creating custom ContentType to cover your complex objects like posts, comments, or live streams), but it will fall back to a naive implementation that might not scale. You may need to customize much more of its internals to get the same functional guarantees provided by PDQ and MD5.
