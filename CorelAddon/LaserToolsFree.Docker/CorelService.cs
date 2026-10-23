using System;
using System.IO;
using System.Linq;

namespace LaserToolsFree.Docker
{
    /// <summary>
    /// Usa dynamic para consumir o objeto Application entregue pelo host. Não requer VBA
    /// ou a distribuição de Corel.Interop.VGCore.dll. Chamadas nativas: alterar documento
    /// em memória SOMENTE após criar e confirmar cópia CDR.
    /// </summary>
    internal sealed class CorelService
    {
        private readonly dynamic _app;
        private const int Millimeter = 3; // cdrMillimeter (CorelDRAW 2022 / 2024)
        public CorelService(object corelApplication)
        {
            if (corelApplication == null) throw new ArgumentNullException("corelApplication");
            _app = corelApplication;
        }

        private dynamic Document()
        {
            try
            {
                dynamic doc = _app.ActiveDocument;
                if (doc == null) throw new InvalidOperationException("Abra um documento CDR primeiro.");
                return doc;
            }
            catch (Microsoft.CSharp.RuntimeBinder.RuntimeBinderException ex)
            {
                throw new InvalidOperationException("A API do CorelDRAW não forneceu um documento ativo.", ex);
            }
        }

        private dynamic Selection(dynamic doc)
        {
            dynamic selection = doc.SelectionRange;
            if (selection == null || (int)selection.Count < 1)
                throw new InvalidOperationException("Selecione pelo menos um objeto no CorelDRAW.");
            return selection;
        }

        private void RequireMillimeter(dynamic doc)
        {
            if ((int)doc.Unit != Millimeter)
                throw new InvalidOperationException("Esta ferramenta DXF exige documento em mm. Unidade interna recebida do CorelDRAW: " + (int)doc.Unit + " (3 = mm, 4 = cm). Nenhum objeto foi alterado.");
        }

        public SelectionSnapshot Inspect()
        {
            dynamic doc = Document();
            dynamic selection = Selection(doc);
            return new SelectionSnapshot
            {
                Name = Convert.ToString(doc.Name), Count = (int)selection.Count,
                Width = Convert.ToDouble(selection.SizeWidth),
                Height = Convert.ToDouble(selection.SizeHeight), Unit = (int)doc.Unit
            };
        }

        private static string SafeFileName(string value)
        {
            string clean = new string((value ?? "Desenho").Where(c => char.IsLetterOrDigit(c) || c == '-' || c == '_').Take(65).ToArray());
            return string.IsNullOrWhiteSpace(clean) ? "Desenho" : clean;
        }

