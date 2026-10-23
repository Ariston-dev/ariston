param([string]$CorelPrograms64 = '')
# Solicita elevacao somente para copiar/remover arquivos da pasta Programs64.
$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    $arguments = '-NoProfile -ExecutionPolicy Bypass -File "' + $PSCommandPath + '"'
    if ($CorelPrograms64) { $arguments += ' -CorelPrograms64 "' + $CorelPrograms64 + '"' }
    $child = Start-Process powershell.exe -Verb RunAs -Wait -PassThru -ArgumentList $arguments
    if ($child.ExitCode -ne 0) { throw 'Operação cancelada ou não concluída com privilégios administrativos.' }
    return
}
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$required = @('AppUI.xslt','UserUI.xslt','CorelDrw.addon','LaserToolsFree.Docker.dll','engine\LaserDXFEngine.exe','engine\LaserToolsFreeEditor.exe')
foreach ($file in $required) {
    if (-not (Test-Path (Join-Path $root $file))) { throw "Pacote INCOMPLETO. Falta: $file. Não use o ZIP de código-fonte como instalador." }
}
if (Get-Process -Name CorelDRW -ErrorAction SilentlyContinue) { throw 'Feche o CorelDRAW antes de instalar.' }
if (-not $CorelPrograms64) {
    $candidates = @(
        (Join-Path $env:ProgramFiles 'Corel\CorelDRAW Graphics Suite 2022\Programs64'),
        (Join-Path $env:ProgramFiles 'Corel\CorelDRAW Graphics Suite 2022\Programs'),
        (Join-Path $env:ProgramFiles 'Corel\CorelDRAW Graphics Suite 2024\Programs64'),
        (Join-Path $env:ProgramFiles 'Corel\CorelDRAW Graphics Suite 2024\Programs')
    )
    $CorelPrograms64 = $candidates | Where-Object { Test-Path (Join-Path $_ 'CorelDRW.exe') } | Select-Object -First 1
}
if (-not $CorelPrograms64 -or -not (Test-Path (Join-Path $CorelPrograms64 'CorelDRW.exe'))) {
    throw 'CorelDRAW 2022/2024 não encontrado automaticamente. Use -CorelPrograms64 com a pasta Programs64 que contém CorelDRW.exe.'
}
$target = Join-Path $CorelPrograms64 'Addons\LaserToolsFree'
Write-Host "Destino: $target" -ForegroundColor Cyan
# Antes de substituir, guardar a DLL instalada fora de Addons.
$oldDll = Join-Path $target 'LaserToolsFree.Docker.dll'
if (Test-Path $oldDll) {
    $backupDir = Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'LaserToolsFree\PluginBackups'
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
    $oldBackup = Join-Path $backupDir ('LaserToolsFree.Docker_' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff') + '.dll')
    Copy-Item -LiteralPath $oldDll -Destination $oldBackup -ErrorAction Stop
    Write-Host "DLL anterior guardada em: $oldBackup" -ForegroundColor Yellow
}
New-Item -ItemType Directory -Path (Join-Path $target 'engine') -Force | Out-Null
foreach ($file in @('AppUI.xslt','UserUI.xslt','CorelDrw.addon','LaserToolsFree.Docker.dll')) { Copy-Item (Join-Path $root $file) (Join-Path $target $file) -Force }
foreach ($file in @('LaserDXFEngine.exe','LaserToolsFreeEditor.exe')) { Copy-Item (Join-Path $root "engine\$file") (Join-Path $target "engine\$file") -Force }
# Arquivos obtidos do GitHub/ZIP podem carregar bloqueio de origem (Zone.Identifier),
# que produz o docker branco mesmo com a DLL correta. Desbloquear somente este addon.
Get-ChildItem -LiteralPath $target -Recurse -File | Unblock-File -ErrorAction Stop
[void][Reflection.AssemblyName]::GetAssemblyName((Join-Path $target 'LaserToolsFree.Docker.dll'))
Write-Host 'Copiados os arquivos do plugin. Nenhum CDR foi alterado.' -ForegroundColor Green
Write-Host 'Abra o CorelDRAW e procure Janela > Janelas de encaixe > Laser Tools Free.'
Write-Host 'Se não aparecer, NÃO redefina a área de trabalho sem backup das configurações.'
