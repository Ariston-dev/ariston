"""
Laser Tools Free v2 — ferramentas independentes para preparar desenhos DXF.
Não é afiliado ao eCut e não contém código proprietário do eCut.

Ferramentas:
1) Limpeza de linhas LINE duplicadas.
2) Relatório de entidades e dimensões aproximadas do desenho.
3) Redimensionar DXF por escala X/Y em porcentagem.
4) Multiplicar cópias de entidades no espaço do modelo, com espaçamento.
5) Exportar uma cópia DXF mantendo o original.

Limitações:
- A limpeza automática trata somente entidades LINE simples.
- Relatório e cópia/escala/multiplicação funcionam com as entidades que a biblioteca ezdxf consegue transformar.
- Unidades DXF podem estar indefinidas; confirme se o desenho está em mm.
- Não substitui as ferramentas de nesting/offset/otimização do eCut.
- Confira todo arquivo antes de enviar ao laser.
"""

import math
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

try:
    import ezdxf
    from ezdxf import bbox
    from ezdxf.math import Matrix44
except ImportError:
    ezdxf = None
    bbox = None
    Matrix44 = None

TITLE = "Laser Tools Free v2 — Preparador DXF"


def pkey(point, decimals=4):
    return tuple(round(float(v), decimals) for v in point[:3])


def line_key(entity, decimals=4):
    return tuple(sorted((pkey(entity.dxf.start, decimals), pkey(entity.dxf.end, decimals))))


def clean_lines(input_path, decimals=4):
    doc = ezdxf.readfile(input_path)
    msp = doc.modelspace()
    seen, duplicate_entities = set(), []
    lines_seen = 0
    for ent in list(msp):
        if ent.dxftype() != "LINE":
            continue
        lines_seen += 1
        a, b = pkey(ent.dxf.start, decimals), pkey(ent.dxf.end, decimals)
        if a == b:
            continue
        key = line_key(ent, decimals)
        if key in seen:
            duplicate_entities.append(ent)
        else:
            seen.add(key)
    for ent in duplicate_entities:
        msp.delete_entity(ent)
    out = safe_output(input_path, "_sem_duplicadas")
    doc.saveas(out)
    return out, lines_seen, len(duplicate_entities)


def safe_output(input_path, suffix):
    source = Path(input_path)
    output = source.with_name(source.stem + suffix + source.suffix)
    n = 2
    while output.exists():
        output = source.with_name(f"{source.stem}{suffix}_{n}{source.suffix}")
        n += 1
    return output


def get_report(input_path):
    doc = ezdxf.readfile(input_path)
    msp = doc.modelspace()
    counts = {}
    for ent in msp:
        counts[ent.dxftype()] = counts.get(ent.dxftype(), 0) + 1
    ext = bbox.extents(msp, fast=True)
    if ext.has_data:
        mn, mx = ext.extmin, ext.extmax
        width, height = mx.x - mn.x, mx.y - mn.y
        depth = mx.z - mn.z
    else:
        width = height = depth = 0
    return counts, width, height, depth


