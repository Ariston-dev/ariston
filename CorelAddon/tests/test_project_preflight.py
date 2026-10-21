"""Preflight for the *shipped* code, not stray source files in the repo root.

The GitHub repository can contain old Python prototypes at its root. Those are
not part of the Laser Tools Free distribution and should not fail the plugin
build. All Python under Python_DXF and CorelAddon is still syntax-checked.
"""
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIRS = ("Python_DXF", "CorelAddon")


def project_python_sources(root=ROOT):
    """Return all Python modules used by the current project, including tests."""
    sources = []
    for name in SOURCE_DIRS:
        directory = root / name
        if not directory.is_dir():
            raise AssertionError(f"Diretório obrigatório não encontrado: {directory}")
        sources.extend(directory.rglob("*.py"))
    return sorted(sources)


def test_every_project_python_file_is_syntactically_valid():
    sources = project_python_sources()
    assert len(sources) >= 15, "Arquivos Python esperados não encontrados."
    for source in sources:
        compile(source.read_text(encoding="utf-8-sig"), str(source), "exec")


def test_old_standalone_files_at_repo_root_are_not_part_of_plugin(tmp_path):
    """Regression for the 2026-10-21 Windows build failure.

    A stale root-level corel_panel_externo.py used to make ROOT.rglob('*.py')
    fail with IndentationError despite the distributed code being valid.
    """
    (tmp_path / "Python_DXF").mkdir()
    (tmp_path / "CorelAddon").mkdir()
    (tmp_path / "corel_panel_externo.py").write_text(
        "    invalid legacy indentation\n", encoding="utf-8"
    )
    (tmp_path / "Python_DXF" / "laser_cli.py").write_text(
        "print('ok')\n", encoding="utf-8"
    )
    (tmp_path / "CorelAddon" / "test_example.py").write_text(
        "value = 42\n", encoding="utf-8"
    )
    sources = project_python_sources(tmp_path)
    assert [p.name for p in sources] == ["test_example.py", "laser_cli.py"]
    for source in sources:
        compile(source.read_text(encoding="utf-8-sig"), str(source), "exec")


def test_addon_xml_is_well_formed():
    folder = ROOT / "CorelAddon/LaserToolsFree.Docker"
    for name in ("DockerUI.xaml", "LaserToolsFree.Docker.csproj", "AppUI.xslt", "UserUI.xslt"):
        ET.parse(folder / name)


def test_dxf_samples_parse_and_audit():
    import ezdxf

    examples = list((ROOT / "Python_DXF/exemplos").glob("*.dxf"))
    assert len(examples) >= 3
    for file in examples:
        doc = ezdxf.readfile(file)
        errors = doc.audit().errors
        assert not errors, f"{file.name}: {errors}"
