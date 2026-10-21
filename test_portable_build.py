from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

def test_portable_runner_targets_compiled_exe():
    source=(ROOT/'CorelAddon/LaserToolsFree.Docker/EngineRunner.cs').read_text(encoding='utf-8')
    assert 'LaserDXFEngine.exe' in source
    assert 'python_path.txt' not in source
    assert 'Quote(operation)' in source
    assert 'laser_cli.py' not in source

def test_portable_gui_targets_compiled_exe():
    source=(ROOT/'CorelAddon/LaserToolsFree.Docker/DockerUI.xaml.cs').read_text(encoding='utf-8')
    assert 'LaserToolsFreeEditor.exe' in source
    assert 'ProcessSelection' in source

def test_workflow_builds_both_windows_bins():
    yaml=(ROOT/'.github/workflows/compilar-plugin-windows.yml').read_text(encoding='utf-8')
    assert 'runs-on: windows-2022' in yaml
    assert 'LaserToolsFree.Docker.csproj' in yaml
    assert '--name LaserDXFEngine' in yaml
    assert '--name LaserToolsFreeEditor' in yaml
    assert 'actions/upload-artifact' in yaml

def test_installer_only_targets_plugin_directory():
    script=(ROOT/'Distribuicao_Windows/INSTALAR_PLUGIN.ps1').read_text(encoding='utf-8')
    assert "'Addons\\LaserToolsFree'" in script
    assert 'CorelDRW.exe' in script
    assert 'LaserDXFEngine.exe' in script
    assert 'LaserToolsFreeEditor.exe' in script
    assert 'INSTALAR_TUDO' not in script
