using System;
using System.Collections.Generic;
using System.IO;
using LaserToolsFree.Docker;

namespace LaserToolsFree.Docker
{
    // Executado no runner Windows sem CorelDRAW. Testa o proprio codigo C#
    // das operacoes de backup e grade, usando API de documento simulada.
    public static class Program
    {
        private static void Assert(bool test, string reason)
        {
            if (!test) throw new Exception("FAIL: " + reason);
        }
        private static void MustFail(Action action, string messageFragment)
        {
            try { action(); }
            catch (InvalidOperationException ex)
            {
                Assert(ex.Message.IndexOf(messageFragment, StringComparison.OrdinalIgnoreCase) >= 0,
                    "Mensagem inesperada: " + ex.Message);
                return;
            }
            throw new Exception("Deveria recusar operacao: " + messageFragment);
        }
        public static int Main()
        {
            string tmp = Path.Combine(Path.GetTempPath(), "ltf-backup-smoke-" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(tmp);
            string original = Path.Combine(tmp, "meu desenho.cdr");
            byte[] contents = new byte[] { 80, 75, 3, 4, 10, 20, 30, 40, 50 };
            File.WriteAllBytes(original, contents);
            var document = new FakeDocument
            {
                Name = Path.GetFileName(original), FileName = Path.GetFileName(original),
                FilePath = tmp + Path.DirectorySeparatorChar, Dirty = false, Unit = 3,
                SelectionRange = new FakeSelection()
            };
            try
            {
                var service = new CorelService(new FakeApplication { ActiveDocument = document });
                string backup = service.TestBackup();
                Assert(File.Exists(backup), "backup existe");
                Assert(BytesEqual(File.ReadAllBytes(backup), contents), "bytes do backup iguais aos do CDR original");
                Assert(BytesEqual(File.ReadAllBytes(original), contents), "original intocado");
                Assert(document.BeginCalls == 0, "teste de backup nao altera documento");
                File.Delete(backup);

                string gradeBackup = service.Grid(2, 3, 3.0);
                Assert(File.Exists(gradeBackup), "backup existe antes da grade");
                Assert(document.BeginCalls == 1 && document.EndCalls == 1, "grupo de undo balanceado");
                Assert(document.SelectionRange.Offsets.Count == 5, "5 copias mais original");
                Assert(OffsetAt(document, 0, 33, 0), "primeira copia na posicao certa");
                Assert(OffsetAt(document, 1, 66, 0), "segunda copia na posicao certa");
                Assert(OffsetAt(document, 2, 0, -23), "proxima linha na posicao certa");
                Assert(BytesEqual(File.ReadAllBytes(original), contents), "sem mudanca no CDR de disco");
                File.Delete(gradeBackup);
                Console.WriteLine("OK: copia do CDR salvo, backup independente, grade 2x3, deslocamentos, undo.");

                // Documento com unidade 1 (polegadas): interface trabalha em mm.
                document.Unit = 1;
                document.SelectionRange.Width = 30.0 / 25.4;
                document.SelectionRange.Height = 20.0 / 25.4;
                document.SelectionRange.Offsets.Clear();
                string inchGrade = service.Grid(2, 3, 3.0);
                Assert(File.Exists(inchGrade), "backup existe para grade em polegadas");
                Assert(OffsetAt(document, 0, 33.0/25.4, 0), "espaco 3 mm no documento em polegadas");
                Assert(OffsetAt(document, 2, 0, -23.0/25.4), "deslocamento vertical em polegadas");
                File.Delete(inchGrade);

                string inchResize = service.Resize(50, 40);
                Assert(File.Exists(inchResize), "backup redimensionamento em polegadas");
                Assert(Math.Abs(document.SelectionRange.LastWidth - 50.0/25.4) < 1e-8, "50 mm em polegadas");
                Assert(Math.Abs(document.SelectionRange.LastHeight - 40.0/25.4) < 1e-8, "40 mm em polegadas");
                File.Delete(inchResize);

                string inchRotate = service.Rotate90(90);
                Assert(File.Exists(inchRotate), "backup da rotacao em polegadas");
                Assert(document.SelectionRange.LastRotate == 90, "rotacao nao precisa exigir mm");
                File.Delete(inchRotate);

                string inchExport = service.ExportSelectionDxf();
                Assert(File.Exists(inchExport), "exportar documento em polegadas para DXF mm");
                Assert(document.LastExportFilter != null && document.LastExportFilter.Units == 3,
                    "filtro DXF fixado em milimetros");
                Assert(document.Unit == 1, "exportacao nao altera unidade CDR");

                string inchImport = service.ImportResultAsNewLayer(inchExport, "teste");
                Assert(File.Exists(inchImport), "backup antes da importacao DXF");
                Assert(document.ActivePage.LastCreatedLayer.LastFilter.Scaling == 2,
                    "importacao DXF exige modo metrico no filtro");
                Assert(document.ActivePage.LastCreatedLayer.Shapes.Count > 0,
                    "filtro devolve geometrias importadas");
                Assert(document.Unit == 1, "importacao preserva unidade do CDR");
                File.Delete(inchImport);
                File.Delete(inchExport);
                Assert(BytesEqual(File.ReadAllBytes(original), contents), "CDR original permanece intacto");
                Console.WriteLine("OK: inch->mm na grade/medidas, rotacao, DXF mm de saida, importacao metrica simulada.");

                document.Dirty = true;
                int previousCount = document.SelectionRange.Offsets.Count;
                MustFail(() => service.Grid(2, 3, 3), "Ctrl+S");
                Assert(document.SelectionRange.Offsets.Count == previousCount, "nenhuma duplicacao quando dirty");
                document.Dirty = false;
                document.FileName = "";
                MustFail(() => service.TestBackup(), "Salvar como");
                document.FileName = "arquivo.pdf";
                MustFail(() => service.TestBackup(), "formato .CDR");
                document.FileName = "desaparecido.cdr";
                MustFail(() => service.TestBackup(), "nao foi encontrado");
                Console.WriteLine("OK: recusa segura de arquivo dirty, nunca salvo, nao-CDR e inexistente.");
                return 0;
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine(ex);
                return 1;
            }
            finally
            {
                try { Directory.Delete(tmp, true); } catch { }
            }
        }
        private static bool OffsetAt(FakeDocument doc, int idx, double x, double y)
        {
            var o = doc.SelectionRange.Offsets[idx];
            return Math.Abs(o.Item1-x) < 1e-8 && Math.Abs(o.Item2-y) < 1e-8;
        }
        private static bool BytesEqual(byte[] a, byte[] b)
        {
            if (a.Length != b.Length) return false;
            for (int i=0; i<a.Length; i++) if (a[i] != b[i]) return false;
            return true;
        }
    }

