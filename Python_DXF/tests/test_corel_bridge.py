from pathlib import Path
from types import SimpleNamespace
import pytest

from corel_bridge import (CorelBridgeError, duplicate_grid, inspect_selection,
                          get_selection, MAX_COPIES)


class FakeSelection:
    Count = 2
    SizeWidth = 10.0
    SizeHeight = 8.0

    def __init__(self, fail_on=0):
        self.calls = []
        self.fail_on=fail_on

    def Duplicate(self, x, y):
        if self.fail_on and len(self.calls)+1 == self.fail_on:
            raise RuntimeError('Erro simulado no CorelDRAW')
        self.calls.append((x, y))


class FakeDoc:
    Name='Aula teste.cdr'
    Unit=3

    def __init__(self, selected=None, fail_save=False):
        self.SelectionRange = selected or FakeSelection()
        self.fail_save=fail_save
        self.begins=[]
        self.ends=0
        self.saved=[]

    def SaveAsCopy(self, name):
        if self.fail_save:
            raise RuntimeError('Sem acesso')
        Path(name).write_bytes(b'CDR simulado, NAO e um CDR real')
        self.saved.append(name)

    def BeginCommandGroup(self, name):
        self.begins.append(name)

    def EndCommandGroup(self):
        self.ends+=1


def test_corel_read_only_selection():
    doc=FakeDoc()
    app=SimpleNamespace(ActiveDocument=doc)
    result=inspect_selection(app)
    assert result.name=='Aula teste.cdr'
    assert result.count==2
    assert result.width==10
    assert result.unit==3
    assert not doc.begins and not doc.saved


def test_no_selection_rejected():
    doc=FakeDoc()
    doc.SelectionRange.Count=0
    with pytest.raises(CorelBridgeError, match='Selecione'):
        get_selection(SimpleNamespace(ActiveDocument=doc))


def test_backup_before_create_grid_and_offsets(tmp_path):
    doc=FakeDoc()
    app=SimpleNamespace(ActiveDocument=doc)
    path,n=duplicate_grid(app,2,3,3.0,tmp_path)
    assert n==5
    assert path.name.startswith('Aula teste_laser_backup_')
    assert path.exists()
    assert doc.saved==[str(path)]
    assert doc.SelectionRange.calls==[(13.0,0.0),(26.0,0.0),(0.0,-11.0),(13.0,-11.0),(26.0,-11.0)]
    assert len(doc.begins)==doc.ends==1


def test_backup_failure_prevents_edit(tmp_path):
    doc=FakeDoc(fail_save=True)
    with pytest.raises(CorelBridgeError,match='Backup falhou'):
        duplicate_grid(SimpleNamespace(ActiveDocument=doc),2,3,3,tmp_path)
    assert doc.SelectionRange.calls==[]
    assert doc.begins==[]


def test_unit_error_prevents_backup_or_edit(tmp_path):
    doc=FakeDoc();doc.Unit=1
    with pytest.raises(CorelBridgeError,match='milímetros'):
        duplicate_grid(SimpleNamespace(ActiveDocument=doc),2,3,3,tmp_path)
    assert doc.saved==[]


def test_max_copies_validation(tmp_path):
    doc=FakeDoc()
    with pytest.raises(CorelBridgeError,match='1 a'):
        duplicate_grid(SimpleNamespace(ActiveDocument=doc),11,10,3,tmp_path)
    assert doc.saved==[]


def test_error_always_ends_command_group_and_backed_up(tmp_path):
    selected=FakeSelection(fail_on=2)
    doc=FakeDoc(selected)
    with pytest.raises(CorelBridgeError,match='Ctrl\\+Z'):
        duplicate_grid(SimpleNamespace(ActiveDocument=doc),2,2,1,tmp_path)
    assert len(doc.saved)==1
    assert selected.calls==[(11.0,0.0)]
    assert doc.ends==1


def test_one_piece_no_backup(tmp_path):
    doc=FakeDoc()
    with pytest.raises(CorelBridgeError,match='pelo menos 2'):
        duplicate_grid(SimpleNamespace(ActiveDocument=doc),1,1,3,tmp_path)
    assert not doc.saved
