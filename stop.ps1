$procs = Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -like '*run.py*' }
if ($procs) {
  $procs | ForEach-Object {
    Write-Host ("Stopping PID " + $_.ProcessId)
    Stop-Process -Id $_.ProcessId -Force
  }
} else {
  Write-Host 'Echo is not running.'
}
Start-Sleep -Seconds 1
