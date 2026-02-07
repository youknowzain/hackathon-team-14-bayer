# Trigger Investigation - PowerShell Version

$AWS_REGION = "us-east-1"
$AWS_ACCOUNT_ID = "333813598365"
$LOG_GROUP_NAME = "/aws/incident-commander/critical-errors"

Write-Host "🚀 Triggering Incident Investigation" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Create input JSON
$startTime = (Get-Date).AddMinutes(-10).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss")
$endTime = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss")

$input = @{
    log_group = $LOG_GROUP_NAME
    time_window = @{
        start = $startTime
        end = $endTime
    }
    error_count = 120
    namespace = "IncidentCommander"
    metric_name = "ErrorCount"
    correlation = @{
        deployment_id = "deploy_1009"
        percentage = 68.5
    }
    auto_remediate = $false
} | ConvertTo-Json

Write-Host "Input:"
Write-Host $input

Write-Host ""
Write-Host "Starting execution..." -ForegroundColor Green

# Save input to temp file
$input | Out-File -FilePath .\stepfunctions_input.json -Encoding UTF8

# Start execution
$result = aws stepfunctions start-execution `
  --state-machine-arn "arn:aws:states:${AWS_REGION}:${AWS_ACCOUNT_ID}:stateMachine:incident-investigation" `
  --input file://stepfunctions_input.json `
  --region $AWS_REGION | ConvertFrom-Json

$EXECUTION_ARN = $result.executionArn

Write-Host "Execution ARN: $EXECUTION_ARN" -ForegroundColor Yellow

Write-Host ""
Write-Host "Monitoring execution (this may take 1-2 minutes)..." -ForegroundColor Cyan

for ($i = 1; $i -le 60; $i++) {
    $STATUS = aws stepfunctions describe-execution `
      --execution-arn $EXECUTION_ARN `
      --region $AWS_REGION `
      --query 'status' `
      --output text
    
    Write-Host "[$i] Status: $STATUS"
    
    if ($STATUS -eq "SUCCEEDED") {
        Write-Host ""
        Write-Host "✅ Investigation Complete!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Final Output:"
        
        aws stepfunctions describe-execution `
          --execution-arn $EXECUTION_ARN `
          --region $AWS_REGION `
          --query 'output' `
          --output text | python -m json.tool
        
        Write-Host ""
        Write-Host "Generate report with: .\get_rca_report.ps1" -ForegroundColor Cyan
        break
    }
    elseif ($STATUS -eq "FAILED") {
        Write-Host ""
        Write-Host "❌ Investigation Failed" -ForegroundColor Red
        
        aws stepfunctions describe-execution `
          --execution-arn $EXECUTION_ARN `
          --region $AWS_REGION
        break
    }
    
    Start-Sleep -Seconds 2
}