    public sealed class FakeApplication { public FakeDocument ActiveDocument { get; set; } }
    public sealed class FakeDocument
    {
        public string Name { get; set; }
        public string FileName { get; set; }
        public string FilePath { get; set; }
        public bool Dirty { get; set; }
        public int Unit { get; set; }
        public FakeSelection SelectionRange { get; set; }
        public FakePage ActivePage { get; } = new FakePage();
        public FakeExportFilter LastExportFilter { get; private set; }
        public FakeExportFilter ExportEx(string filename, int format, int exportRange)
        {
            if (format != 1296 || exportRange != 2) throw new Exception("ExportEx parametros inesperados");
            LastExportFilter = new FakeExportFilter(filename);
            return LastExportFilter;
        }
        public int BeginCalls, EndCalls;
        public void BeginCommandGroup(string title) { BeginCalls++; }
        public void EndCommandGroup() { EndCalls++; }
        public void SaveAsCopy(string filename) { throw new Exception("PROIBIDO: nao usar SaveAsCopy neste teste"); }
    }
    public sealed class FakeSelection
    {
        public int Count { get { return 1; } }
        public double Width { get; set; } = 30;
        public double Height { get; set; } = 20;
        public double SizeWidth { get { return Width; } }
        public double SizeHeight { get { return Height; } }
        public double LastWidth, LastHeight;
        public int LastRotate;
        public double RotationCenterX, RotationCenterY;
        public double CenterX { get { return 0; } }
        public double CenterY { get { return 0; } }
        public void SetSize(double width, double height) { LastWidth=width; LastHeight=height; }
        public void Rotate(int degrees) { LastRotate=degrees; }
        public List<Tuple<double,double>> Offsets = new List<Tuple<double,double>>();
        public FakeSelection Duplicate(double offsetX, double offsetY)
        {
            Offsets.Add(Tuple.Create(offsetX, offsetY));
            return this;
        }
    }

    public sealed class FakeExportFilter
    {
        private readonly string _filename;
        public int Units { get; set; } = -1;
        public FakeExportFilter(string filename) { _filename=filename; }
        public void Finish()
        {
            if (Units != 3) throw new InvalidOperationException("Unidades DXF nao fixadas como mm");
            File.WriteAllText(_filename, "0\nSECTION\n2\nENTITIES\n0\nENDSEC\n0\nEOF\n");
        }
    }
    public sealed class FakePage
    {
        public FakeLayer LastCreatedLayer { get; private set; }
        public FakeLayer CreateLayer(string name)
        {
            LastCreatedLayer = new FakeLayer();
            return LastCreatedLayer;
        }
    }
    public sealed class FakeLayer
    {
        public FakeShapes Shapes { get; } = new FakeShapes();
        public FakeImportFilter LastFilter { get; private set; }
        public FakeImportFilter ImportEx(string dxfPath, int format)
        {
            if (format != 1296 || !File.Exists(dxfPath)) throw new Exception("ImportEx invalido");
            LastFilter = new FakeImportFilter(Shapes);
            return LastFilter;
        }
    }
    public sealed class FakeShapes { public int Count { get; set; } }
    public sealed class FakeImportFilter
    {
        private readonly FakeShapes _shapes;
        public int Scaling { get; set; } = -1;
        public FakeImportFilter(FakeShapes shapes) { _shapes=shapes; }
        public void Finish()
        {
            if (Scaling != 2) throw new Exception("Importacao sem escala metrica");
            _shapes.Count = 1;
        }
    }
}
