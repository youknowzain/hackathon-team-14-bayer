"""
Lambda Function: Deploy Intelligence Agent (Historian)
Maps real-time errors against CI/CD deployments and configuration changes
to identify correlations and suggest rollback candidates.
"""

import json
import boto3
import os
from datetime import datetime, timedelta

dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    """Analyze deployment history for correlations."""
    
    try:
        # Extract parameters
        correlation_hint = event.get('correlation', {})
        time_window = event.get('time_window', {})
        
        deployment_id_hint = correlation_hint.get('deployment_id')
        
        print(f"📜 DeployAgent analyzing deployment history...")
        print(f"   Correlation hint: {deployment_id_hint}")
        print(f"   Time window: {time_window.get('start')} to {time_window.get('end')}")
        
        # For demo purposes, we'll use mock deployment data
        # In production, this would query DynamoDB
        
        # Mock deployment data
        deployments = [
            {
                'deployment_id': 'deploy_1009',
                'timestamp': '2026-02-06T10:00:00Z',
                'service': 'checkout-service',
                'config_version': 'v40',
                'changes': [
                    'Reduced connection pool size from 50 to 10',
                    'Updated Redis cache TTL to 300s',
                    'Enabled query result caching'
                ],
                'deployed_by': 'cicd-pipeline',
                'status': 'DEPLOYED'
            },
            {
                'deployment_id': 'deploy_1008',
                'timestamp': '2026-02-06T09:30:00Z',
                'service': 'payment-service',
                'config_version': 'v39',
                'changes': [
                    'Updated payment gateway timeout to 30s'
                ],
                'deployed_by': 'cicd-pipeline',
                'status': 'DEPLOYED'
            },
            {
                'deployment_id': 'deploy_1007',
                'timestamp': '2026-02-06T08:00:00Z',
                'service': 'auth-service',
                'config_version': 'v38',
                'changes': [
                    'Updated JWT expiration to 24h'
                ],
                'deployed_by': 'cicd-pipeline',
                'status': 'DEPLOYED'
            }
        ]
        
        # Find the deployment mentioned in correlation hint
        target_deployment = None
        for deploy in deployments:
            if deploy['deployment_id'] == deployment_id_hint:
                target_deployment = deploy
                break
        
        if not target_deployment:
            print(f"⚠️  No deployment found for {deployment_id_hint}")
            target_deployment = deployments[0]  # Default to most recent
        
        # Calculate time difference
        deploy_time = datetime.fromisoformat(target_deployment['timestamp'].replace('Z', ''))
        incident_time = datetime.fromisoformat(time_window['start'])
        time_diff_minutes = int((incident_time - deploy_time).total_seconds() / 60)
        
        # Analyze the deployment for suspicious changes
        suspicious_changes = []
        for change in target_deployment['changes']:
            if 'pool' in change.lower() or 'connection' in change.lower():
                suspicious_changes.append({
                    'change': change,
                    'risk_level': 'HIGH',
                    'reason': 'Connection pool modifications can cause resource exhaustion'
                })
            elif 'timeout' in change.lower():
                suspicious_changes.append({
                    'change': change,
                    'risk_level': 'MEDIUM',
                    'reason': 'Timeout changes can affect error rates'
                })
        
        # Determine confidence based on timing and correlation
        if time_diff_minutes >= 0 and time_diff_minutes <= 30:
            confidence = 0.95
            correlation_strong = True
        elif time_diff_minutes > 30 and time_diff_minutes <= 60:
            confidence = 0.70
            correlation_strong = False
        else:
            confidence = 0.40
            correlation_strong = False
        
        findings = {
            'agent': 'DeployAgent',
            'findings': {
                'target_deployment': target_deployment,
                'correlation': {
                    'deployment_id': target_deployment['deployment_id'],
                    'config_version': target_deployment['config_version'],
                    'time_before_incident_minutes': time_diff_minutes,
                    'correlation_strength': 'STRONG' if correlation_strong else 'WEAK',
                    'confidence': confidence
                },
                'suspicious_changes': suspicious_changes,
                'recent_deployments': deployments[:3]
            },
            'root_cause_hypothesis': 'Connection pool reduction in deploy_1009' if suspicious_changes else 'Unknown',
            'recommended_action': f"ROLLBACK deploy_1009 to previous config (v39)" if confidence > 0.8 else "Investigate further",
            'confidence': confidence
        }
        
        print(f"✅ Deployment analysis complete")
        print(f"   Target: {target_deployment['deployment_id']}")
        print(f"   Time before incident: {time_diff_minutes} minutes")
        print(f"   Confidence: {confidence:.0%}")
        
        return findings
        
    except Exception as e:
        print(f"❌ Error in DeployAgent: {str(e)}")
        return {
            'agent': 'DeployAgent',
            'error': str(e),
            'confidence': 0
        }
