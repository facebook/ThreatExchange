Let's say you have an s3 bucket that contains images stored on your AWS account. Whenever an image is uploaded to the bucket, you want to send it directly to HMA for Hashing, Matching, and Actioning. Rather than writing custom code, triggers, and lambdas to set this up, you can configure automatic uploads with a simple terraform command. 

Let's say you have a bucket in s3 with name `my-separate-aws-bucket` and ARN `arn:aws:s3:::my-separate-aws-bucket`. Add the following to your `terraform.tfvars` file: 

```
partner_image_buckets = [{
    "name": "my-separate-aws-bucket", 
    "arn" : "arn:aws:s3:::my-separate-aws-bucket",
    "params" : {}
}]
```

Then run `cd hasher-matcher-actioner/terraform &&  terraform apply`

Additionally, you can filter uploads to be only those files in a specific "folder" of the bucket, or with a specific extension, using the 
"prefix" and "suffix" parameters respectively. For example. if you have an `images/important/` nested directory in your bucket and you only want to upload jpg images to HMA you could set params as follows:

```
partner_image_buckets = [{
    ...
    "params" : {
        "prefix" : "images/important/"
        "suffix" : ".jpg"
    }
}]
```

If you upload content from s3 buckets in this manner, ContentIDs will be generated automatically from the bucket and key. Specifically, if you upload a photo with file name `xkcd.jpg` to the `images/important/` directory of bucket `my-separate-aws-bucket`, the content ID will be:

`my-separate-aws-bucket:images.important.xkcd.jpg`

Because ContentIDs are unique across HMA, and the above string could be submitted as a ContentID for submissions via the UI or API, if you are using partner bucket uploads in prod, we recommend only submitting content via this method unless you are absolutely confident you wont cause collisions.


Note: To enable automatic Bucket Uploads, you will have to give HMA permission to read objects (`s3:GetObject`) from the bucket. Terraform will attempt to grant HMA the necessary permissions when you run `terraform apply`. Current behavior is to grant `GetObject` permissions to the entire bucket, even if a prefix is being used. This could eventually be restricted further. Feel free to reach out to the HMA team for help with your specific use-case.