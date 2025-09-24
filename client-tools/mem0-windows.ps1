# mem0 Windows Shell Integration
# Supports PowerShell, Command Prompt, and Windows Subsystem for Linux

param(
    [string]$Action,
    [string]$ContextName,
    [string]$Command = "",
    [string]$WorkingDir = "",
    [int]$ExitCode = 0
)

$MEM0_PORT = $env:MEM0_PORT
if (-not $MEM0_PORT) { $MEM0_PORT = "13370" }

$MEM0_DEBUG = $env:MEM0_DEBUG
if (-not $MEM0_DEBUG) { $MEM0_DEBUG = "0" }

$MEM0_CONTEXT = $env:MEM0_CONTEXT
$MEM0_CACHE_TTL = $env:MEM0_CACHE_TTL
if (-not $MEM0_CACHE_TTL) { $MEM0_CACHE_TTL = "30" }

# Global variables
$script:CurrentContext = ""
$script:ContextCache = ""
$script:CacheTimestamp = 0
$script:LastCommand = ""

function Write-DebugLog {
    param([string]$Message)
    if ($MEM0_DEBUG -eq "1") {
        Write-Host "[mem0-debug] $Message" -ForegroundColor Yellow
    }
}

function Test-ServerConnection {
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:$MEM0_PORT/health" -Method GET -TimeoutSec 5 -ErrorAction Stop
        return $true
    }
    catch {
        return $false
    }
}

function Get-ContextFromCache {
    $currentTime = [int](Get-Date -UFormat %s)

    if ($script:ContextCache -and ($currentTime - $script:CacheTimestamp) -lt [int]$MEM0_CACHE_TTL) {
        Write-DebugLog "Using cached context: $($script:ContextCache)"
        return $script:ContextCache
    }

    if (Test-ServerConnection) {
        try {
            $response = Invoke-WebRequest -Uri "http://127.0.0.1:$MEM0_PORT/context/active" -Method GET -TimeoutSec 5
            if ($response.StatusCode -eq 200) {
                $script:ContextCache = $response.Content
                $script:CacheTimestamp = $currentTime
                Write-DebugLog "Fetched context from server: $($script:ContextCache)"
                return $script:ContextCache
            }
        }
        catch {
            Write-DebugLog "Failed to fetch context: $($_.Exception.Message)"
        }
    }

    return ""
}

function Send-Command {
    param(
        [string]$Command,
        [string]$WorkingDir,
        [int]$ExitCode
    )

    $context = Get-ContextFromCache
    if (-not $context) {
        Write-DebugLog "No active context, skipping command"
        return
    }

    # Skip short or irrelevant commands
    if ($Command.Length -lt 3 -or $Command -match '^(ls|dir|cd|echo|set|cls|exit|history)$') {
        return
    }

    Write-DebugLog "Sending command: $Command (pwd: $WorkingDir, exit: $ExitCode)"

    $jsonPayload = @{
        type = "terminal_command"
        source = "powershell_session"
        data = @{
            command = $Command
            timestamp = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss.fffZ")
            pwd = $WorkingDir
            exit_code = $ExitCode
            context = $context
            shell = "powershell"
            os = "windows"
        }
    } | ConvertTo-Json -Depth 10

    if (Test-ServerConnection) {
        try {
            $job = Start-Job -ScriptBlock {
                param($url, $payload)
                Invoke-WebRequest -Uri $url -Method POST -Body $payload -ContentType "application/json" -TimeoutSec 10 | Out-Null
            } -ArgumentList "http://127.0.0.1:$MEM0_PORT/memory", $jsonPayload

            # Clean up job after completion
            Start-Job -ScriptBlock {
                param($jobId)
                Wait-Job -Id $jobId -Timeout 30 | Remove-Job
            } -ArgumentList $job.Id | Out-Null

            Write-DebugLog "Command sent successfully"
        }
        catch {
            Write-DebugLog "Failed to send command: $($_.Exception.Message)"
        }
    }
    else {
        Write-DebugLog "Server not available, command not sent"
    }
}

function Start-Mem0Context {
    param([string]$ContextName)

    if (-not $ContextName) {
        Write-Host "Usage: Start-Mem0Context -ContextName <name>" -ForegroundColor Red
        return
    }

    if (Test-ServerConnection) {
        try {
            $jsonPayload = @{ name = $ContextName } | ConvertTo-Json
            $response = Invoke-WebRequest -Uri "http://127.0.0.1:$MEM0_PORT/context/start" -Method POST -Body $jsonPayload -ContentType "application/json"

            if ($response.StatusCode -eq 200) {
                $env:MEM0_CONTEXT = $ContextName
                $script:ContextCache = ""
                $script:CacheTimestamp = 0
                Write-Host "Started recording to context: $ContextName" -ForegroundColor Green
            }
            else {
                Write-Host "Failed to start context" -ForegroundColor Red
            }
        }
        catch {
            Write-Host "Failed to start context: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    else {
        Write-Host "mem0 server not running" -ForegroundColor Red
    }
}

function Stop-Mem0Context {
    if (Test-ServerConnection) {
        try {
            $response = Invoke-WebRequest -Uri "http://127.0.0.1:$MEM0_PORT/context/stop" -Method POST

            if ($response.StatusCode -eq 200) {
                $env:MEM0_CONTEXT = ""
                $script:ContextCache = ""
                $script:CacheTimestamp = 0
                Write-Host "Stopped recording" -ForegroundColor Green
            }
            else {
                Write-Host "Failed to stop context" -ForegroundColor Red
            }
        }
        catch {
            Write-Host "Failed to stop context: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    else {
        Write-Host "mem0 server not running" -ForegroundColor Red
    }
}

function Get-Mem0Context {
    $context = Get-ContextFromCache
    if ($context) {
        Write-Host "Active context: $context" -ForegroundColor Green
    }
    else {
        Write-Host "No active context" -ForegroundColor Yellow
    }
}

function Clear-Mem0Cache {
    $script:ContextCache = ""
    $script:CacheTimestamp = 0
    Write-DebugLog "Context cache cleared"
    Write-Host "Cache cleared" -ForegroundColor Green
}

# Handle command-line arguments
switch ($Action) {
    "start" {
        Start-Mem0Context -ContextName $ContextName
    }
    "stop" {
        Stop-Mem0Context
    }
    "active" {
        Get-Mem0Context
    }
    "clear-cache" {
        Clear-Mem0Cache
    }
    "send" {
        if ($Command) {
            Send-Command -Command $Command -WorkingDir $WorkingDir -ExitCode $ExitCode
        }
    }
    default {
        Write-Host "Usage: .\mem0-windows.ps1 -Action <start|stop|active|clear-cache> [-ContextName <name>] [-Command <cmd>] [-WorkingDir <dir>] [-ExitCode <code>]" -ForegroundColor Yellow
    }
}

# Export functions for use in PowerShell profile
Export-ModuleMember -Function Start-Mem0Context, Stop-Mem0Context, Get-Mem0Context, Clear-Mem0Cache, Send-Command
