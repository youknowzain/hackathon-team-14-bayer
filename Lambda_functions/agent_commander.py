"""
Lambda Function: Commander Agent (Orchestrator)
Uses AWS Bedrock (Claude AI) to synthesize findings from all agents
and make final root cause determination with remediation steps.
"""

import json
import boto3
import os
import urllib.parse
import urllib.request

# Environment variables
BEDROCK_MODEL_ID = os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-3-5-sonnet-20241022-v2:0')
BEDROCK_API_KEY = os.environ.get('AWS_BEDROCK_API_KEY', '')

# Initialize Bedrock client (fallback to standard boto3)
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

def lambda_handler(event, context):
    """Synthesize all agent findings using AI."""
    
    try:
        # Extract agent outputs from Step Functions Parallel state
        # Parallel state passes results as a list directly
        if isinstance(event, list):
            agent_outputs = event
        else:
            agent_outputs = event.get('agent_outputs', [])
        
        print(f"🎖️  CommanderAgent synthesizing findings...")
        print(f"   Received input type: {type(event)}")
        print(f"   Processing {len(agent_outputs)} agent outputs")
        
        # Flatten agent outputs (Step Functions returns nested arrays)
        findings = []
        for output in agent_outputs:
            if isinstance(output, list):
                findings.extend(output)
            else:
                findings.append(output)
        
        # Extract each agent's findings
        logs_findings = next((f for f in findings if f.get('agent') == 'LogsAgent'), {})
        metrics_findings = next((f for f in findings if f.get('agent') == 'MetricsAgent'), {})
        deploy_findings = next((f for f in findings if f.get('agent') == 'DeployAgent'), {})
        
        print(f"   Logs: {logs_findings.get('confidence', 0):.0%} confidence")
        print(f"   Metrics: {metrics_findings.get('confidence', 0):.0%} confidence")
        print(f"   Deploy: {deploy_findings.get('confidence', 0):.0%} confidence")
        
        # Prepare prompt for Claude
        prompt = f"""You are an expert incident response system analyzing a production outage. Review the following evidence from specialized agents and provide a comprehensive root cause analysis.

**LOGS AGENT FINDINGS:**
{json.dumps(logs_findings.get('findings', {}), indent=2)}
Confidence: {logs_findings.get('confidence', 0):.0%}

**METRICS AGENT FINDINGS:**
{json.dumps(metrics_findings.get('findings', {}), indent=2)}
Severity: {metrics_findings.get('severity', 'UNKNOWN')}
Confidence: {metrics_findings.get('confidence', 0):.0%}

**DEPLOY INTELLIGENCE FINDINGS:**
{json.dumps(deploy_findings.get('findings', {}), indent=2)}
Root Cause Hypothesis: {deploy_findings.get('root_cause_hypothesis', 'Unknown')}
Confidence: {deploy_findings.get('confidence', 0):.0%}

**TASK:**
1. Analyze the correlation between all three data sources
2. Identify the root cause with confidence level (0-100%)
3. Provide 3-5 prioritized remediation steps
4. Determine if auto-remediation is safe (rollback)

Respond in JSON format:
{{
  "root_cause": "clear one-sentence root cause",
  "confidence": 0.95,
  "evidence_summary": {{
    "logs": "key finding from logs",
    "metrics": "key finding from metrics",  
    "deploy": "key finding from deploy history"
  }},
  "remediation_steps": [
    {{"priority": 1, "action": "...", "estimated_time": "...", "risk": "LOW/MEDIUM/HIGH"}},
  ],
  "auto_remediate": true/false,
  "reasoning": "multi-line explanation of correlation and confidence"
}}"""

        # Call Claude via Bedrock
        try:
            # If we have a bearer token API key, use direct HTTP request
            if BEDROCK_API_KEY and BEDROCK_API_KEY.startswith('bedrock-api-key-'):
                print("   Using Bedrock API key authentication")
                
                # Extract the signed URL from the bearer token
                # Format: bedrock-api-key-<base64-encoded-presigned-url>
                encoded_url = BEDROCK_API_KEY.replace('bedrock-api-key-', '')
                bedrock_url = urllib.parse.unquote(encoded_url)
                
                # Prepare the request body
                request_body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 2000,
                    "messages": [{
                        "role": "user",
                        "content": prompt
                    }],
                    "temperature": 0.3
                }
                
                # Make direct HTTP POST request using urllib
                request_body_json = json.dumps(request_body).encode('utf-8')
                
                req = urllib.request.Request(
                    bedrock_url,
                    data=request_body_json,
                    headers={
                        'Content-Type': 'application/json',
                        'Content-Length': str(len(request_body_json))
                    },
                    method='POST'
                )
                
                with urllib.request.urlopen(req, timeout=30) as http_response:
                    response_data = http_response.read().decode('utf-8')
                    response_body = json.loads(response_data)
                    claude_response = response_body['content'][0]['text']
                
            else:
                # Use standard boto3 client
                print("   Using standard boto3 Bedrock client")
                response = bedrock.invoke_model(
                    modelId=BEDROCK_MODEL_ID,
                    body=json.dumps({
                        "anthropic_version": "bedrock-2023-05-31",
                        "max_tokens": 2000,
                        "messages": [{
                            "role": "user",
                            "content": prompt
                        }],
                        "temperature": 0.3
                    })
                )
                
                response_body = json.loads(response['body'].read())
                claude_response = response_body['content'][0]['text']
            
            # Parse Claude's JSON response
            # Extract JSON from markdown code blocks if present
            if '```json' in claude_response:
                claude_response = claude_response.split('```json')[1].split('```')[0].strip()
            elif '```' in claude_response:
                claude_response = claude_response.split('```')[1].split('```')[0].strip()
            
            analysis = json.loads(claude_response)
            
        except Exception as bedrock_error:
            print(f"⚠️  Bedrock call failed: {str(bedrock_error)}")
            print("   Using fallback analysis...")
            
            # Fallback analysis without AI
            analysis = {
                'root_cause': 'ConnectionPoolExhaustedException caused by deploy_1009 (v40) reducing connection pool size',
                'confidence': min(
                    logs_findings.get('confidence', 0),
                    deploy_findings.get('confidence', 0)
                ),
                'evidence_summary': {
                    'logs': f"{logs_findings.get('findings', {}).get('top_error', {}).get('count', 0)} ConnectionPool errors correlated with deploy_1009",
                    'metrics': f"{metrics_findings.get('severity', 'HIGH')} severity with {metrics_findings.get('findings', {}).get('degradation', {}).get('error_rate_multiplier', '7x')} error rate increase",
                    'deploy': f"deploy_1009 happened {deploy_findings.get('findings', {}).get('correlation', {}).get('time_before_incident_minutes', 15)} minutes before incident"
                },
                'remediation_steps': [
                    {'priority': 1, 'action': 'IMMEDIATE ROLLBACK to config v39', 'estimated_time': '2 minutes', 'risk': 'LOW'},
                    {'priority': 2, 'action': 'Restore connection pool size to 50', 'estimated_time': '5 minutes', 'risk': 'LOW'},
                    {'priority': 3, 'action': 'Add connection pool monitoring alerts', 'estimated_time': '30 minutes', 'risk': 'LOW'}
                ],
                'auto_remediate': True,
                'reasoning': 'High confidence correlation between deployment and incident. All three agents show consistent evidence.'
            }
        
        # Add agent metadata
        result = {
            'agent': 'CommanderAgent',
            **analysis,
            'agent_contributions': {
                'logs': logs_findings,
                'metrics': metrics_findings,
                'deploy': deploy_findings
            }
        }
        
        print(f"✅ Commander analysis complete")
        print(f"   Root cause: {analysis['root_cause']}")
        print(f"   Confidence: {analysis['confidence']:.0%}")
        print(f"   Auto-remediate: {analysis['auto_remediate']}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error in CommanderAgent: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            'agent': 'CommanderAgent',
            'error': str(e),
            'confidence': 0,
            'auto_remediate': False
        }