def transform_dxf(input_path, scale_x, scale_y, copies, gap_x, gap_y):
    doc = ezdxf.readfile(input_path)
    msp = doc.modelspace()
    original_entities = list(msp)
    if not original_entities:
        raise ValueError("O DXF não contém entidades no espaço do modelo.")

    # Scale around origin; user's DXF is expected to be drawn from a suitable origin.
    sx, sy = scale_x / 100.0, scale_y / 100.0
    for ent in original_entities:
        try:
            ent.transform(Matrix44.scale(sx, sy, 1))
        except Exception:
            # Unsupported entities are left untouched; user is warned in UI.
            pass

    # Duplicate the transformed original geometry with offset based on its bounding box.
    ext = bbox.extents(msp, fast=True)
    if not ext.has_data:
        raise ValueError("Não foi possível calcular os limites do desenho.")
    width = ext.extmax.x - ext.extmin.x
    height = ext.extmax.y - ext.extmin.y
    transformed_originals = list(msp)
    for i in range(1, copies):
        dx = i * (width + gap_x)
        dy = i * gap_y
        for ent in transformed_originals:
            try:
                clone = ent.copy()
                clone.transform(Matrix44.translate(dx, dy, 0))
                msp.add_entity(clone)
            except Exception:
                pass

    out = safe_output(input_path, "_escala_copias")
    doc.saveas(out)
    return out, len(original_entities), copies


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(TITLE)
        self.geometry("800x650")
        self.minsize(690, 560)
        self.file_var = tk.StringVar()
        self.precision = tk.StringVar(value="4")
        self.sx = tk.StringVar(value="100")
        self.sy = tk.StringVar(value="100")
        self.copies = tk.StringVar(value="1")
        self.gapx = tk.StringVar(value="5")
        self.gapy = tk.StringVar(value="0")
        self.status = tk.StringVar(value="Selecione um DXF exportado do CorelDRAW.")
        self.build()

    def build(self):
        root = ttk.Frame(self, padding=18)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text="Laser Tools Free", font=("Segoe UI", 20, "bold")).pack(anchor="w")
        ttk.Label(root, text="Utilitários independentes para preparar arquivos de corte a laser", font=("Segoe UI", 10)).pack(anchor="w", pady=(0, 12))

        file_row = ttk.Frame(root)
        file_row.pack(fill="x", pady=(0, 12))
        ttk.Label(file_row, text="Arquivo DXF:").pack(side="left")
        ttk.Entry(file_row, textvariable=self.file_var).pack(side="left", fill="x", expand=True, padx=8)
        ttk.Button(file_row, text="Procurar…", command=self.choose).pack(side="left")

        nb = ttk.Notebook(root)
        nb.pack(fill="both", expand=True)

        clean_tab = ttk.Frame(nb, padding=14)
        nb.add(clean_tab, text="Limpar duplicatas")
        ttk.Label(clean_tab, text="Remove entidades LINE com os mesmos extremos (também reconhece direção invertida).").pack(anchor="w")
        row = ttk.Frame(clean_tab)
        row.pack(anchor="w", pady=10)
        ttk.Label(row, text="Precisão decimal:").pack(side="left")
        ttk.Combobox(row, textvariable=self.precision, values=("3", "4", "5", "6"), state="readonly", width=6).pack(side="left", padx=8)
        ttk.Button(clean_tab, text="Limpar e salvar nova cópia", command=self.clean).pack(anchor="w", pady=6)
        ttk.Label(clean_tab, text="Limitação: não processa linhas dentro de polilinhas nem arcos/círculos/splines; não detecta sobreposição parcial.", wraplength=690).pack(anchor="w", pady=8)

        report_tab = ttk.Frame(nb, padding=14)
        nb.add(report_tab, text="Relatório")
        ttk.Label(report_tab, text="Mostra quantidade por tipo de entidade e dimensões aproximadas do desenho.").pack(anchor="w", pady=(0, 10))
        ttk.Button(report_tab, text="Gerar relatório", command=self.report).pack(anchor="w")
        self.report_box = tk.Text(report_tab, height=16, wrap="word")
        self.report_box.pack(fill="both", expand=True, pady=10)
        self.report_box.insert("1.0", "O relatório aparecerá aqui.\n")
        self.report_box.configure(state="disabled")

        transform_tab = ttk.Frame(nb, padding=14)
        nb.add(transform_tab, text="Escala e cópias")
        ttk.Label(transform_tab, text="Cria uma nova cópia do DXF com escala X/Y e cópias espaçadas. Confirme as unidades antes de usar.").pack(anchor="w", pady=(0, 10))
        form = ttk.Frame(transform_tab)
        form.pack(anchor="w")
        fields = [
            ("Escala X (%)", self.sx), ("Escala Y (%)", self.sy),
            ("Número total de cópias", self.copies), ("Espaço X (unidades DXF)", self.gapx),
            ("Espaço Y (unidades DXF)", self.gapy),
        ]
        for i, (label, var) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=i, column=0, sticky="w", padx=(0, 12), pady=5)
            ttk.Entry(form, textvariable=var, width=14).grid(row=i, column=1, sticky="w", pady=5)
        ttk.Button(transform_tab, text="Gerar novo DXF", command=self.transform).pack(anchor="w", pady=12)
        ttk.Label(transform_tab, text="A escala é aplicada ao redor da origem (0,0). Cópias são colocadas em linha no eixo X. Confira a posição no RDWorks.", wraplength=690).pack(anchor="w")

        about_tab = ttk.Frame(nb, padding=14)
        nb.add(about_tab, text="Sobre")
        ttk.Label(about_tab, text=(
            "Laser Tools Free v2\n\n"
            "Projeto independente; não é afiliado ao eCut e não copia seu código.\n"
            "Esta versão ainda não tem nesting automático, contornos/offset, limpeza de polilinhas,\n"
            "ordenação de percurso nem integração direta com o CorelDRAW.\n\n"
            "Sempre mantenha o original e simule/revise o corte antes de operar a máquina."
        ), justify="left", wraplength=690).pack(anchor="w")

        ttk.Label(root, textvariable=self.status, relief="sunken", anchor="w").pack(fill="x", pady=(12, 0))
        if ezdxf is None:
            self.status.set("Biblioteca ezdxf ausente — execute: py -m pip install ezdxf")

    def choose(self):
        path = filedialog.askopenfilename(title="Selecione um DXF", filetypes=[("DXF", "*.dxf")])
        if path:
            self.file_var.set(path)
            self.status.set("Arquivo selecionado.")

    def selected_file(self):
        path = self.file_var.get().strip()
        if not path or not Path(path).is_file():
            messagebox.showwarning("Arquivo necessário", "Selecione um arquivo DXF válido.")
            return None
        return path

    def clean(self):
        if ezdxf is None:
            messagebox.showerror("Dependência ausente", "Execute no Prompt: py -m pip install ezdxf")
            return
        path = self.selected_file()
        if not path:
            return
        try:
            out, count, removed = clean_lines(path, int(self.precision.get()))
            self.status.set(f"Limpeza concluída: {removed} duplicata(s) removida(s).")
            messagebox.showinfo("Concluído", f"Linhas LINE encontradas: {count}\nDuplicatas removidas: {removed}\n\nArquivo:\n{out}\n\nConfira antes de cortar.")
        except Exception as exc:
            messagebox.showerror("Erro", str(exc))

    def report(self):
        if ezdxf is None:
            messagebox.showerror("Dependência ausente", "Execute no Prompt: py -m pip install ezdxf")
            return
        path = self.selected_file()
        if not path:
            return
        try:
            counts, w, h, d = get_report(path)
            lines = [f"Arquivo: {Path(path).name}", "", "Entidades por tipo:"]
            lines.extend(f"  {name}: {count}" for name, count in sorted(counts.items()))
            lines += ["", f"Largura aproximada: {w:.4f} unidades DXF", f"Altura aproximada: {h:.4f} unidades DXF", f"Profundidade Z: {d:.4f} unidades DXF", "", "Nota: as unidades dependem da configuração/exportação do desenho."]
            self.report_box.configure(state="normal")
            self.report_box.delete("1.0", "end")
            self.report_box.insert("1.0", "\n".join(lines))
            self.report_box.configure(state="disabled")
            self.status.set("Relatório gerado.")
        except Exception as exc:
            messagebox.showerror("Erro", str(exc))

    def transform(self):
        if ezdxf is None:
            messagebox.showerror("Dependência ausente", "Execute no Prompt: py -m pip install ezdxf")
            return
        path = self.selected_file()
        if not path:
            return
        try:
            sx, sy = float(self.sx.get()), float(self.sy.get())
            copies, gx, gy = int(self.copies.get()), float(self.gapx.get()), float(self.gapy.get())
            if sx <= 0 or sy <= 0 or copies < 1 or copies > 100:
                raise ValueError("Escalas devem ser positivas; cópias devem ficar entre 1 e 100.")
            out, count, copies = transform_dxf(path, sx, sy, copies, gx, gy)
            self.status.set("Novo DXF criado.")
            messagebox.showinfo("Concluído", f"Entidades originais processadas: {count}\nCópias totais solicitadas: {copies}\n\nArquivo:\n{out}\n\nConfira escala, unidades e posicionamento antes de cortar.")
        except Exception as exc:
            messagebox.showerror("Erro", str(exc))


if __name__ == "__main__":
    if ezdxf is None:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Instale ezdxf", "Execute no Prompt de Comando:\npy -m pip install ezdxf")
    else:
        App().mainloop()
