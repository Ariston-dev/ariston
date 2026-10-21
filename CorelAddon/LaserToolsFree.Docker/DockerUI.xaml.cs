using System;
using System.Diagnostics;
using System.IO;
using System.Collections.Generic;
using System.Globalization;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;

namespace LaserToolsFree.Docker
{
    /// <summary>Instanciado diretamente pelo host WPF do CorelDRAW.</summary>
    public partial class DockerUI : UserControl
    {
        private readonly CorelService _corel;
        private bool _processing;

        // CorelDRAW fornece Application ao construtor do controle hospedado.
        // object evita distribuir DLLs proprietárias do Corel ou exigir VBA.
        public DockerUI(object application)
        {
            InitializeComponent();
            _corel = new CorelService(application);
            TxtStatus.Text = "Painel carregado. Clique em Atualizar seleção.";
        }

        private void Error(Exception ex)
        {
            TxtStatus.Text = "Falha: " + ex.Message;
            MessageBox.Show(ex.Message, "Laser Tools Free", MessageBoxButton.OK, MessageBoxImage.Warning);
        }

        private void Run(Action work)
        {
            try { work(); }
            catch (Exception ex) { Error(ex); }
        }

        private bool Confirm(string action)
        {
            return MessageBox.Show(
                action + "\n\nUma cópia .CDR será criada automaticamente em Documentos\\LaserToolsFree\\Backups " +
                "ANTES da alteração. O original será mantido, e o documento aberto não será salvo automaticamente.\n\n" +
                "Use somente arquivos de teste nesta versão. Continuar?",
                "Confirmar operação", MessageBoxButton.YesNo, MessageBoxImage.Question) == MessageBoxResult.Yes;
        }

        private void Refresh()
        {
            SelectionSnapshot s = _corel.Inspect();
            string unit = s.Unit == 3 ? "mm" : "outra unidade (ajuste o documento para mm)";
            TxtSelection.Text = "Documento: " + s.Name + "\nObjetos: " + s.Count +
                "\nLargura: " + Calculations.Mm(s.Width) + " " + unit +
                " | Altura: " + Calculations.Mm(s.Height) + " " + unit +
                "\nÁrea da caixa envolvente: " + Calculations.Mm(s.Width * s.Height) +
                " unidades² (NÃO é a área geométrica das peças)";
            if (s.Unit == 3)
            {
                TxtWidth.Text = Calculations.Mm(s.Width);
                TxtHeight.Text = Calculations.Mm(s.Height);
            }
            TxtStatus.Text = "Seleção atualizada. Nenhum objeto foi modificado.";
        }

        private void BtnRefresh_Click(object sender, RoutedEventArgs e) { Run(Refresh); }

        private void BtnGrid_Click(object sender, RoutedEventArgs e)
        {
            Run(() =>
            {
                int rows = Calculations.PositiveCount(TxtRows.Text, "Linhas");
                int cols = Calculations.PositiveCount(TxtColumns.Text, "Colunas");
                double gap = Calculations.Number(TxtGap.Text, "Espaçamento", 0, 10000);
                SelectionSnapshot s = _corel.Inspect();
                Calculations.CheckGrid(rows, cols, gap, s.Width, s.Height);
                if (!Confirm("Criar " + (rows * cols - 1) + " cópia(s) da seleção em grade")) return;
                string path = _corel.Grid(rows, cols, gap);
                Refresh();
                TxtStatus.Text = "Cópias criadas. Backup: " + path;
            });
        }

        private void BtnResize_Click(object sender, RoutedEventArgs e)
        {
            Run(() =>
            {
                double w = Calculations.Number(TxtWidth.Text, "Largura", 0.01, 100000);
                SelectionSnapshot s = _corel.Inspect();
                double h = ChkRatio.IsChecked == true
                    ? Calculations.ProportionalHeight(s.Width, s.Height, w)
                    : Calculations.Number(TxtHeight.Text, "Altura", 0.01, 100000);
                if (h < 0.01 || h > 100000) throw new ArgumentException("Altura calculada fora dos limites.");
                if (!Confirm("Ajustar a seleção para " + Calculations.Mm(w) + " × " + Calculations.Mm(h) + " mm")) return;
                string path = _corel.Resize(w, h);
                Refresh();
                TxtStatus.Text = "Dimensões aplicadas. Backup: " + path;
            });
        }

