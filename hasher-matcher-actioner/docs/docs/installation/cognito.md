---
id: cognito
title: Cognito User Pools for Authentication 
---

## Terraforming a User Pool

This starts after you have checked out a release of HMA and unzipped it. Check out this [section in the installation](installation/#checking-out-a-release) page.

```sh
$ cd ThreatExchange-HMA-v0.1.1/hasher-matcher-actioner/
$ cd terraform/authentication-shared/
$ cp terraform.tfvars.example terraform.tfvars
```

Open `terraform.tfvars` in an editor and set the value of `organization` to a short string that denotes your organization. It may use the name of the organization, or it may not. It is used as a part of the name for s3 buckets which are expected to be globally unique. Use a short, all-smallcase string without any hyphens or underscores.

### Create a shared pool

```sh
$ terraform init
$ terraform apply
```

### Get the values of the outputs

Run the following command.

```sh
$ terraform output
```

Copy the outputs of these and replace the values of `webapp_and_api_shared_user_pool_client_id` and `webapp_and_api_shared_user_pool_id` with the output of the command above.

If you do so, you must also set the value of `use_shared_user_pool` as true.

## Adding and editing users

Go to the AWS Console, to the [Cognito page](https://us-east-1.console.aws.amazon.com/cognito/home?region=us-east-1#) and click on the name of the user pool you created. Typically, this will be something like: `shared-hma-user-pool`. There will be a link on the left called 'Users & Groups'. You can use that to give more users access to HMA.
