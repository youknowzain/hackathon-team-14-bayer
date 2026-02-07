# Architecture Flow: Complete Lambda Pipeline

## 📊 The Correct Flow (YES, This is Right!)

```
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 1: Upload Log File                                            │
│  ────────────────────────                                           │
│  User uploads: errors_json_native.log                               │
│  Destination: s3://your-bucket/incidents/demo.log                   │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                │ S3 Event Trigger
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 2: Log Streamer Lambda (lambda_log_streamer.py)               │
│  ──────────────────────────────────────────────────────             │
│  • Reads file from S3                                               │
│  • Parses timestamps from JSON                                      │
│  • Simulates real-time by adding delays                             │
│  • Writes DIRECTLY to CloudWatch Logs ✅                            │
│                                                                      │
│  Output: CloudWatch Logs (one log group per service)                │
│    ├─ /aws/incident-commander/auth                                  │
│    ├─ /aws/incident-commander/payment                               │
│    ├─ /aws/incident-commander/inventory                             │
│    └─ /aws/incident-commander/checkout                              │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                │ CloudWatch Logs Subscription Filter
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 3: Log Segregator Lambda (lambda_log_segregator.py)           │
│  ──────────────────────────────────────────────────────             │
│  • Triggered by CloudWatch Logs (real-time!)                        │
│  • Reads latency_ms from each error log                             │
│  • Categories errors:                                                │
│    - Fast failures (<100ms)                                          │
│    - Medium latency (100-500ms)                                      │
│    - Slow failures (500-2000ms)                                      │
│    - Critical timeouts (>2000ms)                                     │
│  • Writes to S3 in organized folders                                 │
│                                                                      │
│  Output: s3://categorized-bucket/categorized/{category}/            │
└─────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────┐
│  STEP 4: Incident Detection                                         │
│  ───────────────────────                                            │
│  CloudWatch Metric Alarm detects high error rate                    │
│  Triggers: EventBridge → Step Functions                             │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 5: Agent Analysis (agent_logs_analyzer.py)                    │
│  ────────────────────────────────────────────────                   │
│  Step Functions invokes this Lambda                                 │
│                                                                      │
│  Agent makes API calls to:                                          │
│  ✅ CloudWatch Logs Insights API (query logs)                       │
│  ✅ S3 API (read categorized logs)                                  │
│                                                                      │
│  Returns findings to Step Functions                                 │
└─────────────────────────────────────────────────────────────────────┘
```

## ✅ Your Understanding is CORRECT!

**Q: "Can Lambda send directly to CloudWatch?"**
**A:** YES! ✅ Use `logs_client.put_log_events()` API

**Q: "Agent code will read from CloudWatch?"**
**A:** YES! ✅ Use CloudWatch Logs Insights API: `logs_client.start_query()`

**Q: "API calls happen in agent code?"**
**A:** YES! ✅ Agent Lambda calls:
- CloudWatch Logs Insights API (to query logs)
- S3 API (to read categorized logs)
- Returns analysis to Step Functions

---

## 🚀 How to Use These Files

### 1. Set Your S3 Bucket Name

Replace in Terraform or as environment variable:
```bash
export SOURCE_BUCKET="your-incident-logs-bucket"
export CATEGORIZED_BUCKET="your-categorized-logs-bucket"
```

### 2. Deploy Lambda Functions

```bash
# Package log streamer
cd /path/to/lambda_log_streamer
pip install -r requirements_lambda.txt -t .
zip -r lambda_log_streamer.zip .

# Package log segregator
cd /path/to/lambda_log_segregator
zip lambda_log_segregator.zip lambda_log_segregator.py

# Package agent
cd /path/to/agent_logs_analyzer
zip agent_logs_analyzer.zip agent_logs_analyzer.py

# Upload to AWS Lambda (via Terraform or AWS CLI)
```

### 3. Configure CloudWatch Log Groups

Create log groups (Terraform will do this):
```bash
aws logs create-log-group --log-group-name /aws/incident-commander/auth
aws logs create-log-group --log-group-name /aws/incident-commander/payment
aws logs create-log-group --log-group-name /aws/incident-commander/inventory
aws logs create-log-group --log-group-name /aws/incident-commander/checkout
aws logs create-log-group --log-group-name /aws/incident-commander/recommendation
```

### 4. Set Up CloudWatch Subscription Filter

Terraform will create this, or manually:
```bash
aws logs put-subscription-filter \
  --log-group-name "/aws/incident-commander/payment" \
  --filter-name "latency-segregation" \
  --filter-pattern '{ $.level = "ERROR" }' \
  --destination-arn "arn:aws:lambda:REGION:ACCOUNT:function:incident-log-segregator"
```

### 5. Upload Your Log File

```bash
aws s3 cp errors_json_native.log \
  s3://YOUR-BUCKET/incidents/demo-incident.log
```

This triggers the entire pipeline! 🎉

---

## 📝 Lambda Environment Variables

Set these in Terraform or AWS Console:

**lambda_log_streamer.py:**
- `SPEED_MULTIPLIER=10.0` (stream 10x faster)
- `LOG_GROUP_PREFIX=/aws/incident-commander`

**lambda_log_segregator.py:**
- `CATEGORIZED_LOGS_BUCKET=your-bucket-name`

**agent_logs_analyzer.py:**
- (Gets parameters from Step Functions event)

---

## 🔍 Testing Locally

```python
# Test log streamer
python lambda_log_streamer.py

# Simulate S3 event
event = {
    'Records': [{
        's3': {
            'bucket': {'name': 'your-bucket'},
            'object': {'key': 'incidents/demo.log'}
        }
    }]
}
```

Give me your S3 bucket endpoint when ready! 🚀
