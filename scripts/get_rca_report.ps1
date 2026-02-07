# Get RCA Report - PowerShell Version
# Fetches latest Step Functions execution and generates RCA report

$AWS_REGION = "us-east-1"
$AWS_ACCOUNT_ID = "333813598365"

Write-Host "📊 Fetching Latest Investigation Results" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Get latest execution
$EXECUTION_ARN = aws stepfunctions list-executions `
  --state-machine-arn "arn:aws:states:${AWS_REGION}:${AWS_ACCOUNT_ID}:stateMachine:incident-investigation" `
  --max-results 1 `
  --region $AWS_REGION `
  --query 'executions[0].executionArn' `
  --output text

if ([string]::IsNullOrEmpty($EXECUTION_ARN) -or $EXECUTION_ARN -eq "None") {
    Write-Host "❌ No executions found. Run .\trigger-investigation.ps1 first" -ForegroundColor Red
    exit 1
}

Write-Host "Execution: $EXECUTION_ARN"
Write-Host ""

# Check status
$STATUS = aws stepfunctions describe-execution `
  --execution-arn $EXECUTION_ARN `
  --region $AWS_REGION `
  --query 'status' `
  --output text

Write-Host "Status: $STATUS"

if ($STATUS -ne "SUCCEEDED") {
    Write-Host "⚠️  Execution not yet complete or failed" -ForegroundColor Yellow
    exit 1
}

# Get output
Write-Host ""
Write-Host "Generating RCA Report..." -ForegroundColor Green

aws stepfunctions describe-execution `
  --execution-arn $EXECUTION_ARN `
  --region $AWS_REGION `
  --query 'output' `
  --output text | Out-File -FilePath .\stepfunctions_output.json -Encoding UTF8

# Generate report using Python
python generate_rca_report.py stepfunctions_output.json

Write-Host ""
Write-Host "✅ Done! Check the generated rca_report_*.md file" -ForegroundColor Green
