#!/usr/bin/env pwsh
<#+
.SYNOPSIS
Wait for a new terminal Codex task event without using an LLM heartbeat.

.DESCRIPTION
Observes one explicit Codex JSONL session file. By default the watcher starts at
that file's current end, so old task_complete events cannot satisfy a new wait.
A .NET FileSystemWatcher wakes the local PowerShell process when the file changes.
Only newly appended JSONL records are parsed.

The script does not call OpenAI, does not modify the session file, and does not
print arbitrary event payloads.

.EXITCODES
0   A new task_complete event was observed.
2   Invalid input or ambiguous/truncated session state.
124 Timeout expired before a new task_complete event was observed.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$SessionFile,

    [ValidateRange(0, 2147483647)]
    [int]$TimeoutSeconds = 0,

    [switch]$FromStart
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-TerminalMarker {
    param([string]$Path)

    [pscustomobject]@{
        event        = 'EXECUTOR_TASK_COMPLETE'
        session_file = $Path
        observed_at  = [DateTimeOffset]::UtcNow.ToString('o')
    } | ConvertTo-Json -Compress
}

try {
    $resolved = (Resolve-Path -LiteralPath $SessionFile -ErrorAction Stop).Path
    $fileInfo = Get-Item -LiteralPath $resolved -ErrorAction Stop

    if (-not ($fileInfo -is [System.IO.FileInfo])) {
        throw 'SessionFile must point to one regular file.'
    }

    $directory = $fileInfo.DirectoryName
    $fileName = $fileInfo.Name
    [long]$offset = if ($FromStart) { 0 } else { $fileInfo.Length }
    $buffer = ''

    $watcher = [System.IO.FileSystemWatcher]::new($directory, $fileName)
    $watcher.IncludeSubdirectories = $false
    $watcher.NotifyFilter =
        [System.IO.NotifyFilters]::LastWrite -bor
        [System.IO.NotifyFilters]::Size -bor
        [System.IO.NotifyFilters]::FileName

    $sourceId = 'sol-luna-codex-' + [Guid]::NewGuid().ToString('N')
    $subscription = Register-ObjectEvent \
        -InputObject $watcher \
        -EventName Changed \
        -SourceIdentifier $sourceId
    $watcher.EnableRaisingEvents = $true

    $deadline = if ($TimeoutSeconds -gt 0) {
        [DateTimeOffset]::UtcNow.AddSeconds($TimeoutSeconds)
    } else {
        $null
    }

    function Read-NewJsonLines {
        $current = Get-Item -LiteralPath $resolved -ErrorAction Stop
        if ($current.Length -lt $script:offset) {
            throw 'Session file was truncated or replaced while waiting; refusing ambiguous completion state.'
        }

        $share = [System.IO.FileShare]::ReadWrite -bor [System.IO.FileShare]::Delete
        $stream = [System.IO.FileStream]::new(
            $resolved,
            [System.IO.FileMode]::Open,
            [System.IO.FileAccess]::Read,
            $share
        )

        try {
            [void]$stream.Seek($script:offset, [System.IO.SeekOrigin]::Begin)
            $remaining = $stream.Length - $script:offset
            if ($remaining -le 0) {
                return @()
            }

            $bytes = New-Object byte[] $remaining
            $read = $stream.Read($bytes, 0, $bytes.Length)
            $script:offset += $read
            $text = [System.Text.Encoding]::UTF8.GetString($bytes, 0, $read)
            $script:buffer += $text
        }
        finally {
            $stream.Dispose()
        }

        $parts = $script:buffer -split "`n", -1
        if ($parts.Count -eq 1) {
            return @()
        }

        $script:buffer = $parts[-1]
        return @($parts[0..($parts.Count - 2)])
    }

    function Test-TaskCompleteLine {
        param([string]$Line)

        $candidate = $Line.TrimEnd("`r")
        if ([string]::IsNullOrWhiteSpace($candidate)) {
            return $false
        }

        try {
            $record = $candidate | ConvertFrom-Json -Depth 32 -ErrorAction Stop
        }
        catch {
            # A malformed/non-JSON line is ignored. No payload is printed.
            return $false
        }

        return (
            $record.type -eq 'event_msg' -and
            $null -ne $record.payload -and
            $record.payload.type -eq 'task_complete'
        )
    }

    function Drain-AppendedEvents {
        foreach ($line in (Read-NewJsonLines)) {
            if (Test-TaskCompleteLine -Line $line) {
                Write-TerminalMarker -Path $resolved
                return $true
            }
        }
        return $false
    }

    # Close the race between capturing the initial EOF and enabling notifications.
    if (Drain-AppendedEvents) {
        exit 0
    }

    while ($true) {
        if ($null -eq $deadline) {
            $evt = Wait-Event -SourceIdentifier $sourceId
        }
        else {
            $remainingSeconds = ($deadline - [DateTimeOffset]::UtcNow).TotalSeconds
            if ($remainingSeconds -le 0) {
                [Console]::Error.WriteLine('Timed out waiting for a new task_complete event.')
                exit 124
            }
            $evt = Wait-Event \
                -SourceIdentifier $sourceId \
                -Timeout ([Math]::Max(1, [Math]::Ceiling($remainingSeconds)))
            if ($null -eq $evt) {
                [Console]::Error.WriteLine('Timed out waiting for a new task_complete event.')
                exit 124
            }
        }

        Remove-Event -EventIdentifier $evt.EventIdentifier -ErrorAction SilentlyContinue

        if (Drain-AppendedEvents) {
            exit 0
        }
    }
}
catch {
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 2
}
finally {
    if (Get-Variable -Name sourceId -Scope 0 -ErrorAction SilentlyContinue) {
        Unregister-Event -SourceIdentifier $sourceId -ErrorAction SilentlyContinue
        Get-Event -SourceIdentifier $sourceId -ErrorAction SilentlyContinue | Remove-Event -ErrorAction SilentlyContinue
    }
    if (Get-Variable -Name watcher -Scope 0 -ErrorAction SilentlyContinue) {
        $watcher.EnableRaisingEvents = $false
        $watcher.Dispose()
    }
}
