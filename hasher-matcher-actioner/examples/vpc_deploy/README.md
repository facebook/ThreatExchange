# Example VPC Deployment

In order to test VPC support for HMA, a VPC and moreover a way to invoke the API is needed. These terraform files get you close to that point but require a few extra steps to fully test.

## Setup

Just like the main terraform folder you will need `backend.tf` and `terraform.tfvars` files.

example `backend.tf`

```HCL
terraform {
  backend "s3" {
    bucket         = "<your-project>-tf-state"
    key            = "state/hasher-matcher-actioner-<prefix>-vpc-example.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-state-locking"
  }
}
```

example `terraform.tfvars`

```HCL
prefix = "<prefix>"
```

Before deploying you will need to follow the steps [here](https://docs.aws.amazon.com/vpn/latest/clientvpn-admin/client-authentication.html#mutual) to create the certificates used by the VPN.

Then after running `terraform init` & `terraform apply` the necessary pieces should be created for you then [export and edit the config file](https://docs.aws.amazon.com/vpn/latest/clientvpn-admin/cvpn-working-endpoints.html#cvpn-working-endpoint-export) to add the profile to the [AWS Client VPN](https://aws.amazon.com/vpn/client-vpn-download/)

## Passing value to HMA

The outputs of apply, specifically `vpc_id`, `priv_subnets`, and `security_group_id` can then be given in the `terraform.tfvars` of the main module as `vpc_id`, `vpc_subnets`, and `security_groups` respectively with `security_groups` being passed as a one element list.

You should then be able to test deploy HMA behind a VPC and only access the API's invoke URL when connected to the VPN created in this example.
