# Hasher Matcher Actioner (HMA)

_Note: HMA has just completed a rewrite! It is now an entirely new architecture. You can [read our motivations below](./docs/history.md). If you need the HMA 1.0 code (Terraform, AWS, node), it lives forever with a copy of its wiki at [HMA_1.0_archive](https://github.com/facebook/ThreatExchange/tree/HMA_1.0_archive/hasher-matcher-actioner)_

# Project Introduction

[Meta's newsroom post about HMA](https://about.fb.com/news/2022/12/meta-launches-new-content-moderation-tool/).

"Hasher-Matcher-Actioner" or HMA, is a reference implementation for a key Trust and Safety content moderation capability: copy detection. Copy detection refers to the ability to identify identical or similar items to ones that you've previously identified. One popular technology used in copy detection is "hashing" technology, which allows previously seen content to be turned into anonymous digital fingerprints called "hashes". Different platforms could then share these hashes to help other platforms improve their ability to detect similar content. There are many Trust & Safety programs that allow platforms to work together to detect harmful and illegal content, such as the [National Center for Missing and Exploited Children (NCMEC) Hash Sharing Program](https://report.cybertip.org/hashsharing/v2/documentation/), the [Global Internet Forum to Counter Terrorism's Hash-Sharing Database](https://gifct.org/hsdb/), [StopNCII.org](https://stopncii.org/) and, Meta's [ThreatExchange](https://developers.facebook.com/docs/threat-exchange/) to name a few.

To participate in a program, platforms need to have capabilities related to the hashing techniques used by the program, the ability to ingestion of third party hashes, and then to match their content against those hashes. Hasher-Matcher-Actioner provides all the technical pieces you need.

The name "hasher, matcher, actioner" refers to the technical process by which new content is evaluated against collections of known content (called "Banks" in HMA):

1. First content is **hashed** into intermediate representations ("Hashes" or "Signals")
2. Then it is **matched** against an index of known content
3. If it matches, some **action** is taken as a result, such as logging the content or enqueuing it for human review.

We have documentation on the following aspects of the HMA project:

- [Architecture](./docs/architecture.md)
- [Goals & Non-Goals](./docs/goals.md)
- [Project History](./docs/history.md)
- [API](./docs/api.md) (work in progress)

## Configurability

There is no one-size-fits all solution to make platforms safe, and even in the narrow scope of hashing and matching technology, there are many possible solutions. HMA is designed to be highly configurable, such that new algorithms, hash exchanges, or other capabilities could be integrated later. If you want to use a custom or proprietary hashing algorithm with HMA, you simple need to follow the interfaces defined in [python-threatexchange ](../python-threatexchange) to add new capabilities. A full list of known available algorithms and compatible exchanges can be found at [the python-threatexchange/extensions README](https://github.com/facebook/ThreatExchange/tree/main/python-threatexchange/threatexchange/extensions/README.md).

You can find an example on expanding the base image to include the Clip tx extension [here](https://github.com/juanmrad/HMA-CLIP-demo)

## Using HMA for your platform

HMA can be used as a library, or in any deployment setup that can use docker. It uses a simple REST API to make it as simple as possible to include in your existing environment. You'll need an engineer familiar with your platform's architecture to figure out the best way to deploy it in your ecosystem. At it's simplest, HMA can be run on a single machine, which is enough for evaluation purposes. At scale, HMA is designed with horizontal scalability in mind, and you can increase throughput by increasing the number of instances.

If you are interested in using HMA for your platform, but find it's missing something for your usecase, [this issue](https://github.com/facebook/ThreatExchange/issues/1440) is currently the best place to make requests!

### Docker

#### How to use this image

The HMA Docker image requires a PostgreSQL database to store information. Below is how you can set up and use the HMA image effectively in different environments:

#### Pre-requisites

- A running PostgreSQL database.
- A configuration file that specifies settings for different roles for each instance running (Hasher, Matcher, Curator) or a configuration file for a single instance for all three roles.

#### Using Docker Compose

You can see a complete example using Docker Compose in the provided [docker-compose.yaml](./docker-compose.yaml) file. This example includes both the application and database services, illustrating how they can be orchestrated together.

#### Configuration File

HMA requires a configuration file passed as an environment variable, `OMM_CONFIG`, which specifies various operational parameters. An [example configuration file](./reference_omm_configs/development_omm_config.py) can be found in the repository for you to customize according to your needs.

#### Running the Application in Development

To run HMA in a development environment using Docker, use the following command:

```bash
$ docker run -e OMM_CONFIG='/build/reference_omm_configs/development_omm_config.py' -p 5000:5000 ghcr.io/facebook/threatexchange/hma flask --app OpenMediaMatch.app run --host=0.0.0.0
```

This command sets the necessary environment variable and exposes the app on port 5000 of your host machine, making the API accessible locally.

#### Running the Application in Production

For production environments, it is recommended to use a more robust server like Gunicorn instead of Flask's built-in server. Also, ensure that only a single instance of the curator role is active at any time to manage the indexing and download of hash bank data effectively.

Here is an example command to run the application with Gunicorn:

```bash
$ docker run -e OMM_CONFIG='/build/reference_omm_configs/production_omm_config.py' -p 5000:5000 ghcr.io/facebook/threatexchange/hma gunicorn --bind 0.0.0.0:5000 "OpenMediaMatch.app:create_app()"
```

#### Notes:

- Adjust the port configurations and environment variables according to your specific deployment requirements.
- It is crucial to handle the database credentials and other sensitive data securely, preferably using secrets management tools or services.

## Demo instance

HMA can be easily run locally for demo purposes. While Docker is running on your machine. access the directory `hasher-matcher-actioner` and run the command:

```bash
$ docker compose up
```

This will spin up both a postgresql db as well as an instance of the app running all the configurations ready for testing.

### Demo UI and Walkthrough
Please see [hma-ui.md](hma-ui.md) for a walkthrough of the UI!

# Contributors

- [David Callies](https://github.com/Dcallies)
- [Sam Freeman](https://github.com/Sam-Freeman)
- [Nikolay Gospodinov](https://github.com/NikolayOG)
- [Doug Neal](https://github.com/dougneal)
- [Juan Mrad](https://github.com/juanmrad)
- And many more!
