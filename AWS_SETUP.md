# AWS Setup Guide

This document provides instructions for setting up AWS resources required by the document processing feature.

## Prerequisites

- AWS Account with appropriate permissions
- AWS CLI installed and configured (or environment variables set)

## AWS Services Required

The document processing feature uses **Amazon Textract** for extracting text from documents.

## Step 1: Create AWS Account

If you don't have an AWS account:
1. Go to [aws.amazon.com](https://aws.amazon.com)
2. Click "Create an AWS Account"
3. Follow the signup process
4. Verify your email address

## Step 2: Configure AWS Credentials

You have two options for configuring AWS credentials:

### Option A: AWS CLI (Recommended)

1. Install AWS CLI:
   ```bash
   pip install awscli
   ```

2. Configure your credentials:
   ```bash
   aws configure
   ```

3. Enter your credentials when prompted:
   - AWS Access Key ID: `YOUR_ACCESS_KEY_ID`
   - AWS Secret Access Key: `YOUR_SECRET_ACCESS_KEY`
   - Default region name: `us-east-1` (or your preferred region)
   - Default output format: `json`

### Option B: Environment Variables

Set the following environment variables:

```bash
export AWS_ACCESS_KEY_ID="your-access-key-id"
export AWS_SECRET_ACCESS_KEY="your-secret-access-key"
export AWS_DEFAULT_REGION="us-east-1"
```

For persistence, add these to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.)

## Step 3: Create IAM User with Textract Permissions

For security, create an IAM user with minimal required permissions:

1. Go to AWS Console → IAM → Users → "Create user"
2. Enter username: `document-processor`
3. Select "Attach policies directly"
4. Create and attach the following inline policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "textract:DetectDocumentText",
        "textract:AnalyzeDocument"
      ],
      "Resource": "*"
    }
  ]
}
```

5. Save the user and create Access Key (Security credentials → Create access key)
6. **Important**: Save the Access Key ID and Secret Access Key - you won't see them again

## Step 4: Verify Setup

Test your AWS configuration:

```bash
# Test AWS CLI
aws sts get-caller-identity

# Test Textract access (requires a test document)
aws textract detect-document-text \
  --document-bucket your-bucket-name \
  --document-name test.pdf \
  --region us-east-1
```

## Step 5: Region Selection

Amazon Textract is available in the following regions:
- us-east-1 (N. Virginia)
- us-east-2 (Ohio)
- us-west-1 (N. California)
- us-west-2 (Oregon)
- eu-west-1 (Ireland)
- eu-central-1 (Frankfurt)
- ap-northeast-1 (Tokyo)
- ap-northeast-2 (Seoul)
- ap-southeast-1 (Singapore)
- ap-southeast-2 (Sydney)
- ap-south-1 (Mumbai)

Set your preferred region via environment variable or AWS CLI configuration.

## Step 6: Local Environment Setup

Add to your `.env` file or environment:

```bash
# AWS Configuration
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
AWS_DEFAULT_REGION=us-east-1
```

For the FastAPI backend, create a `.env` file in the `backend/` directory:

```bash
# AWS Configuration
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
AWS_DEFAULT_REGION=us-east-1
```

## Cost Considerations

Amazon Textract pricing (as of 2024):

| Operation | Price |
|-----------|-------|
| DetectDocumentText | $1.50 per 1,000 pages |
| AnalyzeDocument | $15.00 per 1,000 pages |

**Free Tier**: AWS offers 1,000 pages of text detection and 100 pages of form/data extraction per month for the first 3 months.

For detailed pricing, visit: https://aws.amazon.com/textract/pricing/

## Troubleshooting

### Error: "NoCredentialsError"

**Cause**: AWS credentials not configured properly.

**Solution**:
1. Verify `aws configure` was run correctly
2. Check environment variables are set
3. Ensure credentials file at `~/.aws/credentials` exists

### Error: "AccessDenied"

**Cause**: IAM user lacks Textract permissions.

**Solution**:
1. Verify IAM user policy includes `textract:*` permissions
2. Check region matches where Textract is available

### Error: "botocore.exceptions.NoRegionError"

**Cause**: AWS region not specified.

**Solution**:
```bash
export AWS_DEFAULT_REGION=us-east-1
```

### Error: "ValidationException: Document is not in a supported format"

**Cause**: Unsupported file type.

**Solution**: The API only supports `.pdf`, `.pptx`, `.docx`, and `.txt` files (max 10MB).

## Security Best Practices

1. **Never commit AWS credentials to version control**
2. Use IAM users with least-privilege policies
3. Rotate access keys regularly
4. Use AWS Secrets Manager or Parameter Store for production deployments
5. Enable MFA on your AWS root account
6. Set up billing alerts to monitor Textract usage

## Production Deployment

For production deployments:

1. Use AWS IAM Roles instead of access keys when running on AWS infrastructure (EC2, ECS, Lambda)
2. Store credentials in AWS Secrets Manager
3. Implement retry logic for transient AWS failures
4. Set up CloudWatch alarms for Textract API usage and errors
5. Consider using AWS CDK or Terraform for infrastructure as code

## Testing Without AWS

The test suite includes mocked Textract responses, allowing you to run tests without AWS credentials:

```bash
cd backend
pytest tests/ -v
```

However, to run integration tests or use the API endpoint with real documents, AWS credentials are required.

## Next Steps

After completing AWS setup:

1. Verify credentials are loaded: Run `aws sts get-caller-identity`
2. Test the FastAPI endpoint with a real document
3. Monitor AWS CloudWatch for Textract usage metrics
4. Set up billing alerts to track costs

## Additional Resources

- [Amazon Textract Documentation](https://docs.aws.amazon.com/textract/)
- [Boto3 Textract Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/textract.html)
- [AWS IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [AWS Security Best Practices](https://docs.aws.amazon.com/general/latest/gr/aws-security-best-practices.html)
