# Deployment Configuration Template for Hackathon Team 14
# COPY THIS FILE and fill in your actual values
# NEVER commit the file with real credentials!

# AWS Configuration
AWS_REGION="us-east-1"
AWS_ACCOUNT_ID="YOUR_AWS_ACCOUNT_ID"  # Get with: aws sts get-caller-identity

# AWS Credentials (DO NOT COMMIT - Use AWS CLI configure instead!)
# Run: aws configure
# Then enter your credentials interactively

# S3 Buckets
SOURCE_BUCKET="your-team-bucket-name"
CATEGORIZED_BUCKET="your-categorized-logs-bucket"

# Log File
LOG_FILE="errors_json_native.log"

# CloudWatch
LOG_GROUP_NAME="/aws/incident-commander/critical-errors"

# Lambda Configuration
CRITICAL_LATENCY_MS="2000"
SPEED_MULTIPLIER="1.0"  # No artificial delays

# Bedrock Model
BEDROCK_MODEL_ID="anthropic.claude-3-5-sonnet-20241022-v2:0"

# DynamoDB
DEPLOYMENTS_TABLE="incident-deployments"

# IAM Roles (you'll need to create these)
LAMBDA_ROLE="arn:aws:iam::${AWS_ACCOUNT_ID}:role/lambda-execution-role"
LAMBDA_BEDROCK_ROLE="arn:aws:iam::${AWS_ACCOUNT_ID}:role/lambda-bedrock-role"
STEPFUNCTIONS_ROLE="arn:aws:iam::${AWS_ACCOUNT_ID}:role/stepfunctions-execution-role"

# NOTE: For actual deployment, use AWS IAM credentials configured via:
# aws configure
# This keeps credentials separate from your code!
