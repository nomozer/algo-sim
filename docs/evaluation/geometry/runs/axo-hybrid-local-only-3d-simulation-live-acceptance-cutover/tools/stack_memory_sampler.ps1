# Per-second working set / private bytes / CPU seconds of the whole local-only stack: backend (owner of :8000 + its
# venv launcher parent), llama-server, and the Playwright Chromium processes (path under ms-playwright). Plain CSV
# (invariant culture, no thousands separators): t_ms,group,pid_count,ws_mb,private_mb,cpu_s
# usage: pwsh -File stack_memory_sampler.ps1 <out.csv>
param([string]$Out)
$ci = [Globalization.CultureInfo]::InvariantCulture
while ($true) {
    $t = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
    $bpid = (Get-NetTCPConnection -State Listen -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object -First 1).OwningProcess
    $all = Get-CimInstance Win32_Process -Property ProcessId, ParentProcessId, Name, ExecutablePath
    $backend = @($all | Where-Object { $_.ProcessId -eq $bpid -or ($bpid -and $_.ProcessId -eq ($all | Where-Object ProcessId -eq $bpid).ParentProcessId -and $_.Name -eq 'python.exe') })
    $groups = @{
        backend = $backend.ProcessId
        llama   = ($all | Where-Object Name -eq 'llama-server.exe').ProcessId
        chromium = ($all | Where-Object { $_.ExecutablePath -like '*ms-playwright*' }).ProcessId
    }
    foreach ($g in $groups.Keys) {
        $ps = @($groups[$g] | Where-Object { $_ } | ForEach-Object { Get-Process -Id $_ -ErrorAction SilentlyContinue })
        $ws = ($ps | Measure-Object WorkingSet64 -Sum).Sum / 1MB
        $pv = ($ps | Measure-Object PrivateMemorySize64 -Sum).Sum / 1MB
        $cpu = ($ps | Measure-Object CPU -Sum).Sum
        Add-Content -Path $Out -Value ([string]::Format($ci, "{0},{1},{2},{3:F1},{4:F1},{5:F2}", $t, $g, $ps.Count, $ws, $pv, $cpu))
    }
    Start-Sleep -Milliseconds 1000
}
