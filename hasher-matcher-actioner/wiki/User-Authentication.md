HMA uses AWS's Cognito to manage users. You can add / remove / change passwords for users via the cognito interface.

There are two ways to use authentication. A shared user pool or a dedicated user pool. 

A shared user pool needs to be setup only once and can be used across multiple HMA instances. You can setup multiple HMA instances to develop HMA or to test out new features. The shared pool does not get destroyed when you are tearing down HMA instances. So, you could save some admin time in managing accounts if you use a shared pool.

A dedicated user pool will be created if `use_shared_user_pool = false` inside terraform/variables.tf. This would destroy the user pool every time you do a `terraform destroy` and you'll need to setup user accounts again.

We recommend using a shared pool.

# Setting up a shared user pool

```shell
$ cd hasher-matcher-actioner/terraform/authentication-shared
$ cp terraform.tfvars.example terraform.tfvars
$ <edit> terraform.tfvars and add a sensible org name. This will only be used to name the user pool.
$ terraform init
$ terraform apply
$ terraform output
```

This will produce an output you can directly paste into your main terraform variables file at `hasher-matcher-actioner/terraform/terraform.tfvars`. 

So, if your terraform output looks like...

```
webapp_and_api_shared_user_pool_client_id = "6r0f5XXXXXXen6r6g5sd027pg6"
webapp_and_api_shared_user_pool_id = "us-east-1_86XXXXXXf"
```

Add the following to `terraform/terraform.tfvars`:
```hcl
use_shared_user_pool                      = true
webapp_and_api_shared_user_pool_client_id = "6r0f5XXXXXXen6r6g5sd027pg6"
webapp_and_api_shared_user_pool_id = "us-east-1_86XXXXXXf"
```

Note the extra `use_shared_user_pool` directive. That's it. Once you run terraform apply in the main terraform directory (`hasher-matcher-actioner/terraform`, it will now use the durable shared user pool. You can share the pool outputs with others in your team, or check it in to your configuration management system such that it is re-used across all HMA instances.

# Finding your user pool on the Cognito UI

Open the AWS Console. Use the search bar at the top to find Cognito. In the Cognito page, find "User pools" on the left sidebar. From the terraform output, you should know the user_pool_id. This will be something like "us-east-1_86XXXXXXf". In the list on the user pools page, find that pool and click its name.

# Adding a user via Cognito UI

In the users tab on the user pool page, click 'Create user'.

<img width="1405" alt="Screen Shot 2023-01-02 at 12 49 10" src="https://user-images.githubusercontent.com/217056/210277073-a6680925-98c3-4753-8355-d40fec2ae7a9.png">

Use the form to create a new user. Typically, AWS will send an email and ask the user to change their password.

# Removing a user via Cognito UI

In the users tab on the user pool page, find the user you are removing, click the checkbox to their left and click the 'Delete user' button.

<img width="1414" alt="Screen Shot 2023-01-02 at 12 53 20" src="https://user-images.githubusercontent.com/217056/210277380-2bd74b44-023d-4e8f-a89d-e27817fa1183.png">

# Managing users via Cognito API

If you want to automate creation / deletion of users from the cognito user pool from your own LDAP / SSO or other database, that will have to be done via the Cognito API. Unfortunately, this is out of scope for this wiki. Start with [boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cognito-idp.html) or get in touch with us via github issues.