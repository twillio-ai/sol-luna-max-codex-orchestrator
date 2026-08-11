#!/usr/bin/env pwsh
<#
.SYNOPSIS
Wait for a new terminal Codex task event without using an LLM heartbeat.

.DESCRIPTION
Observes one explicit Codex JSONL session file. By default the watcher starts at
that file's current end, so old task_complete events cannot satisfy a new wait.
PowerShell reads only newly appended bytes and sleeps locally between checks.

This is intentionally process-level polling, not model polling: it does not call
OpenAI, does not invoke Sol or Luna, does not modify the session file, and does not
print arbitrary event payloads.

Use -ReadyFile when a launcher needs a deterministic local signal that the watcher
captured its starting offset before work begins.

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

    [ValidateRange(25, 60000)]
    [int]$PollMilliseconds = 250,

    [switch]$FromStart,

    [string]$ReadyFile = ''
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

    [long]$offset = if ($FromStart) { 0 } else { $fileInfo.Length }
    $buffer = ''
    $deadline = if ($TimeoutSeconds -gt 0) {
        [DateTimeOffset]::UtcNow.AddSeconds($TimeoutSeconds)
    } else {
        $null
    }

    if (-not [string]::IsNullOrWhiteSpace($ReadyFile)) {
        $readyPath = [System.IO.Path]::GetFullPath($ReadyFile)
        if ($readyPath -eq $resolved) {
            throw 'ReadyFile must not be the session file.'
        }
        [System.IO.File]::WriteAllText($readyPath, 'WATCHER_READY', [System.Text.Encoding]::UTF8)
    }

    while ($true) {
        $current = Get-Item -LiteralPath $resolved -ErrorAction Stop
        if ($current.Length -lt $offset) {
            throw 'Session file was truncated or replaced while waiting; refusing ambiguous completion state.'
        }

        if ($current.Length -gt $offset) {
            $share = [System.IO.FileShare]::ReadWrite -bor [System.IO.FileShare]::Delete
            $stream = [System.IO.FileStream]::new(
                $resolved,
                [System.IO.FileMode]::Open,
                [System.IO.FileAccess]::Read,
                $share
            )

            try {
                [void]$stream.Seek($offset, [System.IO.SeekOrigin]::Begin)
                [long]$remaining = $stream.Length - $offset
                if ($remaining -gt [int]::MaxValue) {
                    throw 'New session chunk is too large to read safely in one pass.'
                }

                $bytes = New-Object byte[] ([int]$remaining)
                $read = $stream.Read($bytes, 0, $bytes.Length)
                $offset += $read
                $buffer += [System.Text.Encoding]::UTF8.GetString($bytes, 0, $read)
            }
            finally {
                $stream.Dispose()
            }

            $parts = $buffer -split "`n"
            if ($parts.Count -gt 1) {
                $buffer = $parts[-1]
                foreach ($line in $parts[0..($parts.Count - 2)]) {
                    $candidate = $line.TrimEnd("`r")
                    if ([string]::IsNullOrWhiteSpace($candidate)) {
                        continue
                    }

                    try {
                        $record = $candidate | ConvertFrom-Json -Depth 32 -ErrorAction Stop
                    }
                    catch {
                        continue
                    }

                    if (
                        $record.type -eq 'event_msg' -and
                        $null -ne $record.payload -and
                        $record.payload.type -eq 'task_complete'
                    ) {
                        Write-TerminalMarker -Path $resolved
                        exit 0
                    }
                }
            }
        }

        if ($null -ne $deadline -and [DateTimeOffset]::UtcNow -ge $deadline) {
            [Console]::Error.WriteLine('Timed out waiting for a new task_complete event.')
            exit 124
        }

        Start-Sleep -Milliseconds $PollMilliseconds
    }
}
catch {
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 2
}
