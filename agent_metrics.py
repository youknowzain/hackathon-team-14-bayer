"""
Lambda Function: Metrics Agent (Telemetry Analyst)
Monitors CloudWatch Metrics for error rate spikes, latency degradation,
and system health anomalies.
"""

import json
import boto3
from datetime import datetime, timedelta
from statistics import mean

cloudwatch = boto3.client('cloudwatch')

def lambda_handler(event, context):
    """Analyze CloudWatch Metrics for anomalies."""
    
    try:
        # Extract parameters
        time_window = event.get('time_window', {})
        namespace = event.get('namespace', 'IncidentCommander')
        
        print(f"📊 MetricsAgent analyzing metrics...")
        print(f"   Namespace: {namespace}")
        print(f"   Time window: {time_window.get('start')} to {time_window.get('end')}")
        
        # Parse time window
        start_time = datetime.fromisoformat(time_window['start'])
        end_time = datetime.fromisoformat(time_window['end'])
        
        # Calculate baseline and incident periods
        baseline_start = start_time - timedelta(minutes=15)
        baseline_end = start_time
        incident_start = start_time
        incident_end = end_time
        
        # For demo purposes, we'll simulate metric data based on the log patterns
        # In production, this would query actual CloudWatch Metrics
        
        # Simulate baseline metrics (normal operation)
        baseline_error_rate = 5  # errors per minute
        baseline_p99_latency = 900  # ms
        
        # Simulate incident metrics (after deploy_1009)
        incident_error_rate = 35  # errors per minute
        incident_p99_latency = 2500  # ms
        
        # Calculate degradation
        error_rate_increase = (incident_error_rate / baseline_error_rate) - 1
        latency_increase = (incident_p99_latency / baseline_p99_latency)
        
        # Determine severity
        if error_rate_increase > 5 or latency_increase > 2:
            severity = "CRITICAL"
        elif error_rate_increase > 2 or latency_increase > 1.5:
            severity = "HIGH"
        else:
            severity = "MEDIUM"
        
        findings = {
            'agent': 'MetricsAgent',
            'findings': {
                'baseline': {
                    'error_rate_per_min': baseline_error_rate,
                    'p99_latency_ms': baseline_p99_latency,
                    'period': f"{baseline_start.isoformat()} to {baseline_end.isoformat()}"
                },
                'incident': {
                    'error_rate_per_min': incident_error_rate,
                    'p99_latency_ms': incident_p99_latency,
                    'period': f"{incident_start.isoformat()} to {incident_end.isoformat()}"
                },
                'degradation': {
                    'error_rate_increase': f"{error_rate_increase * 100:.0f}%",
                    'error_rate_multiplier': f"{incident_error_rate / baseline_error_rate:.1f}x",
                    'latency_increase': f"{(latency_increase - 1) * 100:.0f}%",
                    'latency_multiplier': f"{latency_increase:.1f}x"
                },
                'anomalies': [
                    f"Error rate spike of {error_rate_increase * 100:.0f}% detected",
                    f"P99 latency increased {latency_increase:.1f}x from baseline",
                    "Critical threshold breach at incident start time"
                ]
            },
            'severity': severity,
            'confidence': 0.92,
            'spike_detected_at': incident_start.isoformat()
        }
        
        print(f"✅ Metrics analysis complete")
        print(f"   Severity: {severity}")
        print(f"   Error rate increase: {error_rate_increase * 100:.0f}%")
        print(f"   Latency degradation: {latency_increase:.1f}x")
        
        return findings
        
    except Exception as e:
        print(f"❌ Error in MetricsAgent: {str(e)}")
        return {
            'agent': 'MetricsAgent',
            'error': str(e),
            'severity': 'UNKNOWN',
            'confidence': 0
        }
