"""Interface de teste COM para o CorelDRAW. NÃO é painel embutido/dockable."""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from corel_bridge import connect, inspect_selection, duplicate_grid, CorelBridgeError


class CorelWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Laser Tools Free | Ponte CorelDRAW (teste)')
        self.geometry('575x410')
        self.resizable(False, False)
        self.rows=tk.StringVar(value='2')
        self.columns=tk.StringVar(value='3')
        self.gap=tk.StringVar(value='3')
        self.folder=tk.StringVar(value=str(Path.home() / 'Documents'))
        self.status=tk.StringVar(value='Abra um CDR e selecione objetos no CorelDRAW 2024.')
        frame=ttk.Frame(self,padding=18)
        frame.pack(fill='both',expand=True)
        ttk.Label(frame,text='Conexão com CorelDRAW 2024',font=('Segoe UI',14,'bold')).pack(anchor='w',pady=(0,12))
        ttk.Label(frame,text='PROTÓTIPO: controla a seleção aberta, sem DXF e sem VBA.\n'
                             'A janela ainda é separada; o painel embutido será desenvolvido em C#.',
                  justify='left').pack(anchor='w')
        ttk.Button(frame,text='Ler seleção do CorelDRAW',command=self.read).pack(anchor='w',pady=(12,10))
        options=ttk.Frame(frame)
        options.pack(fill='x')
        for i,(label,var) in enumerate([('Linhas:',self.rows),('Colunas:',self.columns),('Espaço (mm):',self.gap)]):
            ttk.Label(options,text=label).grid(row=0,column=i*2,padx=(0,4))
            ttk.Entry(options,width=6,textvariable=var).grid(row=0,column=i*2+1,padx=(0,10))
        backup=ttk.Frame(frame)
        backup.pack(fill='x',pady=(15,8))
        ttk.Label(backup,text='Pasta de backup:').pack(anchor='w')
        line=ttk.Frame(backup);line.pack(fill='x')
        ttk.Entry(line,textvariable=self.folder).pack(side='left',fill='x',expand=True)
        ttk.Button(line,text='Escolher',command=self.browse).pack(side='left',padx=(8,0))
        ttk.Button(frame,text='Gerar grade no CorelDRAW (faz backup CDR)',command=self.run).pack(anchor='w',pady=(4,10))
        ttk.Separator(frame).pack(fill='x',pady=5)
        ttk.Label(frame,textvariable=self.status,wraplength=525,justify='left').pack(anchor='w',pady=6)
        ttk.Label(frame,text='Teste apenas em documentos de exemplo. Sempre confira \n'
                             'posição, dimensões e resultado antes de salvar.',foreground='#795600').pack(anchor='w',pady=4)

    def browse(self):
        p=filedialog.askdirectory(initialdir=self.folder.get() if Path(self.folder.get()).is_dir() else None)
        if p: self.folder.set(p)

    def read(self):
        try:
            info=inspect_selection(connect())
            unit='mm' if info.unit==3 else f'código de unidade {info.unit} (mude para mm para copiar)'
            self.status.set(f'Documento: {info.name} | Objetos: {info.count} | '
                            f'Dimensões: {info.width:.3f} x {info.height:.3f} ({unit})')
        except Exception as exc:
            self.status.set(str(exc));messagebox.showerror('CorelDRAW',str(exc))

    def run(self):
        try:
            rows=int(self.rows.get()); columns=int(self.columns.get())
            gap=float(self.gap.get().replace(',','.'))
            if not messagebox.askyesno('Confirmar',
                  'Será criado um backup .CDR na pasta selecionada.\n'
                  'Em seguida serão criadas cópias no documento ABERTO.\n\n'
                  'O resultado NÃO será salvo automaticamente. Continuar?'):
                return
            path,count=duplicate_grid(connect(),rows,columns,gap,self.folder.get())
            message=f'{count} conjunto(s) duplicado(s) no CorelDRAW.\nBackup: {path}\n'
                    'Volte ao CorelDRAW, confira e use Ctrl+Z se quiser desfazer.'
            self.status.set(message)
            messagebox.showinfo('Pronto para conferir',message)
        except (CorelBridgeError,ValueError) as exc:
            self.status.set(str(exc));messagebox.showerror('Não foi possível concluir',str(exc))
        except Exception as exc:
            self.status.set(str(exc));messagebox.showerror('Erro',str(exc))


if __name__=='__main__':
    CorelWindow().mainloop()
