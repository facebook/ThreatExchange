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

## Setting up Terraform

Before using terraform, you will need to provide some additional configuration, examples of which are provided in this folder using the same name, but with example suffixed to the end.

1. `terraform.tfvars`: In this file, you will want to define the values for the variables defined in [variables.tf](terraform/variables.tf). Only variables without defaults are required, though if you are setting up an environment for developing on the HMA prototype, you likely want to override the default `prefix` to allow having an isolated environment. You may want to set up a shared Cognito user pool for multiple developer environments to share. To do that, run `terraform apply` from `/authentication-shared` once (note it has its own terraform.tfvars) then use the outputs in the main `terraform.tfvars`. See the terraform docs on [input variables](https://www.terraform.io/docs/configuration/variables.html) for more information on providing variable values and overrides.

2. _(optional)_ `backend.tf`: This file is used for optionally defining a remote backend to store your terraform state. If you are working on development for the HMA prototype and are part of the facebook ThreatExchange team, it is highly suggested you use the configuration for this file in the internal wiki. That will enable state locking and remote state storage for your terraform environment.

## VS Code Devcontainers | Automated Development Environment 

If you are using [VS Code](https://code.visualstudio.com/), and we recommend you do, you can use the Devcontainer technology to get started real quick and have a great developer experience. 
1. [Windows Only] Sadly, the devcontainer will misbehave unless all the file endings are unix style (LF) instead of windows style (CRLF). You most likely checked out the repo with autocrlf set to "true", which means you have the wrong line endings. The fastest way to fix this is to simply re-clone the whole repository with autocrlf=input (though with more steps it's possible to fix it inplace).

```
$ OLD_CRLF="$(git config --get core.autocrlf)"  # Save your old value
$ git config --global core.autocrlf input
$ git clone https://github.com/facebook/ThreatExchange.git devcontainer-ThreatExchange # Or call it whatever you want
$ cd devcontainer-ThreatExchange
$ git config --local core.autocrlf input
$ git config --global core.autocrlf "$OLD_CRLF"
```
If we were smarter, we'd have the devcontainer built on a checkout of the repo, but this was faster to figure out than getting git configs in.

2. Download VS Code from [the VS Code website](https://code.visualstudio.com/).
   1. If you are a Meta employee (thanks for looking into contributing!), don't skip this step, this version is different than your pre-installed one. 

3. Install [Docker Desktop](https://www.docker.com/products/docker-desktop) on your computer. 

4. Install the [remote containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.vscode-remote-extensionpack)

    Create `.hma-cmdhist` directory in your home directory. Use `$ mkdir -p ~/.hma-cmdhist` or equivalent for your OS.

5. [Optional/Warning] You may need to tweak the devcontainer.json settings - to make specific changes depending on your operating system.
```
$ cd hasher-matcher-actioner/.devcontainer
$ vim devcontainer.json
```

6. Use `[Cmd]+[Shift]+[P]` inside VS Code and choose "Remote-Containers: Open folder in container ..." and navigate to your checkout of facebook/ThreatExchange, and open ./hasher-matcher-actioner/ (not ./hasher-matcher-actioner/.devcontainer).

The first time may take a while because images need to be built. Subsequently, opening the container will be blazing fast. 5-10 seconds on a 2019 MacBook Pro.

The devcontainer provides all the tools you need to build and hack on HMA. Including python, docker, make, and Typescript tooling.

### Common Errors and how to correct them

1. **Can't connect to docker...**
    > Got permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock: Get http://%2Fvar%2Frun%2Fdocker.sock/v1.24/images/json: dial unix /var/run/docker.sock: connect: permission denied

    Run `sudo chown $(whoami):developers /var/run/docker.sock` in a VS Code integrated terminal. (`[Cmd]+[Shift]+[P]` "Terminal: Create new integrated terminal...")


2. **Building webapp taking too long..**
    If you see sustained 100% CPU when running `npm install|start|build` within the webapp directory, you might need to provide more memory and CPU to the docker desktop app. We recommend atleast 4GB of RAM and 2CPUs.


3. **VPC Limits**
    Default AWS configuration for VPCs is 5. See [this](https://docs.aws.amazon.com/vpc/latest/userguide/amazon-vpc-limits.html). You will need to increase that quota if you encounter errors like
    ```
    Error: error creating EC2 VPC: VpcLimitExceeded: The maximum number of VPCs has been reached.
    ```

4. **git@github.com: Permission denied (publickey).**
    If you have not used git within the devcontainer for a while, an ssh cache gets invalidated. To refresh it, on your local computer, open a terminal and run `ssh git@github.com`. Then run any git command inside the devcontainer terminals.

## Building the Docker Lambda Image

The lambda functions defined for HMA use docker images. You will need to build and publish this docker image to a docker registry you own. eg. an AWS ECR repository.

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

## Working with an unpublished python-threatexchange version

We have built a script to make this more palatable.

If you want to use `python-threatexchange` from the parent directory. Your git checkout version, use 

```
$ ./scripts/set_threatexchange_source local
```

To switch back to a copy of `python-threatexchange` downloaded from pypi, run

```
$ ./scripts/set_threatexchange_source pypi
```

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

## Troubleshooting

### Default devcontainer.json
- Context:
    - You clone the `ThreatExchange` repo and open the `hasher-matcher-actioner/` directory in a VSCode remote container.
    - You select VSCode to use a preexisting `Dockerfile`
    - The VSCode console logs show
        ```bash
        [2022-01-24T14:14:49.974Z] /bin/sh: line 26: tar: command not found
        [2022-01-24T14:14:49.974Z] Exit code 127
        ```
- Cause: You did not create a `devcontainer.json` before opening the directory in the remote container. This caused VSCode to create a default `devcontainer.json` which points to the wrong `Dockerfile`.
- Resolution: This should no longer happen because the repo now has a configured `devcontainer.json`.

### Corrupted /vscode
- Context:
    - You clone the `ThreatExchange` repo and open the `hasher-matcher-actioner/` directory in a VSCode remote container.
    - You select VSCode to use a preexisting `Dockerfile`
    - The VSCode console logs show that it's stuck loading `userProfile`
- Cause: The VSCode plugin to open folder in remote docker containers uses the same `/vscode` volume for subsequent run. This volume can get corrupted if one of the attempts to open a folder remotely fails and leaves empty directories in the `/vscode` volume. Any subsequent attempt to open a file/folder in a remote container would get stuck trying to use the empty directories.
- Resolution: Delete the `/vscode` volume. You will have to stop any containers using the volume before you can delete the volume. A simple way is to close VSCode and run `docker system prune --all --volumes`
