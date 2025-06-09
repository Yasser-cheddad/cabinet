#!/usr/bin/env python
"""
AWS deployment helper script for Cabinet Medicale backend.
This script helps with setting up AWS resources for the application.
"""
import os
import sys
import argparse
import boto3
import json
from botocore.exceptions import ClientError

def create_s3_bucket(bucket_name, region=None):
    """Create an S3 bucket for static files and media storage."""
    try:
        if region is None:
            s3_client = boto3.client('s3')
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            s3_client = boto3.client('s3', region_name=region)
            location = {'LocationConstraint': region}
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration=location
            )
        
        # Set bucket policy to allow public read access
        bucket_policy = {
            'Version': '2012-10-17',
            'Statement': [{
                'Sid': 'PublicReadGetObject',
                'Effect': 'Allow',
                'Principal': '*',
                'Action': ['s3:GetObject'],
                'Resource': [f'arn:aws:s3:::{bucket_name}/*']
            }]
        }
        
        # Convert the policy to JSON
        bucket_policy = json.dumps(bucket_policy)
        
        # Set the bucket policy
        s3_client.put_bucket_policy(Bucket=bucket_name, Policy=bucket_policy)
        
        print(f"✅ Created S3 bucket: {bucket_name}")
        return True
    except ClientError as e:
        print(f"❌ Error creating S3 bucket: {e}")
        return False

def configure_ses(domain, region=None):
    """Configure Amazon SES for sending emails."""
    try:
        if region is None:
            ses_client = boto3.client('ses')
        else:
            ses_client = boto3.client('ses', region_name=region)
        
        # Verify domain identity
        response = ses_client.verify_domain_identity(Domain=domain)
        token = response['VerificationToken']
        
        print(f"✅ Domain verification initiated for: {domain}")
        print(f"⚠️ Create a TXT record with the following value: {token}")
        print(f"⚠️ DNS record name: _amazonses.{domain}")
        print("⚠️ After adding this DNS record, it may take up to 72 hours for verification to complete.")
        
        # Check if DKIM is already configured
        try:
            dkim_response = ses_client.get_identity_dkim_attributes(Identities=[domain])
            if domain in dkim_response['DkimAttributes'] and dkim_response['DkimAttributes'][domain]['DkimEnabled']:
                print(f"✅ DKIM is already enabled for {domain}")
            else:
                # Enable DKIM for the domain
                ses_client.set_identity_dkim_enabled(Identity=domain, DkimEnabled=True)
                dkim_tokens = ses_client.verify_domain_dkim(Domain=domain)['DkimTokens']
                
                print(f"✅ DKIM configuration initiated for: {domain}")
                print("⚠️ Create the following CNAME records:")
                for token in dkim_tokens:
                    print(f"⚠️ Name: {token}._domainkey.{domain}")
                    print(f"⚠️ Value: {token}.dkim.amazonses.com")
                print("⚠️ After adding these DNS records, it may take up to 72 hours for verification to complete.")
        except ClientError as e:
            print(f"❌ Error configuring DKIM: {e}")
        
        return True
    except ClientError as e:
        print(f"❌ Error configuring SES: {e}")
        return False

def create_iam_user(username, region=None):
    """Create an IAM user with appropriate permissions for S3 and SES."""
    try:
        if region is None:
            iam_client = boto3.client('iam')
        else:
            iam_client = boto3.client('iam', region_name=region)
        
        # Create user
        try:
            iam_client.create_user(UserName=username)
            print(f"✅ Created IAM user: {username}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'EntityAlreadyExists':
                print(f"⚠️ IAM user {username} already exists")
            else:
                raise
        
        # Create policy for S3 and SES
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:PutObject",
                        "s3:GetObject",
                        "s3:DeleteObject",
                        "s3:ListBucket"
                    ],
                    "Resource": [
                        "arn:aws:s3:::*/*",
                        "arn:aws:s3:::*"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "ses:SendEmail",
                        "ses:SendRawEmail"
                    ],
                    "Resource": "*"
                }
            ]
        }
        
        policy_name = f"{username}-policy"
        
        try:
            response = iam_client.create_policy(
                PolicyName=policy_name,
                PolicyDocument=json.dumps(policy_document)
            )
            policy_arn = response['Policy']['Arn']
            print(f"✅ Created policy: {policy_name}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'EntityAlreadyExists':
                print(f"⚠️ Policy {policy_name} already exists")
                # Get the policy ARN
                account_id = boto3.client('sts').get_caller_identity().get('Account')
                policy_arn = f"arn:aws:iam::{account_id}:policy/{policy_name}"
            else:
                raise
        
        # Attach policy to user
        try:
            iam_client.attach_user_policy(
                UserName=username,
                PolicyArn=policy_arn
            )
            print(f"✅ Attached policy to user: {username}")
        except ClientError as e:
            print(f"❌ Error attaching policy to user: {e}")
        
        # Create access key
        try:
            response = iam_client.create_access_key(UserName=username)
            access_key = response['AccessKey']
            print("\n===== IMPORTANT: SAVE THESE CREDENTIALS =====")
            print(f"Access Key ID: {access_key['AccessKeyId']}")
            print(f"Secret Access Key: {access_key['SecretAccessKey']}")
            print("============================================\n")
            print("⚠️ This is the only time the secret access key will be shown.")
            print("⚠️ Add these credentials to your .env file as:")
            print(f"AWS_ACCESS_KEY_ID={access_key['AccessKeyId']}")
            print(f"AWS_SECRET_ACCESS_KEY={access_key['SecretAccessKey']}")
            if region:
                print(f"AWS_S3_REGION_NAME={region}")
                print(f"AWS_SES_REGION_NAME={region}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'LimitExceeded':
                print("⚠️ This user already has the maximum number of access keys")
                print("⚠️ You'll need to delete an existing key before creating a new one")
                print("⚠️ Or use existing credentials for this user")
            else:
                print(f"❌ Error creating access key: {e}")
        
        return True
    except ClientError as e:
        print(f"❌ Error creating IAM user: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Set up AWS resources for Cabinet Medicale backend')
    parser.add_argument('--region', default='us-east-1', help='AWS region (default: us-east-1)')
    parser.add_argument('--bucket-name', required=True, help='Name for the S3 bucket')
    parser.add_argument('--domain', required=True, help='Domain name for SES configuration')
    parser.add_argument('--iam-user', default='cabinet-medicale-app', help='Name for the IAM user')
    
    args = parser.parse_args()
    
    print(f"Setting up AWS resources in region: {args.region}")
    
    # Create S3 bucket
    if create_s3_bucket(args.bucket_name, args.region):
        print("\n⚠️ Add these settings to your .env file:")
        print("USE_S3=True")
        print(f"AWS_STORAGE_BUCKET_NAME={args.bucket_name}")
        print(f"AWS_S3_REGION_NAME={args.region}")
    
    # Configure SES
    if configure_ses(args.domain, args.region):
        print("\n⚠️ Add these settings to your .env file:")
        print("USE_SES=True")
        print(f"AWS_SES_REGION_NAME={args.region}")
    
    # Create IAM user
    create_iam_user(args.iam_user, args.region)
    
    print("\n✅ AWS setup complete!")
    print("⚠️ Remember to update your .env file with the settings mentioned above")
    print("⚠️ And verify your domain in SES before sending emails")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
