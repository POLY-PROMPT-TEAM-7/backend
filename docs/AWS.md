 AWS Textract Setup
To enable AWS Textract features, configure an IAM user and an S3 bucket with the required permissions.
 Prerequisites
- An AWS IAM user for this service
- An S3 bucket for document storage and processing
- AWS credentials and configuration values available to the application runtime
 Required Configuration
Provide the following values to your runtime environment:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_DEFAULT_REGION`
- `S3_BUCKET_NAME`
 IAM Permissions
Attach the following two policies to the IAM user.
 Policy 1: S3 + Async Textract Access
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CreateBucketSetup",
      "Effect": "Allow",
      "Action": [
        "s3:CreateBucket",
        "s3:PutBucketPublicAccessBlock",
        "s3:PutBucketOwnershipControls"
      ],
      "Resource": "*"
    },
    {
      "Sid": "TextractBucketObjectAccess",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME/*"
    },
    {
      "Sid": "TextractAsyncApis",
      "Effect": "Allow",
      "Action": [
        "textract:StartDocumentTextDetection",
        "textract:GetDocumentTextDetection"
      ],
      "Resource": "*"
    }
  ]
}

Policy 2: Synchronous Textract Access
{
  Version: 2012-10-17,
  Statement: [
    {
      Effect: Allow,
      Action: [
        textract:DetectDocumentText,
        textract:AnalyzeDocument
      ],
      Resource: *
    }
  ]
}
Notes
- Replace YOUR-BUCKET-NAME with your actual S3 bucket name.
