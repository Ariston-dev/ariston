param([string]$CorelPrograms64 = '')
# Solicita elevacao somente para copiar/remover arquivos da pasta Programs64.
$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    $arguments = '-NoProfile -ExecutionPolicy Bypass -File "' + $PSCommandPath + '"'
    $child = Start-Process powershell.exe -Verb RunAs -Wait -PassThru -ArgumentList $arguments
    if ($child.ExitCode -ne 0) { throw 'Operação cancelada ou não concluída com privilégios administrativos.' }
    return
}
$ErrorActionPreference = 'Stop'
if (Get-Process -Name CorelDRW -ErrorAction SilentlyContinue) { throw 'Feche o CorelDRAW antes de desinstalar.' }
if (-not $CorelPrograms64) {
  $candidates = @(
    (Join-Path $env:ProgramFiles 'Corel\CorelDRAW Graphics Suite 2024\Programs64'),
    (Join-Path $env:ProgramFiles 'Corel\CorelDRAW Graphics Suite 2024\Programs')
  )
  $CorelPrograms64 = $candidates | Where-Object { Test-Path (Join-Path $_ 'CorelDRW.exe') } | Select-Object -First 1
}
if (-not $CorelPrograms64) { throw 'CorelDRAW 2024 não localizado.' }
$target = Join-Path $CorelPrograms64 'Addons\LaserToolsFree'
if (Test-Path $target) { Remove-Item -LiteralPath $target -Recurse -Force }
Write-Host 'Pasta do complemento removida; backups e documentos preservados.'
