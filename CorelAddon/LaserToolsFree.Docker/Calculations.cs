using System;
using System.Globalization;

namespace LaserToolsFree.Docker
{
    /// <summary>Operacoes de validacao independentes da API do CorelDRAW.</summary>
    internal static class Calculations
    {
        public static double Number(string value, string name, double min, double max)
        {
            if (string.IsNullOrWhiteSpace(value)) throw new ArgumentException(name + " não pode ficar em branco.");
            double result;
            string normalized = value.Trim().Replace(',', '.');
            if (!double.TryParse(normalized, NumberStyles.Float, CultureInfo.InvariantCulture, out result)
                || double.IsNaN(result) || double.IsInfinity(result) || result < min || result > max)
                throw new ArgumentException(name + ": informe um número entre " + min + " e " + max + ".");
            return result;
        }

        public static int PositiveCount(string value, string name)
        {
            int result;
            if (!int.TryParse(value, NumberStyles.Integer, CultureInfo.InvariantCulture, out result)
                || result < 1 || result > 100)
                throw new ArgumentException(name + ": use um inteiro entre 1 e 100.");
            return result;
        }

        public static void CheckGrid(int rows, int cols, double gap, double width, double height)
        {
            if (rows < 1 || cols < 1 || rows * cols < 2 || rows * cols > 100)
                throw new ArgumentException("A grade deve ter entre 2 e 100 conjuntos no total.");
            if (double.IsNaN(gap) || double.IsInfinity(gap) || gap < 0 || gap > 10000)
                throw new ArgumentException("Espaçamento inválido (0 a 10000 mm).");
            if (width <= 0 || height <= 0 || double.IsNaN(width) || double.IsNaN(height)
                || double.IsInfinity(width) || double.IsInfinity(height))
                throw new ArgumentException("A seleção precisa ter largura e altura maiores que zero.");
        }

        // CorelDRAW 2022, enum cdrUnit: 1 inch, 2 foot, 3 mm,
        // 4 cm, 7 meter. Sem conversao silenciosa para pixels/pontos.
        public static double MmToDocumentUnits(double millimeters, int cdrUnit)
        {
            if (double.IsNaN(millimeters) || double.IsInfinity(millimeters) || millimeters < 0)
                throw new ArgumentException("Espacamento em mm invalido.");
            switch (cdrUnit)
            {
                case 1: return millimeters / 25.4;    // polegadas
                case 2: return millimeters / 304.8;   // pes
                case 3: return millimeters;           // mm
                case 4: return millimeters / 10.0;    // cm
                case 7: return millimeters / 1000.0;  // metros
                default:
                    throw new InvalidOperationException("Unidade do documento nao suportada para duplicacao segura: "
                        + cdrUnit + ". Use mm ou cm no documento. Nenhum objeto foi modificado.");
            }
        }

        // Converte dimensoes internas do CorelDRAW para mm, sem alterar o documento.
        public static double DocumentUnitsToMm(double value, int cdrUnit)
        {
            if (double.IsNaN(value) || double.IsInfinity(value) || value < 0)
                throw new ArgumentException("Dimensao interna invalida.");
            switch (cdrUnit)
            {
                case 1: return value * 25.4;  // polegadas
                case 2: return value * 304.8; // pes
                case 3: return value;         // mm
                case 4: return value * 10.0;  // cm
                case 7: return value * 1000.0;// metros
                default: throw new InvalidOperationException("Unidade interna nao suportada: " + cdrUnit);
            }
        }

        public static double ProportionalHeight(double currentW, double currentH, double newW)
        {
            if (currentW <= 0 || currentH <= 0 || newW <= 0) throw new ArgumentException("Medidas inválidas.");
            return currentH * (newW / currentW);
        }

        public static string Mm(double amount) { return amount.ToString("0.###", CultureInfo.GetCultureInfo("pt-BR")); }
    }
}
