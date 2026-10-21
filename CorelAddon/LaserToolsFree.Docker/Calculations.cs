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

        public static double ProportionalHeight(double currentW, double currentH, double newW)
        {
            if (currentW <= 0 || currentH <= 0 || newW <= 0) throw new ArgumentException("Medidas inválidas.");
            return currentH * (newW / currentW);
        }

        public static string Mm(double amount) { return amount.ToString("0.###", CultureInfo.GetCultureInfo("pt-BR")); }
    }
}
