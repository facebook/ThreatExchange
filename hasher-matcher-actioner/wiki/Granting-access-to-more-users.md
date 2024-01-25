Once you have setup the HMA instance inside your organization's AWS account, you'll almost certainly want to grant access to the UI to others so they can take it out for a spin.

# Opening the AWS Console

Once you are logged in to the AWS console, open the following link: https://console.aws.amazon.com/cognito/users/

This takes you to the user-pool management page. Once here, select your HMA User pool. You can get this name by running 

```shell
terraform output cognito_user_pool_name
``` 

in your terraform directory.

# Adding users

1. Select **Users and groups** under **General settings** in the sidebar.
2. Select **Create user** in the main panel, then follow the instructions.

![](https://github.com/facebook/ThreatExchange/blob/a9b29ae6ff3a8dca17f24942b6e014257e6cc6e1/hasher-matcher-actioner/docs/images/AWS_UI-Grant-users-cognito.png)

