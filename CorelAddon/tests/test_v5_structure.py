from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]/'LaserToolsFree.Docker'


def test_manifest_and_source_files():
    for name in ['CorelDrw.addon','AppUI.xslt','UserUI.xslt','DockerUI.xaml',
                 'DockerUI.xaml.cs','CorelService.cs','EngineRunner.cs','LaserToolsFree.Docker.csproj']:
        assert (ROOT/name).is_file(),name
    for name in ['AppUI.xslt','UserUI.xslt','DockerUI.xaml','LaserToolsFree.Docker.csproj']:
        ET.parse(ROOT/name)


def test_xaml_handlers_have_implementations():
    xaml=ET.parse(ROOT/'DockerUI.xaml')
    code=(ROOT/'DockerUI.xaml.cs').read_text(encoding='utf-8')
    for el in xaml.iter():
        handler=el.attrib.get('Click')
        if handler: assert 'void '+handler+'(' in code,handler


def test_dll_hosted_type_and_csproj():
    app=(ROOT/'AppUI.xslt').read_text(encoding='utf-8')
    project=(ROOT/'LaserToolsFree.Docker.csproj').read_text(encoding='utf-8')
    assert 'LaserToolsFree.Docker.dll,LaserToolsFree.Docker.DockerUI' in app
    assert 'EngineRunner.cs' in project
    assert 'System.Web.Extensions' in project
    assert 'TargetFrameworkVersion>v4.8' in project


def test_corel_import_protects_original_objects():
    service=(ROOT/'CorelService.cs').read_text(encoding='utf-8')
    assert 'SavedCdrBackup.Copy' in service
    assert 'CreateLayer' in service
    assert 'layer.ImportEx' in service
    assert 'layer.Shapes.Count' in service
    assert 'EndCommandGroup' in service
