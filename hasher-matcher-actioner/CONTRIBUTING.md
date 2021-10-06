# Getting Started

You need some prior configuration / setup before you are ready to start developing on it. Below are some steps and tips for getting started. If anything needs correction, PRs are always welcome.
## Prerequisites

In the prototype's current state, the following tools are prerequisites to deploying the HMA prototype.

1. [terraform cli](https://www.terraform.io/)
2. [Docker](https://www.docker.com/)

Additionally, if you want to make use of the provided scripts for doing things like uploading new Docker images containing the code for the various AWS lambda functions used by HMA, you will want the following tools installed

1. [jq](https://stedolan.github.io/jq/)
2. [aws cli](https://aws.amazon.com/cli/)
3. [make](https://www.gnu.org/software/make/)

Beyond tooling you need to have access to an AWS account where the various resources defined in the terraform files here will be created. You will want to either have your AWS credentials either in your environment or in a centralized credentials file. (See the [aws terraform provider documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs#authentication) for more information on these credentials) 

> **WARNING** `apply`ing these terraform files to your AWS account will result in resources being created that may be billed to your account.

## Automated Development Environment

If you are using [VS Code](https://code.visualstudio.com/), and we recommend you do, you can use the Devcontainer technology to get started real quick and have a great developer experience. 
1. Download VS Code from the link.
2. Install [Docker Desktop](https://www.docker.com/products/docker-desktop) on your computer. 
3. Install the [remote containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.vscode-remote-extensionpack)

    Create `.hma-cmdhist` directory in your home directory. Use `$ mkdir -p ~/.hma-cmdhist` or equivalent for your OS.

4. Use `[Cmd]+[Shift]+[P]` inside VS Code and choose "Remote-Containers: Open folder in container ..." and navigate to the directory containing this file.

The first time may take a while because images need to be built. Subsequently, opening the container will be blazing fast. 5-10 seconds on a 2019 MacBook Pro.

The devcontainer provides all the tools you need to build and hack on HMA. Including python, docker, make, and Typescript tooling.

### Common Errors and how to correct them

1. **Can't connect to docker...**
    > Got permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock: Get http://%2Fvar%2Frun%2Fdocker.sock/v1.24/images/json: dial unix /var/run/docker.sock: connect: permission denied

    Run `sudo chown $(whoami):developers /var/run/docker.sock` in a VS Code integrated terminal. (`[Cmd]+[Shift]+[P]` "Terminal: Create new integrated terminal...")


2. **Building webapp taking too long..**
    If you see sustained 100% CPU when running `npm install|start|build` within the webapp directory, you might need to provide more memory and CPU to the docker desktop app. We recommend atleast 4GB of RAM and 2CPUs.

## Developing HMA

We have built out some tooling that relies on Visual Studio Code. [Install](https://code.visualstudio.com/) VS Code to con

## Building the Docker Lambda Image

The lambda functions defined for HMA use docker images to hold the code executed by the functions. You will need to build and publish this docker image to a docker registry you own. eg. an AWS ECR repository.

There is a build script in [`scripts/update_lambda_docker_image.sh`](scripts/update_lambda_docker_image.sh) to help with this. This assumes there is an ECR repository already set up with the name `hma-lambda-dev` in your aws account. Run the script after providing a `DOCKER_TAG` environment variable. 

It is suggested to tag the image with the prefix you intend to use below in your terraform variables / environment. For example, if I am using the prefix `bodnarbm`, I might run the script like this

```shell
$ DOCKER_TAG=bodnarbm ./scripts/update_lambda_docker_image.sh
```

This script will build and then push the tagged image up to your accounts ECR repository. It should be ready for use then in the HMA lambdas. You will want to use this image below as your `hma_lambda_docker_uri` variable in `terraform.tfvars` (see Config Files section below for more information on setting this up), e.g.

```hcl
hma_lambda_docker_uri = "<AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/hma-lambda-dev:bodnarbm"
```

There is also a Make command that does the above steps...

```
make upload_docker
```

Additionally, if you are testing a change to a lambda function and just pushed up changed docker image, but reusing an old tag, you will need to force AWS lambda to pick up the new docker image for the function (this is because the lambda functions use the specific instance of the image at the time the function was created and does not follow changes in the tag). You can do this using the aws cli with something like

```shell
$ aws lambda update-function-code --function-name <LAMBDA_FUNCTION_NAME> --image-uri <HMA_LAMBDA_DOCKER_URI>
```

e.g.

```shell
$ aws lambda update-function-code --function-name bodnarbm_pdq_matcher --image-uri <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/hma-lambda-dev:bodnarbm
```

Lastly, if you are testing changes to the [`python-threatexchange` module](https://github.com/facebook/ThreatExchange/tree/main/python-threatexchange) that you would like to deploy on docker, you can make docker reference your local version of `python-threatexchange` by running the following steps from the `hasher-matcher-actioner` directory:

1. `$ cp -r ../python-threatexchange local_threatexchange`
2. Edit the Dockerfile to include the following lines **before** the pip install requirements:

```
ARG LOCAL_THREAT_EXCHANGE=./local_threatexchange
COPY $LOCAL_THREAT_EXCHANGE $LOCAL_THREAT_EXCHANGE
RUN python3 -m pip install ./local_threatexchange --target "${DEPS_PATH}"
```

3. `$ make docker && rm -r local_threatexchange`

## Config Files

Before using terraform, you will need to provide some additional configuration, examples of which are provided in this folder using the same name, but with example suffixed to the end.

1. `terraform.tfvars`: In this file, you will want to define the values for the variables defined in [variables.tf](terraform/variables.tf). Only variables without defaults are required, though if you are setting up an environment for developing on the HMA prototype, you likely want to override the default `prefix` to allow having an isolated environment. You may want to set up a shared Cognito user pool for multiple developer environments to share. To do that, run `terraform apply` from `/authentication-shared` once (note it has its own terraform.tfvars) then use the outputs in the main `terraform.tfvars`. See the terraform docs on [input variables](https://www.terraform.io/docs/configuration/variables.html) for more information on providing variable values and overrides.

2. _(optional)_ `backend.tf`: This file is used for optionally defining a remote backend to store your terraform state. If you are working on development for the HMA prototype and are part of the facebook ThreatExchange team, it is highly suggested you use the configuration for this file in the internal wiki. That will enable state locking and remote state storage for your terraform environment.

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


## Running Lambdas locally

A helper script pulls in environment variables from AWS's lambda configuration and runs your lambda with those environment variables. This can be used locally to run _and_ debug python code.

eg. to run the hasher lambda

```
$ python -m hmalib.scripts.cli.main run-lambda --lambda-name hasher
```

Or alternatively if you've done `python setup.py develop`, just
```
$ hmacli run-lambda --lambda-name hasher
```

This will cache terraform outputs to make things faster for subsequent runs. If you have changed your prefix, you might want to use the `--refresh-tf-outputs` flag when using the command.

### Providing input to your lambdas

* Create a file `hasher-matcher-actioner/lambda_local.py`.
* Create an attribute called `event` in that file.
* This is passed as the `event` argument to your lambda

eg.
```python
# hasher-matcher-actioner/lambda_local.py
import json
import uuid
from threatexchange.content_type.photo import PhotoContent
from hmalib.common.messages.submit import URLSubmissionMessage

content_id = str(uuid.uuid4())
print(f"Will use content_id: {content_id}")

# This attribute will get passed to the hasher lambda.
event = {
    "Records": [
        {
            "body": json.dumps(
                URLSubmissionMessage(
                    content_type=PhotoContent,
                    content_id=content_id,
                    url="https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_272x92dp.png",
                ).to_sqs_message()
            )
        }
    ]
}
```

## Running the API locally

This could not be simpler. 

```
$ python -m hmalib.scripts.cli.main run-api
```

or 
```
$ hmacli run-api
```

This will run the API on port 8080 on localhost.
