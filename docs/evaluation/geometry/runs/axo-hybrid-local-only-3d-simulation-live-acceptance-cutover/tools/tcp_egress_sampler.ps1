# Samples the TCP table about once per second for the backend (owner of :8000), every llama-server process and an
# optional witness PID, and appends one JSON line per NON-loopback remote endpoint seen plus a heartbeat per sample (an
# empty result is then provably "sampled and clean", not "never ran"). Covers egress that ignores HTTP(S)_PROXY.
# v2 (after pass 1): `netstat -ano` instead of Get-NetTCPConnection, which took ~12 s per sample on this host.
# usage: pwsh -File tcp_egress_sampler.ps1 <out.jsonl> [-WitnessPid N -Samples K]  (witness: watch a process known to connect out)
param([string]$Out, [int]$WitnessPid = 0, [int]$Samples = 0)
$loop = '^(127\.0\.0\.1|\[::1\]|0\.0\.0\.0|\[::\]|\*):'
while ($true) {
    $rows = netstat -ano -p TCP | Select-String '^\s*TCP' | ForEach-Object { , ($_.Line.Trim() -split '\s+') }
    $backend = ($rows | Where-Object { $_[1] -match ':8000$' -and $_[3] -eq 'LISTENING' } | Select-Object -First 1)
    $pids = @($WitnessPid) + @((Get-Process llama-server -ErrorAction SilentlyContinue).Id) | Where-Object { $_ }
    if ($backend) { $pids += [int]$backend[4] }
    $mine = @($rows | Where-Object { $pids -contains [int]$_[4] })
    $bad = @($mine | Where-Object { $_[2] -notmatch $loop })
    $t = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
    foreach ($c in $bad) {
        @{ t = $t; pid = [int]$c[4]; remote = $c[2]; state = $c[3] } | ConvertTo-Json -Compress | Add-Content -Path $Out
    }
    @{ t = $t; heartbeat = $true; pids = $pids; conns = $mine.Count; non_loopback = $bad.Count } |
        ConvertTo-Json -Compress | Add-Content -Path $Out
    if ($Samples -gt 0 -and --$Samples -eq 0) { break }
    Start-Sleep -Milliseconds 1000
}
