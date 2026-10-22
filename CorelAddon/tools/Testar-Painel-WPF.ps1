param([Parameter(Mandatory=$true)][string]$AssemblyPath)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName PresentationFramework
$path = (Resolve-Path -LiteralPath $AssemblyPath).Path
$assembly = [Reflection.Assembly]::LoadFrom($path)
$type = $assembly.GetType('LaserToolsFree.Docker.DockerUI', $true)
$control = [Activator]::CreateInstance($type)
if (-not ($control -is [System.Windows.Controls.UserControl])) {
    throw 'O tipo compilado nao e um UserControl do WPF.'
}
if (-not ($control.Content -is [System.Windows.Controls.Grid])) {
    throw 'A interface WPF nao carregou o Grid principal. Verifique Documentos/LaserToolsFree/Logs/Docker_WPF.log.'
}
$status = $control.FindName('TxtStatus')
if ($null -eq $status -or $status.Text -notmatch '^Painel carregado') {
    throw 'O rodape da interface nao foi inicializado pelo XAML.'
}
Write-Host 'TESTE WPF OK: controle instanciado, XAML carregado e status visivel.'
