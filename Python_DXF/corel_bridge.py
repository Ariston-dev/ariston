"""Prova de conceito: integração EXTERNA do Python com CorelDRAW 2024 via COM.

Sem VBA. Esta não é uma extensão/dockable panel nativa. Não importamos
win32com no módulo: testes podem executar no Linux com dublês COM.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import math

MM_UNIT = 3  # cdrMillimeter, CorelDRAW 2024 API
MAX_COPIES = 100


class CorelBridgeError(RuntimeError):
    pass


@dataclass(frozen=True)
class SelectionInfo:
    name: str
    count: int
    width: float
    height: float
    unit: int


def connect():
    """Somente se conecta a uma instância de CorelDRAW já em execução."""
    try:
        import pythoncom
        import win32com.client
    except ImportError as exc:
        raise CorelBridgeError('Instale pywin32: py -m pip install pywin32') from exc
    pythoncom.CoInitialize()
    try:
        app = win32com.client.GetActiveObject('CorelDRAW.Application')
        # Acessar propriedade para validar que a sessão está pronta.
        _ = app.Version
        return app
    except Exception as exc:
        raise CorelBridgeError('CorelDRAW não encontrado. Abra o CorelDRAW 2024 e um documento CDR.') from exc


def get_selection(app):
    try:
        doc = app.ActiveDocument
        if doc is None:
            raise CorelBridgeError('Abra um documento no CorelDRAW.')
        selection = doc.SelectionRange
        if int(selection.Count) <= 0:
            raise CorelBridgeError('Selecione pelo menos um objeto no CorelDRAW.')
        return doc, selection
    except CorelBridgeError:
        raise
    except Exception as exc:
        raise CorelBridgeError('Não foi possível ler a seleção atual do CorelDRAW.') from exc


def inspect_selection(app):
    doc, selected = get_selection(app)
    return SelectionInfo(
        name=str(getattr(doc, 'Name', 'Sem nome')),
        count=int(selected.Count),
        width=float(selected.SizeWidth),
        height=float(selected.SizeHeight),
        unit=int(doc.Unit),
    )


def _check_grid(rows, columns, gap_mm, info):
    if info.unit != MM_UNIT:
        raise CorelBridgeError('Defina a unidade do documento como milímetros (mm) no CorelDRAW antes de copiar.')
    if rows < 1 or columns < 1 or rows * columns > MAX_COPIES:
        raise CorelBridgeError(f'Use de 1 a {MAX_COPIES} peças (linhas × colunas).')
    if not (math.isfinite(gap_mm) and 0 <= gap_mm <= 10000):
        raise CorelBridgeError('O espaçamento deve estar entre 0 e 10000 mm.')
    if not (math.isfinite(info.width) and math.isfinite(info.height)
            and info.width > 0 and info.height > 0):
        raise CorelBridgeError('A seleção precisa ter dimensões válidas e não nulas.')


def _unused_path(directory, stem):
    directory = Path(directory).expanduser()
    if not directory.is_dir():
        raise CorelBridgeError('Selecione uma pasta de backup existente.')
    # Criar nome diferente em todas as tentativas; nunca substituir.
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    base = directory / f'{stem}_laser_backup_{stamp}.cdr'
    if not base.exists():
        return base
    idx = 2
    while True:
        path = directory / f'{stem}_laser_backup_{stamp}_{idx}.cdr'
        if not path.exists():
            return path
        idx += 1


def _safe_filename(name):
    # Não admitir caminhos/nomes que escapem da pasta escolhida.
    return ''.join(ch if ch.isalnum() or ch in '._- ' else '_' for ch in str(name))[:80].rstrip('.') or 'Documento'


def save_backup(doc, backup_folder):
    name = _safe_filename(Path(str(getattr(doc, 'Name', 'Desenho'))).stem)
    path = _unused_path(backup_folder, name)
    try:
        # SaveAsCopy cria a cópia sem alterar o destino do CDR em edição.
        doc.SaveAsCopy(str(path))
    except Exception as exc:
        raise CorelBridgeError(f'Backup falhou. Nada foi alterado pelo Laser Tools Free. Detalhes: {exc}') from exc
    if not path.is_file() or path.stat().st_size == 0:
        # Fail closed, mesmo se Corel retornar sucesso mas salvar fora do local.
        raise CorelBridgeError('CorelDRAW não confirmou um backup CDR válido. Operação cancelada.')
    return path


@contextmanager
def _undo_group(doc, name):
    """Fecha BeginCommandGroup sempre, inclusive após falha.

    A interface deve usar Ctrl+Z se houve falha parcial, já que EndCommandGroup
    não desfaz automaticamente a operação.
    """
    doc.BeginCommandGroup(name)
    try:
        yield
    finally:
        doc.EndCommandGroup()


def duplicate_grid(app, rows, columns, gap_mm, backup_folder):
    """Duplica a seleção como conjunto, sem exportar DXF.

    Retorna o caminho do backup e a contagem de cópias NOVAS.
    Preserva objetos originais. Altera apenas o documento em memória,
    que pode ser desfeito por Ctrl+Z; não salva o CDR alterado.
    """
    doc, original = get_selection(app)
    info = inspect_selection(app)
    _check_grid(rows, columns, gap_mm, info)
    if rows * columns == 1:
        raise CorelBridgeError('Escolha pelo menos 2 peças para gerar cópias.')
    backup_path = save_backup(doc, backup_folder)
    created = 0
    try:
        with _undo_group(doc, 'Laser Tools Free - Grade de cópias'):
            # Cada cópia vem SEMPRE do grupo originalmente selecionado.
            # O eixo Y do Corel é positivo para cima, portanto descemos com -y.
            for r in range(rows):
                for c in range(columns):
                    if r == 0 and c == 0:
                        continue
                    dx = c * (info.width + gap_mm)
                    dy = -r * (info.height + gap_mm)
                    original.Duplicate(dx, dy)
                    created += 1
    except Exception as exc:
        raise CorelBridgeError(
            f'Falha após criar {created} cópia(s). Backup: {backup_path}. '
            'Use Ctrl+Z no CorelDRAW para reverter o grupo de operações. '
            f'Detalhes: {exc}'
        ) from exc
    return backup_path, created
