using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Web.Script.Serialization;

namespace LaserToolsFree.Docker
{
    internal sealed class EngineAnswer
    {
        public string Output { get; set; }
        public string Summary { get; set; }
    }

    /// <summary>Invoca apenas o motor local instalado; nunca executa argumentos não validados via cmd.exe.</summary>
    internal static class EngineRunner
    {
        // Motor portátil e editor na mesma árvore do complemento instalado, sem Python no PC.
        public static string EngineDir
        {
            get { return Path.Combine(Path.GetDirectoryName(typeof(EngineRunner).Assembly.Location), "engine"); }
        }

        private static string Quote(string value)
        {
            return "\"" + value.Replace("\"", "\\\"") + "\"";
        }

        public static EngineAnswer Execute(string operation, string input, IDictionary<string,string> options)
        {
            string executable = Path.Combine(EngineDir, "LaserDXFEngine.exe");
            if (!File.Exists(executable))
                throw new FileNotFoundException("Motor portátil não encontrado. Reinstale o pacote compilado: " + executable);
            if (!File.Exists(input)) throw new FileNotFoundException("DXF de entrada não encontrado: " + input);
            var args=Quote(operation)+" "+Quote(input);
            foreach (var entry in options) args+=" --"+entry.Key+" "+Quote(entry.Value);
            var info=new ProcessStartInfo(executable,args)
            {
                UseShellExecute=false,CreateNoWindow=true,RedirectStandardOutput=true,RedirectStandardError=true,
                WorkingDirectory=EngineDir
            };
            using (var process=Process.Start(info))
            {
                if (process==null) throw new IOException("Falha ao iniciar o motor DXF.");
                // Leitura assíncrona para evitar deadlock por buffer cheio.
                var stdout=process.StandardOutput.ReadToEndAsync();
                var stderr=process.StandardError.ReadToEndAsync();
                if (!process.WaitForExit(180000))
                {
                    try { process.Kill(); } catch { }
                    throw new TimeoutException("Tempo limite de 180 segundos para processar o DXF.");
                }
                string output=stdout.GetAwaiter().GetResult();
                string error=stderr.GetAwaiter().GetResult();
                if (process.ExitCode!=0) throw new InvalidOperationException("O DXF não foi processado: "+error);
                var parsed=new JavaScriptSerializer().Deserialize<Dictionary<string,object>>(output.Trim());
                if (parsed==null || !parsed.ContainsKey("ok") || !(bool)parsed["ok"])
                    throw new InvalidOperationException("Resposta do motor DXF inválida.");
                string outPath=parsed.ContainsKey("output")?Convert.ToString(parsed["output"]):"";
                string summary=parsed.ContainsKey("summary")?Convert.ToString(parsed["summary"]):"Concluído.";
                if (!string.IsNullOrWhiteSpace(outPath))
                {
                    if (!Path.IsPathRooted(outPath) || !File.Exists(outPath) || new FileInfo(outPath).Length<100)
                        throw new IOException("O motor não gerou um DXF de saída válido.");
                    if (string.Equals(Path.GetFullPath(outPath),Path.GetFullPath(input),StringComparison.OrdinalIgnoreCase))
                        throw new IOException("O motor tentou sobrescrever o arquivo original, operação bloqueada.");
                }
                return new EngineAnswer { Output=outPath, Summary=summary };
            }
        }
    }
}
