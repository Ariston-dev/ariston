"""Valida estrutura XML e contratos do protótipo; não substitui teste no CorelDRAW."""
from pathlib import Path
import re
import unittest
from lxml import etree

# A API Corel usa xmlns:frmwrk="Corel Framework Data" (com espacos),
# rejeitado por parsers XML estritos como lxml sem recover=True.
COREL_PARSER = etree.XMLParser(recover=True)
BASE = Path(__file__).resolve().parents[1] / 'LaserToolsFree.Docker'
ROOT = BASE.parents[1]

class DockerManifestTests(unittest.TestCase):
    def test_manifest_parses_as_xml(self):
        for name in ('AppUI.xslt', 'UserUI.xslt', 'DockerUI.xaml', 'LaserToolsFree.Docker.csproj'):
            with self.subTest(name=name):
                etree.parse(str(BASE / name), COREL_PARSER)

    def test_appui_registers_docker_and_controls(self):
        transform = etree.XSLT(etree.parse(str(BASE / 'AppUI.xslt'), COREL_PARSER))
        doc = etree.fromstring(b'<uiConfig><items/><dockers/></uiConfig>')
        result = transform(doc)
        root = result.getroot()
        self.assertEqual(len(root.xpath('./items/itemData[@type="wpfhost"]')), 1)
        self.assertEqual(len(root.xpath('./dockers/dockerData')), 1)
        wpf = root.xpath('./items/itemData[@type="wpfhost"]')[0]
        self.assertEqual(wpf.get('hostedType'),
                         r'Addons\LaserToolsFree\LaserToolsFree.Docker.dll,LaserToolsFree.Docker.DockerUI')
        hosted = root.xpath('./dockers/dockerData/container/item')[0]
        self.assertEqual(hosted.get('guidRef'), wpf.get('guid'))

    def test_userui_adds_only_once(self):
        transform = etree.XSLT(etree.parse(str(BASE / 'UserUI.xslt'), COREL_PARSER))
        guid = '3eaa9bbe-28fd-4672-9128-02974ee96332'
        xml = etree.fromstring(f'<uiConfig><commandBars><commandBarData guid="{guid}"><menu/></commandBarData></commandBars><frame/></uiConfig>'.encode())
        once = transform(xml)
        twice = transform(once)
        for result in (once, twice):
            self.assertEqual(len(result.xpath('//commandBarData/menu/item[@guidRef="b4e1c580-9389-4985-a754-b48e22df009a"]')), 1)

    def test_xaml_events_declared(self):
        xml = etree.parse(str(BASE / 'DockerUI.xaml'))
        clicks = set(xml.xpath('//@Click'))
        code = (BASE / 'DockerUI.xaml.cs').read_text(encoding='utf-8')
        for event in clicks:
            with self.subTest(event=event):
                self.assertRegex(code, r'\b' + re.escape(event) + r'\s*\(')

    def test_backup_before_edit_and_no_automatic_save(self):
        code = (BASE / 'CorelService.cs').read_text(encoding='utf-8')
        self.assertLess(code.index('string backup = Backup(doc)'), code.index('doc.BeginCommandGroup'))
        self.assertIn('doc.SaveAsCopy(path)', code)
        self.assertNotIn('doc.Save();', code)
        self.assertIn('exportFilter.Finish()', code)
        self.assertIn('doc.ExportEx(filename, 1296, 2)', code)

    def test_sources_and_previous_versions_present(self):
        self.assertTrue((ROOT / 'Python_DXF' / 'laser_core.py').is_file())
        self.assertTrue((ROOT / 'Python_DXF' / 'corel_bridge.py').is_file())
        self.assertTrue((ROOT / 'Python_DXF' / 'versao_2_original' / 'laser_tools_free.py').is_file())

if __name__ == '__main__':
    unittest.main()
