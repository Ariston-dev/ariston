"""Guards against regression to an opaque, all-white WPF panel.
This is a source contract check, NOT an in-CorelDRAW runtime test.
"""
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / 'LaserToolsFree.Docker' / 'DockerUI.xaml.cs'


def test_supports_host_variations_and_logs_wpf_errors():
    code = SOURCE.read_text(encoding='utf-8')
    assert 'public DockerUI() : this(null)' in code
    assert 'public DockerUI(object application)' in code
    assert 'InitializeComponent();' in code
    assert 'catch (Exception ex)' in code
    assert 'Docker_WPF.log' in code
    assert 'Content = new Border' in code
    assert 'Marshal.GetActiveObject("CorelDRAW.Application.24")' in code


def test_corel_operations_resolve_application_lazily():
    code = SOURCE.read_text(encoding='utf-8')
    assert 'private CorelService Corel' in code
    assert 'Corel.Inspect()' in code
    assert 'Corel.Grid(' in code
    assert 'Corel.ExportSelectionDxf()' in code


def test_windows_build_smokes_actual_wpf_xaml():
    root = SOURCE.parents[2]
    workflow = (root / '.github' / 'workflows' / 'compilar-plugin-windows.yml').read_text(encoding='utf-8')
    ps = (root / 'CorelAddon' / 'tools' / 'Testar-Painel-WPF.ps1').read_text(encoding='utf-8')
    assert 'Testar-Painel-WPF.ps1' in workflow
    assert "Activator]::CreateInstance" in ps
    assert 'System.Windows.Controls.Grid' in ps
    assert 'TxtStatus' in ps
