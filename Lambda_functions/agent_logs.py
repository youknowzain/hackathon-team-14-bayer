"""
Lambda Function: Logs Agent (Forensic Expert)
Deep-scans CloudWatch Logs to find error patterns, stack traces, 
and correlations between errors and deployments.
"""

import json
import boto3
import time
from collections import Counter

logs_client = boto3.client('logs')

def lambda_handler(event, context):
    """Analyze CloudWatch Logs for error patterns."""
    
    try:
        # Extract parameters from event
        log_group = event.get('log_group')
        time_window = event.get('time_window', {})
        
        print(f"🕵️ LogsAgent analyzing: {log_group}")
        print(f"   Time window: {time_window.get('start')} to {time_window.get('end')}")
        
        # Query CloudWatch Logs Insights
        query = """
        fields @timestamp, service, error_type, error_message, deployment_id, config_version, latency_ms
        | filter latency_ms >= 2000
        | sort @timestamp desc
        """
        
        # Start query
        response = logs_client.start_query(
            logGroupName=log_group,
            startTime=int(time.mktime(time.strptime(time_window['start'], '%Y-%m-%dT%H:%M:%S'))),
            endTime=int(time.mktime(time.strptime(time_window['end'], '%Y-%m-%dT%H:%M:%S'))),
            queryString=query
        )
        
        query_id = response['queryId']
        print(f"   Query ID: {query_id}")
        
        # Wait for query to complete
        max_attempts = 30
        for attempt in range(max_attempts):
            result = logs_client.get_query_results(queryId=query_id)
            
            if result['status'] == 'Complete':
                break
            
            time.sleep(1)
        
        # Parse results
        errors = []
        for result_row in result.get('results', []):
            error = {}
            for field in result_row:
                error[field['field']] = field['value']
            errors.append(error)
        
        print(f"   Found {len(errors)} critical errors")
        
        # Analyze patterns
        error_types = Counter([e.get('error_type', 'Unknown') for e in errors])
        deployments = Counter([e.get('deployment_id', 'Unknown') for e in errors])
        services = Counter([e.get('service', 'Unknown') for e in errors])
        
        # Find top error type
        top_error_type, top_error_count = error_types.most_common(1)[0] if error_types else ('None', 0)
        top_deployment, top_deploy_count = deployments.most_common(1)[0] if deployments else ('None', 0)
        
        # Calculate correlation
        correlation_percentage = (top_deploy_count / len(errors) * 100) if errors else 0
        confidence = min(correlation_percentage / 100, 0.95)
        
        findings = {
            'agent': 'LogsAgent',
            'findings': {
                'total_critical_errors': len(errors),
                'top_error': {
                    'type': top_error_type,
                    'count': top_error_count,
                    'percentage': (top_error_count / len(errors) * 100) if errors else 0
                },
                'deployment_correlation': {
                    'deployment_id': top_deployment,
                    'count': top_deploy_count,
                    'percentage': correlation_percentage
                },
                'affected_services': dict(services.most_common(3)),
                'error_distribution': dict(error_types)
            },
            'confidence': confidence,
            'recommendation': f'Investigate {top_deployment}' if correlation_percentage > 50 else 'No clear correlation'
        }
        
        print(f"✅ Analysis complete. Top error: {top_error_type} ({top_error_count})")
        print(f"   Correlation: {top_deployment} ({correlation_percentage:.1f}%)")
        
        return findings
        
    except Exception as e:
        print(f"❌ Error in LogsAgent: {str(e)}")
        return {
            'agent': 'LogsAgent',
            'error': str(e),
            'confidence': 0
        }
