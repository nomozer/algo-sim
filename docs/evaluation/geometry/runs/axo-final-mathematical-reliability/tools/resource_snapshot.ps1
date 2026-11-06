param([string]$Phase = 'checkpoint')
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public class AxoResourceSnapshot {
  [StructLayout(LayoutKind.Sequential)] public struct State {
    public uint size, load;
    public ulong total, available, pageTotal, pageAvailable, virtualTotal, virtualAvailable, extended;
  }
  [DllImport("kernel32.dll")] static extern bool GlobalMemoryStatusEx(ref State s);
  [DllImport("kernel32.dll")] static extern bool GetSystemTimes(out ulong idle, out ulong kernel, out ulong user);
  public static State Memory() { var s=new State(); s.size=(uint)Marshal.SizeOf(s); GlobalMemoryStatusEx(ref s); return s; }
  public static ulong[] Times() { ulong i,k,u; GetSystemTimes(out i,out k,out u); return new ulong[] {i,k,u}; }
}
'@
$before = [AxoResourceSnapshot]::Times()
Start-Sleep -Milliseconds 250
$after = [AxoResourceSnapshot]::Times()
$elapsed = ($after[1]-$before[1])+($after[2]-$before[2])
$memory = [AxoResourceSnapshot]::Memory()
[ordered]@{
  phase = $Phase
  utc = [DateTime]::UtcNow.ToString('o')
  total_ram_gib = [Math]::Round($memory.total/1GB, 3)
  available_ram_gib = [Math]::Round($memory.available/1GB, 3)
  memory_load_percent = $memory.load
  cpu_percent_250ms_sample = $(if ($elapsed -gt 0) { [Math]::Round(100*(1-($after[0]-$before[0])/$elapsed),2) } else { $null })
  processes = @(Get-Process node,python,chrome -ErrorAction SilentlyContinue | ForEach-Object {
    [ordered]@{pid=$_.Id; name=$_.ProcessName; cpu_seconds=$_.CPU; working_set_mib=[Math]::Round($_.WorkingSet64/1MB,1)}
  })
} | ConvertTo-Json -Depth 4 -Compress
