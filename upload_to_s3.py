#!/usr/bin/env python3
"""
Simple script to upload error log file to S3.
Run: python upload_to_s3.py
"""

import boto3
import os

# Configuration (matches your config.sh)
S3_BUCKET = 'hackathon-team14-bucket'
LOG_FILE = 'errors_json_native.log'
AWS_REGION = 'us-east-1'

def upload_to_s3():
    """Upload log file to S3."""
    
    # Check if file exists
    if not os.path.exists(LOG_FILE):
        print(f"❌ Error: {LOG_FILE} not found!")
        return
    
    # Create S3 client
    s3 = boto3.client('s3', region_name=AWS_REGION)
    
    try:
        print(f"📤 Uploading {LOG_FILE} to s3://{S3_BUCKET}/")
        
        # Upload file
        s3.upload_file(
            Filename=LOG_FILE,
            Bucket=S3_BUCKET,
            Key=LOG_FILE
        )
        
        print(f"✅ Upload successful!")
        print(f"   Location: s3://{S3_BUCKET}/{LOG_FILE}")
        print(f"\n💡 This will trigger the Lambda function: incident-process-logs")
        
    except s3.exceptions.NoSuchBucket:
        print(f"❌ Error: Bucket {S3_BUCKET} does not exist!")
        print(f"   Create it with: aws s3 mb s3://{S3_BUCKET} --region {AWS_REGION}")
        
    except Exception as e:
        print(f"❌ Error uploading: {str(e)}")

if __name__ == '__main__':
    print("🚀 S3 Upload Script")
    print("=" * 60)
    upload_to_s3()
