# Quick install guide

This guide allows you to install a `released` version of HMA without any customizations to the source code. 

## Pre-requisites

1. [Docker](https://www.docker.com/)
2. [Terraform cli](https://www.terraform.io/)
3. [aws cli](https://aws.amazon.com/cli/) Configured
4. [jq](https://stedolan.github.io/jq/)
## Mirror HMA Releases to your private ECR repository

HMA uses docker images to deploy code to your infrastructure. This requires the images to be available within your private cloud account. We use AWS ECR [Elastic Container Registry](https://aws.amazon.com/ecr/).

HMA Releases are deployed to a public ECR repository [https://gallery.ecr.aws/l5b3f6x2/hma/releases](https://gallery.ecr.aws/l5b3f6x2/hma/releases).

### Creating a private ECR repository mirroring our releases

This assumes your AWS access keys allow you to create an ECR Repository.

```shell
$ aws ecr create-repository --repository-name hma-releases-mirror
```

### Copying a release to your private ECR repository

```shell
$ export HMA_RELEASE="v0.1.1"

# Copy image to your computer
$ docker pull "public.ecr.aws/l5b3f6x2/hma/releases:$HMA_RELEASE"

# Prepare environment variables to push image to your mirror
$ ECR_PASSWORD="$(aws ecr get-login-password --region us-east-1)"
$ ECR_REPOSITORY_URI="$(aws ecr describe-repositories --repository-names hma-releases-mirror | jq -r '.repositories[0].repositoryUri')"
$ AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Actually push image to your mirror
$ echo "$ECS_PASSWORD" | docker login --username AWS --password-stdin "$ECR_REPOSITORY_URI"
$ docker tag "public.ecr.aws/l5b3f6x2/hma/releases:$HMA_RELEASE" "$ECR_REPOSITORY_URI:$HMA_RELEASE"
$ docker push "$ECR_REPOSITORY_URI:$HMA_RELEASE"
```

## Checking out a release

Go to the Github [releases page](https://github.com/facebook/ThreatExchange/releases) for HMA. Click on the "Assets" for the latest release you see. Download the Source Code in `.zip` or `.tar.gz`. 

```shell
$ unzip ThreatExchange-HMA-v0.1.1.zip
```

## Optionally, setup authentication using cognito

If you do not use cognito for authentication, you'll need to set things up. Follow along in [this guide](cognito) to setting up authentication using cognito.

## Configuring terraform 

```sh
$ cd ThreatExchange-HMA-v0.1.1/hasher-matcher-actioner/
$ cp terraform/terraform.tfvars.example terraform/terraform.tfvars
$ aws ecr describe-repositories --repository-names hma-releases-mirror | jq -r '.repositories[0].repositoryUri'
<some long number>.dkr.ecr.us-east-1.amazonaws.com/hma-releases-mirror
```

### `hma_lambda_docker_uri`

Copy the output of the last command above. Open `terraform/terraform.tfvars` in an editor. Edit the value of `hma_lambda_docker_uri` and paste the output you copied above.

### `organization` 

Use a short string that denotes your organization. It may use the name of the organization, or it may not. It is used as a part of the name for s3 buckets which are expected to be globally unique. Use a short, all-smallcase string without any hyphens or underscores.

### `prefix`

We typically use our usernames or an environment name like `dev`, `test` or `prod`. Use a short, all-smallcase string without any hyphens or underscores.

## Terraforming HMA

Now we get to the fun bits. Run the following commands:

```sh
$ cd hasher-matcher-actioner
$ terraform -chdir=terraform init
$ terraform -chdir=terraform -out=tfplan plan
$ terraform -chdir=terraform apply -input=false tfplan
```

This will output a bunch of key-value pairs.

Visit the value of `ui_url` and find the UI for your HMA instance!