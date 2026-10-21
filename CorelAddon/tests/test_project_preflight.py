"""Preflight: catch syntax problems in optional modules not imported by unit tests."""
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]


def test_every_python_file_is_syntactically_valid():
    sources = list(ROOT.rglob('*.py'))
    assert len(sources) >= 15
    for source in sources:
        compile(source.read_text(encoding='utf-8-sig'), str(source), 'exec')


def test_addon_xml_is_well_formed():
    folder = ROOT / 'CorelAddon/LaserToolsFree.Docker'
    for name in ('DockerUI.xaml','LaserToolsFree.Docker.csproj','AppUI.xslt','UserUI.xslt'):
        ET.parse(folder/name)


def test_dxf_samples_parse_and_audit():
    import ezdxf
    examples = list((ROOT/'Python_DXF/exemplos').glob('*.dxf'))
    assert len(examples) >= 3
    for file in examples:
        doc = ezdxf.readfile(file)
        errors = doc.audit().errors
        assert not errors, f'{file.name}: {errors}'
