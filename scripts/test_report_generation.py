#!/usr/bin/env python3
"""
Test RCA Report Generation with Sample Data
"""

import json
from datetime import datetime

# Sample Commander output (what Step Functions would return)
sample_output = {
    "agent": "CommanderAgent",
    "model": "anthropic.claude-3-5-sonnet-20240620-v1:0",
    "root_cause": "ConnectionPoolExhaustedException caused by deployment deploy_1009 which reduced HikariCP database connection pool size from maxPoolSize=50 to maxPoolSize=10",
    "confidence": 0.92,
    "remediation_steps": [
        "Rollback deployment deploy_1009 to previous stable version",
        "Restore connection pool configuration to maxPoolSize=50 in HikariCP settings",
        "Implement connection pool monitoring alerts with threshold at 80% utilization",
        "Add circuit breaker pattern for database connection handling"
    ],
    "auto_remediate_approved": False,
    "evidence": {
        "logs": {
            "what_happened": "Found 10 distinct error patterns",
            "top_error": {
                "error_type": "ConnectionPoolExhaustedException",
                "error_count": "412",
                "service": "payment",
                "deployment_id": "deploy_1009"
            },
            "correlation": {
                "correlation_found": True,
                "deployment_id": "deploy_1009",
                "percentage": 68.5,
                "insight": "68.5% of errors linked to deployment deploy_1009"
            },
            "error_patterns": [
                {"error_type": "ConnectionPoolExhaustedException", "error_count": "412", "service": "payment"},
                {"error_type": "SqlTimeoutException", "error_count": "198", "service": "checkout"},
                {"error_type": "DatabaseConnectionFailure", "error_count": "156", "service": "inventory"},
                {"error_type": "SocketTimeoutException", "error_count": "89", "service": "payment"},
                {"error_type": "CircuitBreakerOpenException", "error_count": "67", "service": "checkout"}
            ]
        },
        "metrics": {
            "how_bad": "CRITICAL",
            "severity_score": 85,
            "recommended_action": "IMMEDIATE",
            "error_rate": {
                "recent_error_rate": 32.5,
                "baseline_error_rate": 10.2,
                "spike_ratio": 3.2
            },
            "anomaly": {
                "anomaly_detected": True,
                "severity": "CRITICAL",
                "message": "Error rate is 3.2x higher than baseline"
            }
        },
        "deploy": {
            "fix_recommendation": {
                "recommend_rollback": True,
                "confidence": 0.9,
                "deployment_id": "deploy_1009",
                "reason": "68.5% of errors correlate with this deployment"
            },
            "recent_deployments": [
                {"deployment_id": "deploy_1009", "timestamp": "2026-02-06T09:58:00Z", "service": "payment"}
            ]
        }
    },
    "llm_reasoning": "After analyzing evidence from all three agents, the root cause is clear: deployment deploy_1009 changed the database connection pool configuration, reducing it from 50 to 10 connections. This caused connection pool exhaustion under normal load, leading to cascading failures across dependent services. The 68.5% correlation with the deployment and 3.2x error spike provide high confidence in this assessment."
}

# Save to file
with open('sample_stepfunctions_output.json', 'w') as f:
    json.dump(sample_output, f, indent=2)

print("✅ Created: sample_stepfunctions_output.json")
print("\nNow run:")
print("  python generate_rca_report.py sample_stepfunctions_output.json")
