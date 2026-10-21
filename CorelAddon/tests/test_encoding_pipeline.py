"""Regression tests for GitHub Windows cp1252/UTF-8 interoperability."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_utf8_contract_is_explicit_everywhere():
    cli = (ROOT / 'Python_DXF' / 'laser_cli.py').read_text(encoding='utf-8')
    reader = (ROOT / 'CorelAddon' / 'LaserToolsFree.Docker' / 'EngineRunner.cs').read_text(encoding='utf-8')
    tests = (ROOT / 'Python_DXF' / 'tests' / 'test_advanced.py').read_text(encoding='utf-8')
    workflow = (ROOT / '.github' / 'workflows' / 'compilar-plugin-windows.yml').read_text(encoding='utf-8')
    assert "sys.stdout.reconfigure(encoding='utf-8'" in cli
    assert 'StandardOutputEncoding=Encoding.UTF8' in reader
    assert 'StandardErrorEncoding=Encoding.UTF8' in reader
    assert "encoding='utf-8', errors='strict'" in tests
    assert "PYTHONUTF8: '1'" in workflow
    assert "PYTHONIOENCODING: 'utf-8'" in workflow
    assert 'needs: [testes, painel, executaveis]' in workflow


def test_build_jobs_are_separate():
    import yaml
    workflow = yaml.load((ROOT / '.github' / 'workflows' / 'compilar-plugin-windows.yml').read_text(encoding='utf-8'), Loader=yaml.BaseLoader)
    assert {'testes', 'painel', 'executaveis', 'empacotar'} == set(workflow['jobs'])
    assert set(workflow['jobs']['empacotar']['needs']) == {'testes','painel','executaveis'}
    assert workflow['jobs']['painel']['runs-on'] == 'windows-2022'
