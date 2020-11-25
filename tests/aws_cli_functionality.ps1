
# If there are ExecutionPolicy issues, execute with
# powershell -ExecutionPolicy Bypass -File <THIS FILE>
$ErrorActionPreference = "Stop"
$s3Endpoint = "http://localhost:8000"


# AWS CLI Tests for basic compatibility and logic
# This should be run against a clean Redis
# Golden Path

function Run-Test ([String]$TestName, [String]$TestCommand, [String]$Expect) {

    Invoke-Expression $TestCommand
    $ExitCode = $?

    if ( $ExitCode -eq $Expect) {
        Write-Output "PASS: $TestName"
    } else {
        Write-Output "FAIL: $TestName"
        Write-Output "\t$TestCommand"
        exit
    }
}

$TestName = "List all S3 Buckets"
$TestCommand = "aws s3 ls --endpoint-url $s3Endpoint"

Run-Test $TestName $TestCommand 0

$TestName = "Create S3 Bucket"
$TestCommand = "aws s3 mb s3://testbucket --endpoint-url $s3Endpoint"

Run-Test $TestName $TestCommand 0

$TestName = "Remove empty Bucket"
$TestCommand = "aws s3 rb s3://testbucket --endpoint-url $s3Endpoint"

Run-Test $TestName $TestCommand 0

$TestName = "Create S3 Bucket (again)"
$TestCommand = "aws s3 mb s3://testbucket --endpoint-url $s3Endpoint"

Run-Test $TestName $TestCommand 0

Write-Output "Some Nonsense Data" | Out-File -FilePath ./TestFile 

$TestName = "Create S3 Key in Bucket"
$TestCommand = "aws s3 cp ./TestFile s3://testbucket --endpoint-url $s3Endpoint"

Run-Test $TestName $TestCommand 0

$TestName = "Remove Bucket with keys should fail"
$TestCommand = "aws s3 rb s3://testbucket --endpoint-url $s3Endpoint"

Run-Test $TestName $TestCommand 1

$TestName = "Remove Key from Bucket"
$TestCommand = "aws s3 rm s3://testbucket/TestFile --endpoint-url $s3Endpoint"

Run-Test $TestName $TestCommand 0

$TestName = "Remove Key not existing in Bucket"
$TestCommand = "aws s3 rm s3://testbucket/NotHere --endpoint-url $s3Endpoint"

Run-Test $TestName $TestCommand 1

$TestName = "Remove empty Bucket"
$TestCommand = "aws s3 rb s3://testbucket --endpoint-url $s3Endpoint"

Run-Test $TestName $TestCommand 0