        private void BtnRotateLeft_Click(object sender, RoutedEventArgs e) { Rotate(90); }
        private void BtnRotateRight_Click(object sender, RoutedEventArgs e) { Rotate(-90); }

        private void Rotate(int degrees)
        {
            Run(() =>
            {
                if (!Confirm("Girar a seleção " + degrees + " graus")) return;
                string path = _corel.Rotate90(degrees);
                Refresh();
                TxtStatus.Text = "Rotação feita. Backup: " + path;
            });
        }

        private static void StartEngine(string dxfFile)
        {
            string editor = Path.Combine(EngineRunner.EngineDir, "LaserToolsFreeEditor.exe");
            if (!File.Exists(editor))
                throw new FileNotFoundException("Editor DXF portátil não encontrado: " + editor);
            Process.Start(new ProcessStartInfo
            {
                FileName = editor,
                Arguments = string.IsNullOrEmpty(dxfFile) ? "" : "\"" + dxfFile.Replace("\"", "") + "\"",
                WorkingDirectory = EngineRunner.EngineDir,
                UseShellExecute = true
            });
        }

        private void BtnExportSelection_Click(object sender, RoutedEventArgs e)
        {
            Run(() =>
            {
                if (MessageBox.Show("Exportar APENAS os objetos selecionados para um NOVO DXF? " +
                    "O arquivo CDR permanecerá inalterado. Verifique as opções DXF exibidas pelo CorelDRAW.",
                    "Exportação DXF experimental", MessageBoxButton.YesNo, MessageBoxImage.Question)
                    != MessageBoxResult.Yes) return;
                string path = _corel.ExportSelectionDxf();
                TxtStatus.Text = "DXF de seleção: " + path;
                MessageBox.Show("DXF criado: " + path + "\n\nConfira curvas, unidades e dimensões antes de usar no RDWorks.",
                    "DXF exportado", MessageBoxButton.OK, MessageBoxImage.Information);
            });
        }

        private void BtnExportAndOpen_Click(object sender, RoutedEventArgs e)
        {
            Run(() =>
            {
                // Validar dependência ANTES de gerar um arquivo para usar no editor.
                if (!File.Exists(Path.Combine(EngineRunner.EngineDir, "LaserToolsFreeEditor.exe")))
                    throw new FileNotFoundException("Editor DXF portátil não encontrado.");
                if (MessageBox.Show("Criar um DXF da seleção e abrir o editor DXF? O CDR NÃO será modificado.",
                    "Exportação experimental", MessageBoxButton.YesNo, MessageBoxImage.Question)
                    != MessageBoxResult.Yes) return;
                string path = _corel.ExportSelectionDxf();
                StartEngine(path);
                TxtStatus.Text = "DXF exportado e aberto no editor DXF: " + path;
            });
        }

        private void BtnOpenDXF_Click(object sender, RoutedEventArgs e)
        {
            Run(() =>
            {
                StartEngine(null);
                TxtStatus.Text = "Editor DXF aberto em janela separada (não no CDR).";
            });
        }

        private static string Invariant(double d) { return d.ToString("R", CultureInfo.InvariantCulture); }

