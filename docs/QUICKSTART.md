# Quick Start Guide for Hackathon Team 14

## ✅ Your Setup

**S3 Bucket:** `hackathon-team14-bucket`  
**Log File:** `errors_json_native.log` (already uploaded!)  
**Region:** `us-east-1`

---

## 🚀 Deploy in 3 Steps

### Step 1: Install AWS CLI (if not installed)

**Windows (PowerShell):**
```powershell
# Download installer
msiexec.exe /i https://awscli.amazonaws.com/AWSCLIV2.msi

# Configure AWS credentials
aws configure
# Enter your:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region: us-east-1
# - Default output format: json
```

### Step 2: Deploy Everything

```bash
# Make scripts executable (Git Bash on Windows)
chmod +x deploy.sh test-process-logs.sh trigger-investigation.sh

# Run deployment (this creates all AWS resources)
./deploy.sh
```

This will:
- ✅ Create CloudWatch Log Group
- ✅ Create DynamoDB table  
- ✅ Create IAM roles
- ✅ Deploy 5 Lambda functions
- ✅ Configure S3 trigger
- ✅ Create Step Functions workflow

**Deployment time:** ~3-5 minutes

---

### Step 3: Test It!

#### Option A: Test Log Processing

```bash
# Test the Lambda that reads from S3
./test-process-logs.sh
```

This will:
1. Invoke `incident-process-logs` Lambda
2. Read your `errors_json_native.log`
3. Filter errors with latency > 2000ms
4. Upload to CloudWatch Logs

**Expected:** ~100-200 critical errors uploaded

---

#### Option B: Run Full Investigation

```bash
# Trigger the full agent workflow
./trigger-investigation.sh
```

This will:
1. Start Step Functions execution
2. Run 3 agents in parallel:
   - **LogsAgent:** Analyzes WHAT happened
   - **MetricsAgent:** Analyzes HOW BAD
   - **DeployAgent:** Suggests FIX
3. **Commander:** Uses Claude to make final decision
4. Returns RCA report

**Expected:** JSON output with root cause analysis

---

## 📊 View Results

### CloudWatch Logs
```bash
# Watch logs being processed
aws logs tail /aws/incident-commander/critical-errors --follow
```

### Step Functions Console
https://console.aws.amazon.com/states/home?region=us-east-1#/statemachines

Look for: `incident-investigation`

---

## 🧪 Manual Testing (Without Scripts)

### Test Process Logs Lambda
```bash
aws lambda invoke \
  --function-name incident-process-logs \
  --payload '{"Records":[{"s3":{"bucket":{"name":"hackathon-team14-bucket"},"object":{"key":"errors_json_native.log"}}}]}' \
  response.json

cat response.json
```

### Trigger Investigation
```bash
aws stepfunctions start-execution \
  --state-machine-arn "arn:aws:states:us-east-1:YOUR_ACCOUNT_ID:stateMachine:incident-investigation" \
  --input '{
    "log_group": "/aws/incident-commander/critical-errors",
    "error_count": 120,
    "correlation": {"deployment_id": "deploy_1009", "percentage": 68.5}
  }'
```

---

## 🔍 Debugging

### Check Lambda Logs
```bash
# Process Logs
aws logs tail /aws/lambda/incident-process-logs --follow

# LogsAgent
aws logs tail /aws/lambda/incident-agent-logs --follow

# Commander
aws logs tail /aws/lambda/incident-commander --follow
```

### Check IAM Roles
```bash
# Verify roles exist
aws iam get-role --role-name lambda-execution-role
aws iam get-role --role-name lambda-bedrock-role
```

### Enable Bedrock Access
If you get Bedrock permission errors:
1. Go to AWS Console → Bedrock
2. Model access → Request access to Claude 3.5 Sonnet
3. Wait for approval (~instant for most accounts)

---

## 📝 Expected Output

### From test-process-logs.sh:
```json
{
  "statusCode": 200,
  "incident_id": "abc-123",
  "critical_error_count": 156,
  "log_group": "/aws/incident-commander/critical-errors",
  "trigger_investigation": true
}
```

### From trigger-investigation.sh:
```json
{
  "agent": "CommanderAgent",
  "root_cause": "ConnectionPoolExhaustedException due to config v40",
  "confidence": 0.92,
  "remediation_steps": [
    "Rollback deployment to previous config version",
    "Increase connection pool size from 10 to 50",
    "Add circuit breaker pattern"
  ],
  "evidence": {
    "logs": {...},
    "metrics": {...},
    "deploy": {...}
  }
}
```

---

## ⚠️ Common Issues

### Issue: "Role does not exist"
**Solution:** IAM roles take 10-15 seconds to propagate. Wait and retry.

### Issue: "Access Denied" for Bedrock
**Solution:** 
1. Go to Bedrock console
2. Enable Claude 3.5 Sonnet access
3. Redeploy Commander Lambda

### Issue: No logs in CloudWatch
**Solution:**
1. Check S3 trigger is configured: `aws s3api get-bucket-notification-configuration --bucket hackathon-team14-bucket`
2. Check Lambda permissions
3. Re-upload log file to trigger

---

## 🎯 For Hackathon Demo

1. **Show the log file:** `aws s3 ls s3://hackathon-team14-bucket/`
2. **Run investigation:** `./trigger-investigation.sh`
3. **Show Step Functions visual:** Open AWS Console → Step Functions
4. **Show final decision:** Read Commander output with LLM reasoning

**Talking Points for Judges:**
- ✅ Processes 2001 real error logs
- ✅ Filters to critical errors (>2000ms latency)
- ✅ Multi-agent analysis (Logs, Metrics, Deploy)
- ✅ LLM reasoning with Claude 3.5 Sonnet
- ✅ Auto-remediation suggestions
- ✅ All serverless (no infrastructure management)

---

## 📞 Need Help?

Check AWS CloudWatch Logs for detailed error messages:
```bash
aws logs tail /aws/lambda/incident-process-logs --follow --format short
```
