# Hasher-Matcher-Actioner (HMA)

![image](https://user-images.githubusercontent.com/1654004/111525752-2d5f0200-871b-11eb-9239-98dffecaa45e.png)

HMA is a prototype reference architecture for rapidly spinning up a complete solution for integrating with ThreatExchange datasets and evaluating content against them. The goal is to make it possible to spin up an instance with the minimum number of commands, and be able to run at a reasonable scale without customization. 

The name "hasher, matcher, actioner" refers to the process by which new content is evaluated against banks of known content. First content is hashed into intermediate representations ("Hashes" or "Signals"), then it is matched against an index of known content, and then some action is taken as a result, such as counting the hits, or enqueuing for human review.

In the long term, approaches that don't necessarily involve hashing may also be considered (machine learning, etc), but the name "HMA" has stuck with the project.

# General Architecture
HMA runs on Amazon Web Services (AWS), the code itself is packeged with Docker, and Terraform is used to spin up and tear down instances. HMA is intended to be part of a content moderation solution running in your own stack, and so we expect many users will break up individual components, write their own Terraform scripts, or run natively as needed. Additionally, we've attempted to make it possible to insert hooks in every stage of the process, which is where the bridge between your own infrastracture and HMA might occur.

# Running HMA 
Running HMA on a cloud provided will cost you money! Make sure you are ready for that before running any commands that create cloud resources.

## Dependencies
You'll need an AWS account set up. Additionally, you'll need the following tools ready:
1. [aws cli](https://aws.amazon.com/cli/)
2. [jq cli](https://stedolan.github.io/jq/)
3. [terraform cli](https://www.terraform.io/)
4. [Docker](https://www.docker.com/)

## Spinning Up an Instance
In a horrifying misuse of Make, there is a makefile to help you get started and create some configs with default naming. More details on customization be found in [CONTRIBUTING.md](CONTRIBUTING.md)

```bash
$ cd hasher-matcher-actioner
# Before doing this step, make sure to configure the aws cli with `aws configure`
$ make dev_create_configs  # Will populate a terraform.tfvars backend.tf with default names
# Optional: edit terraform.tfvars backend.tf to your preference for names of services
$ make docker  # Will build the image from the local copy of the repo
$ make dev_create_instance  # This will upload docker to AWS and then start the instance
# At this point, you can interact with the service
$ make dev_destroy_instance  # This will wipe your instance completely, leaving no resources on the cloud
```

## Demonstrating HMA From the Instance
This section needs more details, and will somday have a demo video. 

The too-few-details-to-be-useful version of this is:
1. Copy state files from a run of the `python-threatexchange` CLI to the appropriate s3 bucket
2. Add an SNS subcription (i.e. email) on completion of a match lambda
3. Upload test photos to the appropriate s3 bucket
4. Hopefully get a notification from step #2

# Contributing to HMA
For current contributing guidance, please see [CONTRIBUTING.md](CONTRIBUTING.md).