        private string Backup(dynamic doc)
        {
            string backups = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments), "LaserToolsFree", "Backups");
            Directory.CreateDirectory(backups);
            string originalName = Convert.ToString(doc.Name);
            string stem = SafeFileName(Path.GetFileNameWithoutExtension(originalName));
            string path = Path.Combine(backups, stem + "_antes_" + DateTime.Now.ToString("yyyyMMdd_HHmmss_fffffff") + "_" + Guid.NewGuid().ToString("N").Substring(0, 8) + ".cdr");
            // Não salvar o arquivo aberto. Nunca sobrescrever o backup anterior.
            doc.SaveAsCopy(path);
            if (!File.Exists(path) || new FileInfo(path).Length == 0)
                throw new IOException("O backup do CorelDRAW não foi confirmado. Operação cancelada.");
            // Defesa adicional caso CorelDRAW se comporte inesperadamente com SaveAsCopy.
            if (!string.Equals(Convert.ToString(doc.Name), originalName, StringComparison.OrdinalIgnoreCase))
                throw new IOException("O CorelDRAW mudou o nome do arquivo ativo durante o backup; operação cancelada.");
            return path;
        }

        private string RunEdit(string label, Action<dynamic, dynamic> action, bool requireMillimeters = true)
        {
            dynamic doc = Document();
            dynamic selection = Selection(doc);
            if (requireMillimeters) RequireMillimeter(doc);
            string backup = Backup(doc);
            bool groupStarted = false;
            try
            {
                doc.BeginCommandGroup("Laser Tools Free - " + label);
                groupStarted = true;
                action(doc, selection);
                return backup;
            }
            catch (Exception ex)
            {
                throw new InvalidOperationException("Falha durante '" + label + "'. O desenho pode ter sido alterado parcialmente. " +
                    "Use Ctrl+Z no CorelDRAW. Backup salvo em " + backup + ". Detalhes: " + ex.Message, ex);
            }
            finally
            {
                if (groupStarted)
                {
                    try { doc.EndCommandGroup(); }
                    catch (Exception) { /* Não mascarar falha principal. */ }
                }
            }
        }

        /// <summary>
        /// Exportação *não destrutiva* da seleção para DXF em arquivo novo. O filtro
        /// DXF pode apresentar configuração nativa do CorelDRAW (verificar unidades).
        /// </summary>
        public string ExportSelectionDxf()
        {
            dynamic doc = Document();
            Selection(doc);
            RequireMillimeter(doc);
            string folder = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments),
                "LaserToolsFree", "DXF_Exportados");
            Directory.CreateDirectory(folder);
            string stem = SafeFileName(Path.GetFileNameWithoutExtension(Convert.ToString(doc.Name)));
            string filename = Path.Combine(folder, stem + "_selecao_" +
                DateTime.Now.ToString("yyyyMMdd_HHmmss_fffffff") + "_" +
                Guid.NewGuid().ToString("N").Substring(0, 8) + ".dxf");
            // CorelDRAW: cdrDXF=1296; cdrSelection=2. O ExportFilter exige Finish().
            dynamic exportFilter = doc.ExportEx(filename, 1296, 2);
            if (exportFilter == null) throw new IOException("CorelDRAW não retornou o filtro de exportação DXF.");
            // A API do filtro DXF usa DxfUnits=3 para milímetros. No host COM,
            // esta propriedade pode não estar exposta; exigir verificação na etapa Python.
            try { exportFilter.Units = 3; } catch (Microsoft.CSharp.RuntimeBinder.RuntimeBinderException) { }
            exportFilter.Finish();
            if (!File.Exists(filename) || new FileInfo(filename).Length == 0)
                throw new IOException("DXF não foi confirmado. Confira se o CorelDRAW exibiu configuração do filtro ou erro.");
            return filename;
        }

        /// <summary>Importa resultado como camada NOVA, preservando integralmente o desenho antigo.</summary>
        public string ImportResultAsNewLayer(string dxfPath, string operation)
        {
            if (string.IsNullOrWhiteSpace(dxfPath) || !File.Exists(dxfPath))
                throw new FileNotFoundException("DXF processado não encontrado.", dxfPath);
            dynamic doc = Document();
            RequireMillimeter(doc);
            string backup = Backup(doc);
            string layerName="LTF_" + SafeFileName(operation) + "_" + DateTime.Now.ToString("HHmmssfff");
            bool commandStarted=false;
            try
            {
                doc.BeginCommandGroup("Laser Tools Free - Importar DXF");
                commandStarted=true;
                dynamic layer=doc.ActivePage.CreateLayer(layerName);
                dynamic filter=layer.ImportEx(dxfPath, 1296);
                if (filter==null) throw new InvalidOperationException("CorelDRAW não retornou um filtro de importação.");
                filter.Finish();
                if ((int)layer.Shapes.Count<1)
                    throw new InvalidOperationException("O CorelDRAW não registrou formas na nova camada. Confira o DXF importado.");
                return backup;
            }
            catch (Exception ex)
            {
                throw new InvalidOperationException("Falha ao importar; a camada pode estar vazia ou parcialmente criada. " +
                    "Não salve o CDR. Desfaça com Ctrl+Z. Backup em " + backup + ". " + ex.Message,ex);
            }
            finally
            {
                if (commandStarted) try { doc.EndCommandGroup(); } catch { }
            }
        }

        // "gapMm" e sempre expresso em milimetros no painel, independentemente
        // da unidade do desenho. A API Duplicate utiliza as unidades internas
        // do documento; converter ANTES de deslocar evita escalas erradas.
        public string Grid(int rows, int columns, double gapMm)
        {
            SelectionSnapshot s = Inspect();
            Calculations.CheckGrid(rows, columns, gapMm, s.Width, s.Height);
            double gapInDocumentUnits = Calculations.MmToDocumentUnits(gapMm, s.Unit);
            return RunEdit("Criar grade", (doc, selection) =>
            {
                // Conferir se a unidade nao mudou entre inspecao e modificacao.
                if ((int)doc.Unit != s.Unit)
                    throw new InvalidOperationException("A unidade do documento mudou durante a operacao. Nada sera duplicado.");
                for (int r = 0; r < rows; r++)
                {
                    for (int c = 0; c < columns; c++)
                    {
                        if (r == 0 && c == 0) continue;
                        selection.Duplicate(c * (s.Width + gapInDocumentUnits),
                            -r * (s.Height + gapInDocumentUnits));
                    }
                }
            }, requireMillimeters: false);
        }

        public string Resize(double width, double height)
        {
            if (width < 0.01 || height < 0.01 || width > 100000 || height > 100000)
                throw new ArgumentException("Largura e altura devem estar entre 0,01 mm e 100000 mm.");
            SelectionSnapshot s = Inspect();
            if (s.Width <= 0 || s.Height <= 0)
                throw new InvalidOperationException("A seleção não tem dimensões válidas.");
            return RunEdit("Redimensionar", (doc, selection) => selection.SetSize(width, height));
        }

        public string Rotate90(int degrees)
        {
            if (degrees != 90 && degrees != -90)
                throw new ArgumentException("Rotação permitida: 90 ou -90 graus.");
            return RunEdit("Girar 90 graus", (doc, selection) =>
            {
                // Rotação em torno do centro geométrico da seleção.
                selection.RotationCenterX = Convert.ToDouble(selection.CenterX);
                selection.RotationCenterY = Convert.ToDouble(selection.CenterY);
                selection.Rotate(degrees);
            });
        }
    }

    internal sealed class SelectionSnapshot
    {
        public string Name { get; set; }
        public int Count { get; set; }
        public double Width { get; set; }
        public double Height { get; set; }
        public int Unit { get; set; }
    }
}
