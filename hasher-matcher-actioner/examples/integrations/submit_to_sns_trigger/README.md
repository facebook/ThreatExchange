# Example SNS Submission Trigger

This is a python + terraform implementation that can be deployed to test HMA's sns submission flow. 
The point of these files are 1) to send submit request 2) validate an IAM policy for the SNS topic work outside of HMA.

## Setup

Just like the main terraform folder you will need `backend.tf` and `terraform.tfvars` files.

example `backend.tf`

```HCL
terraform {
  backend "s3" {
    bucket         = "<your-project>-tf-state"
    key            = "state/hasher-matcher-actioner-<prefix>-sns-submit-trigger-example.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-state-locking"
  }
}
```

example `terraform.tfvars`

```HCL
prefix = "<prefix>"
submit_topic_arn = "<value-from-tf-outputs-of-HMA>"
```

After running `terraform init` & `terraform apply` the lambda will be created for you.

## Usage: 
Testing is as simple as going to `console.aws.amazon.com/lambda/` finding the function created and submitting a test event in the following format:
```json
{
  "payload": {
    "content_id": "test-sns-object-submit-example-1",
    "content_type": "photo",
    "additional_fields": [
      "submitted_via_aws_console_test"
    ],
    "bucket_name": "<bucket-HMA-was-granted-permission-for>",
    "object_key": "<path-to-test-photo-in-bucket>"
  }
}
``` 
After seeing in the UI: "Execution result: succeeded" for the test event, go to the cloudwatch logs for the `_submit_event__handler` to confirm the submission was received and processed as expected by HMA. 
