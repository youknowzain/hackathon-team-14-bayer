#!/usr/bin/env python3
"""
Generate RCA Report from Step Functions Output

This creates a human-readable Markdown report from the Commander's decision
"""

import json
import sys
from datetime import datetime

def generate_rca_report(stepfunctions_output):
    """Convert Step Functions JSON output to Markdown RCA report"""
    
    # Parse the output
    if isinstance(stepfunctions_output, str):
        data = json.loads(stepfunctions_output)
    else:
        data = stepfunctions_output
    
    # Extract key information
    root_cause = data.get('root_cause', 'Unknown')
    confidence = data.get('confidence', 0.0)
    remediation_steps = data.get('remediation_steps', [])
    evidence = data.get('evidence', {})
    llm_reasoning = data.get('llm_reasoning', '')
    
    # Generate report (Windows-safe, no emoji)
    report = f"""# Incident Root Cause Analysis Report

**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}  
**Status:** Investigation Complete  
**Confidence:** {confidence * 100:.0f}%

---

## Executive Summary

### Root Cause
{root_cause}

### Confidence Level
{'[HIGH]' if confidence >= 0.85 else '[MEDIUM]' if confidence >= 0.7 else '[LOW]'} ({confidence * 100:.0f}%)

---

## Evidence Analysis

### LogsAgent Findings (WHAT Happened)
"""
    
    logs_analysis = evidence.get('logs', {})
    if logs_analysis:
        what_happened = logs_analysis.get('what_happened', 'No data')
        report += f"""
- **Primary Issue:** {what_happened}
"""
        
        correlation = logs_analysis.get('correlation', {})
        if correlation:
            if correlation.get('correlation_found'):
                report += f"""- **Deployment Correlation:** {correlation.get('percentage', 0):.1f}% of errors linked to deployment `{correlation.get('deployment_id')}`
- **Insight:** {correlation.get('insight', 'N/A')}
"""
        
        error_patterns = logs_analysis.get('error_patterns', [])
        if error_patterns:
            report += "\n**Top Error Patterns:**\n"
            for i, pattern in enumerate(error_patterns[:5], 1):
                error_type = pattern.get('error_type', 'Unknown')
                count = pattern.get('error_count', 0)
                service = pattern.get('service', 'unknown')
                report += f"{i}. `{error_type}` - {count} occurrences ({service})\n"
    
    report += "\n### MetricsAgent Findings (HOW BAD)\n"
    
    metrics_analysis = evidence.get('metrics', {})
    if metrics_analysis:
        severity = metrics_analysis.get('how_bad', 'UNKNOWN')
        severity_score = metrics_analysis.get('severity_score', 0)
        
        severity_label = severity
        
        report += f"""
- **Severity:** [{severity_label}] (Score: {severity_score}/100)
- **Recommended Action:** {metrics_analysis.get('recommended_action', 'Monitor')}
"""
        
        error_rate = metrics_analysis.get('error_rate', {})
        if error_rate:
            spike_ratio = error_rate.get('spike_ratio', 1.0)
            report += f"- **Error Rate Spike:** {spike_ratio:.1f}x above baseline\n"
        
        anomaly = metrics_analysis.get('anomaly', {})
        if anomaly and anomaly.get('anomaly_detected'):
            report += f"- **Anomaly Detected:** {anomaly.get('message', 'Yes')}\n"
    
    report += "\n### DeployAgent Findings (FIX Options)\n"
    
    deploy_analysis = evidence.get('deploy', {})
    if deploy_analysis:
        fix_recommendation = deploy_analysis.get('fix_recommendation', {})
        
        if fix_recommendation.get('recommend_rollback'):
            report += f"""
- **Recommendation:** [YES] ROLLBACK RECOMMENDED
- **Target Deployment:** `{fix_recommendation.get('deployment_id')}`
- **Confidence:** {fix_recommendation.get('confidence', 0.0) * 100:.0f}%
- **Reason:** {fix_recommendation.get('reason')}
"""
        else:
            report += f"""
- **Recommendation:** [NO] Rollback not recommended
- **Reason:** {fix_recommendation.get('reason', 'Insufficient correlation')}
"""
        
        fix_applied = deploy_analysis.get('fix_applied')
        if fix_applied:
            report += f"\n**Auto-Remediation:** {fix_applied.get('status', 'Not executed')}\n"
    
    report += "\n---\n\n## LLM Reasoning\n\n"
    if llm_reasoning:
        report += f"{llm_reasoning}\n"
    else:
        report += "*LLM reasoning not available*\n"
    
    report += "\n---\n\n## Remediation Steps\n\n"
    
    if remediation_steps:
        for i, step in enumerate(remediation_steps, 1):
            report += f"{i}. {step}\n"
    else:
        report += "*No specific remediation steps provided*\n"
    
    report += f"""
---

## Next Actions

### Immediate
1. Review this RCA with the team
2. {'Proceed with rollback if approved' if deploy_analysis.get('fix_recommendation', {}).get('recommend_rollback') else 'Monitor the situation'}
3. Notify stakeholders

### Short-term
1. Implement remediation steps
2. Add monitoring for this error pattern
3. Update runbooks

### Long-term
1. Post-incident review
2. Update deployment processes
3. Add automated safeguards

---

**Report Generated by:** Autonomous Incident Commander  
**LLM Model:** Claude 3.5 Sonnet (Amazon Bedrock)  
**Agent Framework:** Multi-Agent AWS Step Functions
"""
    
    return report


if __name__ == '__main__':
    # Read from stdin or file
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r') as f:
            output_json = f.read()
    else:
        output_json = sys.stdin.read()
    
    # Generate report
    report = generate_rca_report(output_json)
    
    # Print to stdout
    print(report)
    
    # Also save to file (with UTF-8 encoding for Windows)
    filename = f"rca_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.md"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✅ Report saved to: {filename}", file=sys.stderr)
