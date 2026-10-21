"""Laser Tools Free v3: interface Tkinter para DXF do CorelDRAW / RDWorks."""
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import sys

try:
    import laser_core as core
except ImportError as exc:
    root = tk.Tk(); root.withdraw()
    messagebox.showerror('Dependências',
        f'Não foi possível iniciar: {exc}\n\nExecute INSTALAR.bat primeiro.')
    raise SystemExit(1)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Laser Tools Free v3 | Preparação de DXF')
        self.geometry('960x740')
        self.minsize(820,640)
        self.file = tk.StringVar()
        self.status = tk.StringVar(value='Selecione um DXF exportado do CorelDRAW.')
        self.precision = tk.StringVar(value='4')
        self.partial=tk.BooleanVar(value=True)
        self.unit=tk.StringVar(value='mm')
        self.material=tk.StringVar(value='0')
        self.cutting=tk.StringVar(value='0')
        self.setup=tk.StringVar(value='0')
        self.sx=tk.StringVar(value='100');self.sy=tk.StringVar(value='100')
        self.copies=tk.StringVar(value='1');self.gapx=tk.StringVar(value='5');self.gapy=tk.StringVar(value='0')
        self.sheetw=tk.StringVar(value='600');self.sheeth=tk.StringVar(value='400')
        self.spacing=tk.StringVar(value='3');self.margin=tk.StringVar(value='5')
        self.ncopies=tk.StringVar(value='1');self.rotate=tk.BooleanVar(value=True)
        self.offset=tk.StringVar(value='2')
        self._build()

    def _build(self):
        shell=ttk.Frame(self,padding=16);shell.pack(fill='both',expand=True)
        ttk.Label(shell,text='Laser Tools Free',font=('Segoe UI',21,'bold')).pack(anchor='w')
        ttk.Label(shell,text='Ferramentas independentes para DXF — CorelDRAW 2024 → DXF → revisão no RDWorks',
                  foreground='#555555').pack(anchor='w',pady=(0,12))
        row=ttk.Frame(shell);row.pack(fill='x',pady=(0,12))
        ttk.Label(row,text='Arquivo DXF:').pack(side='left')
        ttk.Entry(row,textvariable=self.file).pack(side='left',padx=8,fill='x',expand=True)
        ttk.Button(row,text='Procurar...',command=self._choose).pack(side='left')
        tabs=ttk.Notebook(shell);tabs.pack(fill='both',expand=True)
        self._clean_tab(tabs); self._report_tab(tabs);self._scale_tab(tabs)
        self._nest_tab(tabs);self._offset_tab(tabs);self._route_tab(tabs)
        self._about_tab(tabs)
        ttk.Label(shell,textvariable=self.status,relief='sunken',anchor='w',wraplength=840).pack(fill='x',pady=(12,0))

    def _tab(self,notebook,name):
        pane=ttk.Frame(notebook,padding=18);notebook.add(pane,text=name)
        return pane

    @staticmethod
    def _field(frame,title,var,row):
        ttk.Label(frame,text=title).grid(row=row,column=0,sticky='w',padx=(0,20),pady=6)
        ttk.Entry(frame,textvariable=var,width=18).grid(row=row,column=1,sticky='w',pady=6)

    @staticmethod
    def _note(parent,text):
        ttk.Label(parent,text=text,wraplength=800,justify='left',foreground='#555555').pack(anchor='w',pady=(8,12))

    def _clean_tab(self,tabs):
        p=self._tab(tabs,'Limpeza')
        ttk.Label(p,text='Limpeza de linhas e polilinhas duplicadas',font=('Segoe UI',13,'bold')).pack(anchor='w')
        self._note(p,'Reconhece LINE e polilinhas completas idênticas. Respeita cores/camadas. '
                   'Sobreposição parcial: remove ou recorta somente trechos LINE já cobertos por LINE ou segmentos retos de polilinhas.')
        row=ttk.Frame(p);row.pack(anchor='w',pady=8)
        ttk.Label(row,text='Casas decimais:').pack(side='left')
        ttk.Combobox(row,textvariable=self.precision,values=('2','3','4','5','6','7'),
                     state='readonly',width=6).pack(side='left',padx=8)
        ttk.Checkbutton(p,text='Corrigir também sobreposições parciais de LINE',variable=self.partial).pack(anchor='w',pady=8)
        ttk.Button(p,text='Limpar e salvar outra cópia',command=lambda:self._run(self._clean)).pack(anchor='w',pady=8)
        self._note(p,'Polilinhas curvas, interseções e sobreposição entre duas polilinhas diferentes ainda não são automaticamente recortadas.')

    def _report_tab(self,tabs):
        p=self._tab(tabs,'Medições e custo')
        ttk.Label(p,text='Relatório, área, perímetro e custo geométrico',font=('Segoe UI',13,'bold')).pack(anchor='w')
        r=ttk.Frame(p);r.pack(anchor='w',pady=8)
        ttk.Label(r,text='Unidade REAL do DXF:').pack(side='left')
        ttk.Combobox(r,textvariable=self.unit,values=('mm','cm','m'),state='readonly',width=6).pack(side='left',padx=8)
        form=ttk.Frame(p);form.pack(anchor='w')
        self._field(form,'Material (R$/m²)',self.material,0)
        self._field(form,'Corte (R$/m)',self.cutting,1)
        self._field(form,'Custo fixo (R$)',self.setup,2)
        ttk.Button(p,text='Calcular sem alterar o DXF',command=lambda:self._run(self._report)).pack(anchor='w',pady=8)
        self.result=tk.Text(p,height=13,wrap='word');self.result.pack(fill='both',expand=True)
        self.result.insert('1.0','Os resultados aparecerão aqui.\n');self.result.config(state='disabled')
        self._note(p,'Áreas fechadas somadas sem descontar ilhas/furos, sobreposições ou sobras da chapa. '
                   'Não é previsão real de velocidade de corte.')

    def _scale_tab(self,tabs):
        p=self._tab(tabs,'Escala e cópias')
        ttk.Label(p,text='Redimensionar e multiplicar o desenho',font=('Segoe UI',13,'bold')).pack(anchor='w')
        form=ttk.Frame(p);form.pack(anchor='w',pady=12)
        for n,(t,v) in enumerate([('Escala X (%)',self.sx),('Escala Y (%)',self.sy),
              ('Total de cópias',self.copies),('Espaçamento X',self.gapx),('Deslocamento Y por cópia',self.gapy)]):
            self._field(form,t,v,n)
        ttk.Button(p,text='Aplicar em nova cópia',command=lambda:self._run(self._scale)).pack(anchor='w',pady=8)
        self._note(p,'Escala em torno de (0,0). Algumas entidades com arcos não aceitam escala não uniforme; '
                   'nesses casos o processo é interrompido, sem gerar DXF incompleto.')

    def _nest_tab(self,tabs):
        p=self._tab(tabs,'Nesting retangular')
        ttk.Label(p,text='Encaixe automático por retângulo envolvente',font=('Segoe UI',13,'bold')).pack(anchor='w')
        self._note(p,'Mecanismo inicial de aproveitamento de chapa. Aceita SOMENTE contornos fechados independentes '
                   '(LWPOLYLINE, POLYLINE 2D ou CIRCLE). Não é nesting de formas reais e não agrupa múltiplas curvas de uma peça.')
        form=ttk.Frame(p);form.pack(anchor='w')
        for n,(t,v) in enumerate([('Largura da chapa',self.sheetw),('Altura da chapa',self.sheeth),
            ('Distância entre peças',self.spacing),('Margem da chapa',self.margin),
            ('Cópias por contorno',self.ncopies)]):self._field(form,t,v,n)
        ttk.Checkbutton(p,text='Permitir giro de 90°',variable=self.rotate).pack(anchor='w',pady=7)
        ttk.Button(p,text='Encaixar e salvar outra cópia',command=lambda:self._run(self._nest)).pack(anchor='w',pady=10)
        self._note(p,'Se alguma peça não couber na chapa, a operação falha por completo e não cria arquivo parcial.')

    def _offset_tab(self,tabs):
        p=self._tab(tabs,'Contornos / Offset')
        ttk.Label(p,text='Gerar contornos deslocados',font=('Segoe UI',13,'bold')).pack(anchor='w')
        self._note(p,'Suporta círculos e polilinhas LWPOLYLINE FECHADAS com segmentos retos. '
                   'O original permanece e o novo contorno é criado na camada LASER_OFFSET (vermelha).')
        form=ttk.Frame(p);form.pack(anchor='w');self._field(form,'Distância (+ fora / − dentro)',self.offset,0)
        ttk.Button(p,text='Gerar offset em cópia',command=lambda:self._run(self._offset)).pack(anchor='w',pady=12)
        self._note(p,'Revisar a camada LASER_OFFSET no RDWorks. Não envie original + offset como corte duplo por engano.')

    def _route_tab(self,tabs):
        p=self._tab(tabs,'Percurso de corte')
        ttk.Label(p,text='Ordenação simples de linhas por proximidade',font=('Segoe UI',13,'bold')).pack(anchor='w')
        self._note(p,'Reorganiza linhas LINE com heurística do vizinho mais próximo, '
                   'permitindo inverter o sentido da linha. Mantém grupos por camada. '
                   'Não altera DXFs com outros tipos de entidades.')
        ttk.Button(p,text='Reordenar LINE e salvar outra cópia',command=lambda:self._run(self._route)).pack(anchor='w',pady=8)
        self._note(p,'A ordem física de corte depende do RDWorks. Confirme sempre a simulação no software da máquina.')

    def _about_tab(self,tabs):
        p=self._tab(tabs,'Sobre')
        ttk.Label(p,text='Laser Tools Free v3',font=('Segoe UI',15,'bold')).pack(anchor='w',pady=(0,12))
        self._note(p,'Software independente desenvolvido em Python + ezdxf + Shapely. '
                   'Não contém código do eCut, não modifica ou contorna suas licenças e não é afiliado a ele.\n\n'
                   'Não utiliza VBA nem requer plugin dentro do CorelDRAW 2024. '\
                   'Fluxo: CorelDRAW → exportar DXF → Laser Tools Free → importar no RDWorks → simular.\n\n'
                   'Sempre confira unidades, camadas, direção e escala antes de operar o laser.')

    def _choose(self):
        path=filedialog.askopenfilename(title='Abrir DXF',filetypes=[('DXF','*.dxf')])
        if path:self.file.set(path)

    def _source(self):
        p=Path(self.file.get().strip())
        if not p.is_file() or p.suffix.lower()!='.dxf':
            raise ValueError('Selecione um arquivo DXF válido primeiro.')
        return p

    @staticmethod
    def _num(var):return float(var.get().strip().replace(',','.'))

    def _run(self,operation):
        try:
            path=self._source()
            msg=operation(path)
            self.status.set(msg.split('\n')[0][:210])
            messagebox.showinfo('Laser Tools Free',msg)
        except Exception as exc:
            self.status.set('Não foi criado arquivo: '+str(exc)[:180])
            messagebox.showerror('Operação não realizada',str(exc))

    def _clean(self,p):
        r=core.clean_duplicates(p,int(self.precision.get()),self.partial.get())
        return (f'DXF salvo: {r.output}\nLINE removidas: {r.lines_removed}\n'
                f'Polilinhas removidas: {r.polylines_removed}\nLINE divididas: {r.lines_split}\n'
                f'Fragmentos extras: {r.line_fragments_created}\n{r.notes}')

    def _report(self,p):
        r=core.report(p,self.unit.get(),self._num(self.material),self._num(self.cutting),self._num(self.setup))
        lines=[f'Arquivo: {p.name}',f'Unidade selecionada: {r["unit"]} | $INSUNITS DXF: {r["insunits"]}',
               f'Largura x altura: {r["width"]:.3f} x {r["height"]:.3f} {r["unit"]}',
               f'Comprimento total medido: {r["length_m"]:.4f} m',
               f'Área nominal de contornos fechados: {r["area_m2"]:.6f} m²',
               '',f'Material: R$ {r["material_cost"]:.2f}',f'Corte: R$ {r["cut_cost"]:.2f}',
               f'Fixo: R$ {r["setup"]:.2f}',f'TOTAL ESTIMADO: R$ {r["total"]:.2f}',
               '','Entidades:']
        lines+=['  '+k+': '+str(v) for k,v in sorted(r['types'].items())]
        if r['skipped']:
            lines+=['','Não medidos:']+['  '+k+': '+str(v) for k,v in r['skipped'].items()]
        lines+=['',r['warnings']]
        self.result.config(state='normal');self.result.delete('1.0','end')
        self.result.insert('1.0','\n'.join(lines));self.result.config(state='disabled')
        return 'Relatório calculado (DXF original não modificado).'

    def _scale(self,p):
        out=core.scale_and_copy(p,self._num(self.sx),self._num(self.sy),int(self.copies.get()),
                                self._num(self.gapx),self._num(self.gapy))
        return f'Arquivo de escala e cópias criado: {out}'

    def _nest(self,p):
        out,qty,shelves=core.rectangular_nesting(p,self._num(self.sheetw),self._num(self.sheeth),
                    self._num(self.spacing),self._num(self.margin),int(self.ncopies.get()),self.rotate.get())
        return f'Nesting salvo: {out}\nContornos posicionados: {qty}\nFaixas de encaixe: {shelves}'

    def _offset(self,p):
        out,n,skipped=core.create_offsets(p,self._num(self.offset))
        return f'Contornos na camada LASER_OFFSET: {out}\nContornos criados: {n}\nIgnorados: {skipped}'

    def _route(self,p):
        out,before,after=core.optimize_lines(p)
        return f'Percursos reordenados: {out}\nMovimento em vazio antes: {before:.2f} unidades\nApós: {after:.2f} unidades'


if __name__=='__main__':
    app = App()
    if len(sys.argv) > 1:
        initial = Path(sys.argv[1]).expanduser()
        if initial.is_file() and initial.suffix.lower() == '.dxf':
            app.file.set(str(initial.resolve()))
            app.status.set('DXF exportado pelo CorelDRAW carregado; revise unidades e entidades.')
    app.mainloop()
