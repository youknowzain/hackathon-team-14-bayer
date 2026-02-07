"""
Lambda Function: Process Logs
Reads error logs from S3, filters critical errors (latency >= 2000ms), 
and writes them to CloudWatch Logs for analysis.
"""

import json
import boto3
import os
from datetime import datetime

s3_client = boto3.client('s3')
logs_client = boto3.client('logs')
stepfunctions_client = boto3.client('stepfunctions')

# Environment variables
CRITICAL_LATENCY_MS = int(os.environ.get('CRITICAL_LATENCY_MS', '2000'))
LOG_GROUP_NAME = os.environ.get('LOG_GROUP_NAME', '/aws/incident-commander/critical-errors-team14')
STATE_MACHINE_ARN = os.environ.get('STATE_MACHINE_ARN', 'arn:aws:states:us-east-1:333813598365:stateMachine:incident-reasoning-orchestrator')

def lambda_handler(event, context):
    """Main handler for processing S3 log files."""
    
    try:
        # Get S3 bucket and key from event
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
        
        print(f"📥 Processing file: s3://{bucket}/{key}")
        
        # Download log file from S3
        response = s3_client.get_object(Bucket=bucket, Key=key)
        log_data = response['Body'].read().decode('utf-8')
        
        # Parse JSON logs
        all_errors = []
        for line in log_data.strip().split('\n'):
            try:
                all_errors.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        
        print(f"📊 Total errors in file: {len(all_errors)}")
        
        # Count critical errors for reporting
        critical_errors = [
            error for error in all_errors 
            if error.get('latency_ms', 0) >= CRITICAL_LATENCY_MS
        ]
        
        print(f"🚨 Critical errors (>= {CRITICAL_LATENCY_MS}ms): {len(critical_errors)}")
        print(f"📝 Writing ALL {len(all_errors)} logs to CloudWatch for analysis")
        
        # Ensure log group and stream exist
        log_stream_name = f"incident-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        try:
            logs_client.create_log_stream(
                logGroupName=LOG_GROUP_NAME,
                logStreamName=log_stream_name
            )
        except logs_client.exceptions.ResourceAlreadyExistsException:
            pass
        
        # Write ALL logs to CloudWatch (not just critical ones)
        # This allows agents to see baseline vs incident periods
        log_events = []
        for error in all_errors:
            log_events.append({
                'timestamp': int(datetime.fromisoformat(error['timestamp'].replace('Z', '')).timestamp() * 1000),
                'message': json.dumps(error)
            })
        
        # Sort by timestamp
        log_events.sort(key=lambda x: x['timestamp'])
        
        # CloudWatch has a 10,000 event limit per request
        for i in range(0, len(log_events), 10000):
            batch = log_events[i:i+10000]
            logs_client.put_log_events(
                logGroupName=LOG_GROUP_NAME,
                logStreamName=log_stream_name,
                logEvents=batch
            )
        
        print(f"✅ Wrote {len(all_errors)} logs to CloudWatch ({len(critical_errors)} critical)")
        
        # Auto-trigger investigation if critical errors exceed threshold
        trigger_investigation = len(critical_errors) > 50
        execution_arn = None
        
        if trigger_investigation:
            try:
                print(f"🚀 Auto-triggering investigation (>50 critical errors)")
                
                # Calculate time window from log timestamps
                timestamps = [datetime.fromisoformat(e['timestamp'].replace('Z', '')) for e in all_errors]
                start_time = min(timestamps).isoformat()
                end_time = max(timestamps).isoformat()
                
                # Start Step Functions execution
                response = stepfunctions_client.start_execution(
                    stateMachineArn=STATE_MACHINE_ARN,
                    name=f"{log_stream_name}-auto",
                    input=json.dumps({
                        'log_group': LOG_GROUP_NAME,
                        'time_window': {
                            'start': start_time,
                            'end': end_time
                        },
                        'error_count': len(critical_errors),
                        'auto_triggered': True
                    })
                )
                
                execution_arn = response['executionArn']
                print(f"✅ Investigation started: {execution_arn}")
                
            except Exception as trigger_error:
                print(f"⚠️  Failed to auto-trigger investigation: {str(trigger_error)}")
                print(f"   You can manually trigger using incident_id: {log_stream_name}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'incident_id': log_stream_name,
                'total_logs_written': len(all_errors),
                'critical_error_count': len(critical_errors),
                'log_group': LOG_GROUP_NAME,
                'log_stream': log_stream_name,
                'trigger_investigation': trigger_investigation,
                'execution_arn': execution_arn
            })
        }
        
    except Exception as e:
        print(f"❌ Error processing logs: {str(e)}")
        raise
