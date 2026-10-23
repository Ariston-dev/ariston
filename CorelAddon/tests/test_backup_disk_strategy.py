from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=(ROOT/'LaserToolsFree.Docker/CorelService.cs').read_text(encoding='utf-8')
XAML=(ROOT/'LaserToolsFree.Docker/DockerUI.xaml').read_text(encoding='utf-8')
UI=(ROOT/'LaserToolsFree.Docker/DockerUI.xaml.cs').read_text(encoding='utf-8')
INSTALL=(ROOT.parent/'Distribuicao_Windows/INSTALAR_PLUGIN.ps1').read_text(encoding='utf-8-sig')


def test_backup_does_not_use_broken_corel_save_as_copy():
    assert 'doc.SaveAsCopy(' not in SRC
    assert 'File.Copy(original, destination, false)' in SRC
    assert 'Convert.ToBoolean(doc.Dirty)' in SRC
    assert 'documento' in SRC.lower()


def test_copy_action_has_backup_and_manual_save_precondition():
    assert SRC.index('string backup = Backup(doc)') < SRC.index('doc.BeginCommandGroup')
    assert 'Ctrl+S' in SRC
    assert 'public string TestBackup()' in SRC
    assert 'SavedCdrBackup.Copy' in SRC


def test_version_and_diagnostic_button():
    assert 'v5.1.7' in XAML
    assert 'BtnTestBackup_Click' in XAML and 'BtnTestBackup_Click' in UI
    assembly=(ROOT/'LaserToolsFree.Docker/Properties/AssemblyInfo.cs').read_text(encoding='utf-8')
    assert '5.1.6.0' in assembly


def test_windows_install_for_2022_unblocks_files_and_backs_up_old_dll():
    assert 'CorelDRAW Graphics Suite 2022' in INSTALL
    assert 'Get-ChildItem -LiteralPath $target -Recurse -File | Unblock-File' in INSTALL
    assert 'PluginBackups' in INSTALL


def test_windows_workflow_executes_compiled_corel_backup_smoke():
    workflow=(ROOT.parent/'.github/workflows/compilar-plugin-windows.yml').read_text(encoding='utf-8')
    assert 'BackupSmoke.csproj' in workflow
    assert 'BackupSmoke.exe' in workflow
    assert (ROOT/'tests/BackupSmoke/Program.cs').is_file()
