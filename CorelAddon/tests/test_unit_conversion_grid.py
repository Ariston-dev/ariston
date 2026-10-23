"""Guardas de código para o bug de unidades no botão Cópias.
Não substituem a compilação C# e o teste dentro do CorelDRAW 2022.
"""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1] / "LaserToolsFree.Docker"

def test_mm_conversions_defined_for_corel_2022():
    source=(ROOT / "Calculations.cs").read_text(encoding="utf-8")
    for token in ["case 3: return millimeters;", "case 4: return millimeters / 10.0;", "case 1: return millimeters / 25.4;", "default:"]:
        assert token in source

def test_grid_converts_gap_without_changing_document_units():
    source=(ROOT / "CorelService.cs").read_text(encoding="utf-8")
    grid=source.split("public string Grid(",1)[1].split("public string Resize(",1)[0]
    assert "MmToDocumentUnits(gapMm, s.Unit)" in grid
    assert "gapInDocumentUnits" in grid
    assert "requireMillimeters: false" in grid
    assert "doc.Unit =" not in grid
    assert "Backup" not in grid or "RunEdit" in grid

def test_panel_displays_internal_units():
    source=(ROOT / "DockerUI.xaml.cs").read_text(encoding="utf-8")
    assert "Unidade interna:" in source
    assert 's.Unit == 4 ? "cm"' in source