        private async Task ProcessSelection(string command, IDictionary<string,string> options, bool import)
        {
            if (_processing)
            {
                MessageBox.Show("Já existe uma operação em andamento.", "Laser Tools Free");
                return;
            }
            _processing = true;
            try
            {
                // Nunca chama API COM do CorelDRAW em uma thread em segundo plano.
                // Primeiro exporta na thread UI, depois executa apenas Python fora dela.
                if (!File.Exists(Path.Combine(EngineRunner.EngineDir, "LaserDXFEngine.exe")))
                    throw new InvalidOperationException("Motor DXF portátil ausente. Reinstale o pacote compilado.");
                string question=import
                    ? "Executar " + command + " e IMPORTAR resultado na camada nova? A seleção original permanecerá intacta."
                    : "Processar a seleção em DXF sem alterar o desenho?";
                if (MessageBox.Show(question, "Laser Tools Free v5", MessageBoxButton.YesNo, MessageBoxImage.Question)
                    != MessageBoxResult.Yes) return;
                SelectionSnapshot origin = _corel.Inspect();
                string input=_corel.ExportSelectionDxf();
                TxtStatus.Text="Processando " + command + "...";
                var result=await Task.Run(() => EngineRunner.Execute(command,input,options));
                // Não importa automaticamente em outro documento se usuário trocar de janela.
                SelectionSnapshot current = _corel.Inspect();
                if (current.Name != origin.Name || current.Unit != origin.Unit || current.Count != origin.Count)
                    throw new InvalidOperationException("Seleção/documento mudou durante o processamento. O DXF foi salvo, mas não será importado automaticamente.");
                if (import && !string.IsNullOrWhiteSpace(result.Output))
                {
                    if (!Confirm("Importar o DXF processado sem remover nem substituir o original")) return;
                    string backup=_corel.ImportResultAsNewLayer(result.Output,command);
                    TxtStatus.Text="Nova camada criada. " + result.Summary;
                    MessageBox.Show(result.Summary+"\n\nDXF: "+result.Output+
                        "\n\nBackup CDR: "+backup+
                        "\n\nCONFIRA escala, posição, unidades e cores!", "Laser Tools Free",
                        MessageBoxButton.OK, MessageBoxImage.Information);
                }
                else
                {
                    TxtStatus.Text=result.Summary;
                    MessageBox.Show(result.Summary+(string.IsNullOrWhiteSpace(result.Output)?"":"\n\nDXF: "+result.Output),
                        "Laser Tools Free", MessageBoxButton.OK, MessageBoxImage.Information);
                }
            }
            catch (Exception ex) { Error(ex); }
            finally { _processing = false; }
        }

        private async void BtnClean_Click(object sender, RoutedEventArgs e)
        {
            await ProcessSelection("clean",new Dictionary<string,string>(),true);
        }
        private async void BtnOffset_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                double d=Calculations.Number(TxtOffset.Text,"Distância de offset",-10000,10000);
                if(Math.Abs(d)<0.0000001) throw new ArgumentException("Offset deve ser diferente de zero.");
                await ProcessSelection("offset",new Dictionary<string,string>{{"distance",Invariant(d)}},true);
            }
            catch(Exception ex) { Error(ex); }
        }
        private async void BtnRectangle_Click(object sender, RoutedEventArgs e)
        {
            await DoNesting("rectangle");
        }
        private async void BtnShape_Click(object sender, RoutedEventArgs e)
        {
            await DoNesting("shape");
        }
        private async Task DoNesting(string op)
        {
            try
            {
                double w=Calculations.Number(TxtSheetWidth.Text,"Largura da chapa",1,100000);
                double h=Calculations.Number(TxtSheetHeight.Text,"Altura da chapa",1,100000);
                double spacing=Calculations.Number(TxtSpacing.Text,"Espaçamento",0,10000);
                double margin=Calculations.Number(TxtMargin.Text,"Margem",0,10000);
                int copies=Calculations.PositiveCount(TxtCopies.Text,"Cópias");
                var opts=new Dictionary<string,string>{{"width",Invariant(w)}, {"height",Invariant(h)},
                    {"spacing",Invariant(spacing)}, {"margin",Invariant(margin)},
                    {"copies",copies.ToString(CultureInfo.InvariantCulture)}};
                await ProcessSelection(op,opts,true);
            }
            catch(Exception ex) { Error(ex); }
        }
        private async void BtnCost_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                var opts=new Dictionary<string,string>
                {
                    {"material",Invariant(Calculations.Number(TxtMaterial.Text,"Material",0,100000000))},
                    {"cut",Invariant(Calculations.Number(TxtCut.Text,"Corte",0,100000000))},
                    {"setup",Invariant(Calculations.Number(TxtSetup.Text,"Fixo",0,100000000))}
                };
                await ProcessSelection("report",opts,false);
            }
            catch(Exception ex) { Error(ex); }
        }
        private async void BtnRDWorks_Click(object sender, RoutedEventArgs e)
        {
            await ProcessSelection("rdworks",new Dictionary<string,string>(),false);
        }

        private void BtnOpenBackups_Click(object sender, RoutedEventArgs e)
        {
            Run(() =>
            {
                string folder = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments),
                    "LaserToolsFree", "Backups");
                Directory.CreateDirectory(folder);
                Process.Start(new ProcessStartInfo { FileName = "explorer.exe", Arguments = "\"" + folder + "\"", UseShellExecute = true });
            });
        }
    }
}
