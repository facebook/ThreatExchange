# Quick install guide

Before you can use HMA, you need to deploy the system to your cloud. The installation will provision AWS resources necessary for running HMA and will provide you with a URL to the user interface.

## Step 0: Installing dependencies

HMA uses several packages that you must install before you can deploy HMA:

1. [aws cli](https://aws.amazon.com/cli/)
2. [jq cli](https://stedolan.github.io/jq/)
3. [terraform cli](https://www.terraform.io/downloads.html)
4. [npm](https://www.npmjs.com/get-npm)
5. [Docker](https://www.docker.com/)

## Step 1: Clone this repo
There are [several ways to clone a repo](https://docs.github.com/en/github/creating-cloning-and-archiving-repositories/cloning-a-repository-from-github/cloning-a-repository). The easiest is to, using the command line, navigate to the location you'd like to install HMA and run
```
$ git clone git@github.com:facebook/ThreatExchange.git
```

## Step 2: Create an AWS Elastic Container Registry
After logging in to your AWS account, navigate to https://console.aws.amazon.com/ecr/repositories and click "Create Repository". Create a new private repository named `hma-lambda-dev`

You will likely also want access to an permanent s3 bucket where you can remotely store your terraform state(s), the name of which you'll need as part of the next step.

## Step 3: Make a Docker image and deploy to HMA
First, make sure you have configured the aws cli by running `aws configure`. Then run the following commands:
```bash
$ cd ThreatExchange/hasher-matcher-actioner
$ make docker  # Will build the image from the local copy of the repo
$ make dev_create_instance
```
### Storing deployed state remotely
Note: unless you have created a `backend.tf` file you will be met with the following prompt:
```
terraform state will only be stored locally unless a backend.tf file is configured. 
Create a backend.tf? to use custom s3 bucket first: export TF_STATE_S3_BUCKET=bucket_name [y/N]
```
Anything other than 'y' will skip creating 'backend.tf'; entering 'y' will run `./scripts/write_backend_config.sh > terraform/backend.tf` which uses ENV values (or fb dev specific defaults) to populate a [backend configuration](https://www.terraform.io/docs/language/settings/backends/configuration.html). To overwrite the bucket used (likely necessary) run: `export TF_STATE_S3_BUCKET=<tf_state_bucket_name>` before `make dev_create_instance`

### ThreatExchange API Token

When running `dev_create_instance` you will be prompted for a ThreatExchange API Token. If you have the token provide it otherwise you can leave blank for now.

### Complete deployment
You will be prompted "Do you want to perform these actions?". Type "yes"

After Terraform creates the environment it will provide you with several outputs. One of these outputs should look like:
```
ui_url = "jeberl-example-org-hma-webapp.s3-website-us-east-1.amazonaws.com"
```
Navigating to the given URL will direct you to the HMA UI.

You may need to grant user access. To do that you can follow [this tutorial](Granting-access-to-more-users)

## Step 4: Connect To ThreatExchange
HMA is most useful when connected to [ThreatExchange](Glossary#fetcher). To connect HMA to ThreatExchange, you'll need an [Application](Glossary#fetcher) on the Facebook GraphAPI that has access to ThreatExchange. You can read more about ThreatExchange [here](https://developers.facebook.com/docs/threat-exchange/getting-started) and can create an Application [here](https://developers.facebook.com/programs/threatexchange)

Once you have an Application with ThreatExchange access you can [navigate here](https://developers.facebook.com/tools/accesstoken/) to get the App's AccessToken. Then run the following commands to add the access token to your `terrraform/terraform.tfvars` file and rebuild HMA:

```
$ echo 'te_api_token = "<YOUR-ACCESS-TOKEN-HERE>"' >> terraform/terraform.tfvars
$ make dev_create_instance
```

Once this is completed, you can navigate to the [ThreatExchange Settings Page](ThreatExchange-Settings-Page) and [press the "Sync" Button](ThreatExchange-Settings-Page#sync-button) to load the list of ThreatExchange [Datasets](Glossary#matcher) you have access to.

# Next Steps
Once you've installed HMA, you can check out our [tutorials](wiki#tutorials). A good place to start is with [Manually Submitting Photos to HMA](Tutorial:-Manually-Submitting-Photos-to-HMA) and [Getting notified when a Match occurs](https://github.com/facebook/ThreatExchange/wiki/Tutorial:-How-to-Notify-My-System-when-My-Content-Matches-a-Dataset)


