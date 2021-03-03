Getting Started with Contributing

In it's rough state, the prototype needs some prior configuration / setup before you are ready to start developing on it. Below are some steps and tips for getting started. If anything needs correction, PRs are always welcome.

## Prerequisites

In the prototype's current state, the following tools are prerequisites to deploying the HMA prototype.

1. [terraform cli](https://www.terraform.io/)
2. [Docker](https://www.docker.com/)

Additionally, if you want to make use of the provided scripts for doing things like uploading new Docker images containing the code for the various AWS lambda functions used by HMA, you will want the following tools installed

1. [jq](https://stedolan.github.io/jq/)
2. [aws cli](https://aws.amazon.com/cli/)

Beyond tooling you need to have access to an AWS account where the various resources defined in the terraform files here will be created. You will want to either have your AWS credentials either in your environment or in a centralized credentials file. (See the [aws terraform provider documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs#authentication) for more information on these credentials) **Note: These applying these terraform files to your AWS account will result in resources being created that will create costs for your account.**

## Building the Docker Lambda Image

The lambda functions defined for HMA use docker images to hold the code executed by the functions. Until an image is published in a public docker registry, you will need to build and publish this docker image to a docker registry you own. There is a build script in [`scripts/update_lambda_docker_image.sh`](scripts/update_lambda_docker_image.sh) to help with this. This assumes there is an ECR repository already set up with the name `hma-lambda-dev` in your aws account. Run the script after providing a `DOCKER_TAG` environment variable. It is suggested to tag the image with the prefix you intend to use below in your terraform variables / environment. For example, if I am using the prefix `bodnarbm`, I might run the script like this

```shell
$ DOCKER_TAG=bodnarbm ./scripts/update_lambda_docker_image.sh
```

This script will build and then push the tagged image up to your accounts ECR repository. It should be ready for use then in the HMA lambdas. You will want to use this image below as your `hma_lambda_docker_uri` variable in `terraform.tfvars` (see Config Files section below for more information on setting this up), e.g.

```hcl
hma_lambda_docker_uri = "<AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/hma-lambda-dev:bodnarbm"
```

Additionally, if you are testing a change to a lambda function and just pushed up changed docker image, but reusing an old tag, you will need to force AWS lambda to pick up the new docker image for the function (this is because the lambda functions use the specific instance of the image at the time the function was created and does not follow changes in the tag). You can do this using the aws cli with something like

```shell
$ aws lambda update-function-code --function-name <LAMBDA_FUNCTION_NAME> --image-uri <HMA_LAMBDA_DOCKER_URI>
```

e.g.

```shell
$ aws lambda update-function-code --function-name bodnarbm_pdq_matcher --image-uri <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/hma-lambda-dev:bodnarbm
```

## Config Files

Before using terraform, you will need to provide some additional configuration, examples of which are provided in this folder using the same name, but with example suffixed to the end.

1. `terraform.tfvars`: In this file, you will want to define the values for the variables defined in [variables.tf](terraform/variables.tf). Only variables without defaults are required, though if you are setting up an environment for developing on the HMA prototype, you likely want to override the default `prefix` to allow having an isolated environment. See the terraform docs on [input variables](https://www.terraform.io/docs/configuration/variables.html) for more information on providing variable values and overrides.

2. *(optional)* `backend.tf`: This file is used for optionally defining a remote backend to store your terraform state. If you are working on development for the HMA prototype and are part of the facebook ThreatExchange team, it is highly suggested you use the configuration for this file in the internal wiki. That will enable state locking and remote state storage for your terraform environment.

## Deploying to AWS

1. After finishing the above steps, use `terraform plan` to see what changes will be made to your existing environment in AWS. If this is the first time running this, you will likely need to run `terraform init` first.

2. If the changes look acceptable, you would then use `terraform apply` to execute those changes on AWS.

## After Deploying

Until a Syncer module is created, test threatexchange data needs to be manually uploaded to S3 for the indexers to create their indexes. Go to the S3 service on the AWS console, and go to the S3 bucket created by your run of terraform (it should be named something like `<prefix>-hashing-data<string_of_numbers>`). There should be a `threat_exchange_data/` folder there. Open that folder and upload your test threat_exchange data. You can use the `threatexchange_samples` dataset that is downloaded by default using the `threatexchange cli` tool when there is no config given (access to the samples still requires ThreatExchange access though). Once these files are uploaded, you should then see indexes being created in the `index/` folder of the S3 bucket.

## Testing the HMA flow.

1. Ensure the indexes above have been created.
2. Go to the `images/` folder of the S3 bucket.
3. Upload some target and no target images.

This should run the images through the existing PDQ hasher and matcher lambda functions.
