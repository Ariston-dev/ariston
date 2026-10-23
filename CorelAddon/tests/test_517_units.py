"""Verificacoes preventivas do bug de unidade 1 (polegadas) no CorelDRAW 2022.
Estes testes nao substituem o CorelDRAW real.
"""
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / "LaserToolsFree.Docker"
SERVICE = (BASE / "CorelService.cs").read_text(encoding="utf-8")
UI = (BASE / "DockerUI.xaml.cs").read_text(encoding="utf-8")
CALC = (BASE / "Calculations.cs").read_text(encoding="utf-8")


def test_old_unit_barrier_removed_from_common_edit_and_export():
    assert "RequireMillimeter" not in SERVICE
    assert "Esta ferramenta DXF exige documento em mm" not in SERVICE
    assert "doc.Unit =" not in SERVICE  # nao alterar unidade do documento


def test_resize_transforms_mm_to_document_unit_before_setsize():
    resize = SERVICE.split("public string Resize(", 1)[1].split("public string Rotate90(", 1)[0]
    assert "MmToDocumentUnits(width, s.Unit)" in resize
    assert "MmToDocumentUnits(height, s.Unit)" in resize
    assert "selection.SetSize(widthInDoc, heightInDoc)" in resize


def test_rotate_does_not_require_document_millimeters():
    rotate = SERVICE.split("public string Rotate90(", 1)[1].split("internal static class SavedCdrBackup", 1)[0]
    assert 'RunEdit("Girar 90 graus"' in rotate
    assert "RequireMillimeter" not in rotate


def test_displayed_selection_sizes_are_actual_mm():
    assert "DocumentUnitsToMm(s.Width, s.Unit)" in UI
    assert "DocumentUnitsToMm(s.Height, s.Unit)" in UI
    assert "TxtWidth.Text = Calculations.Mm(widthMm)" in UI
    assert "TxtHeight.Text = Calculations.Mm(heightMm)" in UI
    assert "case 1: return value * 25.4;" in CALC


def test_dxf_output_requires_explicit_mm_and_input_metric_scale():
    export = SERVICE.split("public string ExportSelectionDxf(", 1)[1].split("public string ImportResultAsNewLayer(", 1)[0]
    assert "exportFilter.Units = 3;" in export
    assert "Exportacao cancelada para evitar escala incorreta" in export
    assert "filter.Scaling = 2;" in SERVICE
    assert "metric" in SERVICE.lower()


def test_csharp_smoke_includes_proportions_and_backups():
    smoke = (BASE.parent / "tests" / "BackupSmoke" / "Program.cs").read_text(encoding="utf-8")
    for item in ["service.Grid(2, 3, 3.0)", "service.Resize(50, 40)", "service.Rotate90(90)", "service.ExportSelectionDxf()", "service.ImportResultAsNewLayer(inchExport", "document.Unit == 1", "BytesEqual(File.ReadAllBytes(original), contents)"]:
        assert item in smoke
