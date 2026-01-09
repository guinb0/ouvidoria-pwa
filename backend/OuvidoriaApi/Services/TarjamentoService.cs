using System.Text.RegularExpressions;
using System.Text.Json;

namespace OuvidoriaApi.Services
{
    public class PresidioRequest
    {
        public string texto { get; set; } = string.Empty;
        public string language { get; set; } = "pt";
    }

    public class PresidioResponse
    {
        public string textoOriginal { get; set; } = string.Empty;
        public string textoTarjado { get; set; } = string.Empty;
        public int dadosOcultados { get; set; }
    }

    public class TarjamentoService
    {
        private readonly HttpClient _httpClient;
        private readonly ILogger<TarjamentoService> _logger;
        private readonly string _presidioUrl;

        public TarjamentoService(HttpClient httpClient, ILogger<TarjamentoService> logger, IConfiguration configuration)
        {
            _httpClient = httpClient;
            _logger = logger;
            _presidioUrl = configuration["PresidioService:Url"] ?? "http://localhost:8000";
        }

        public async Task<(string TextoTarjado, int DadosOcultados)> TarjarDadosPessoaisAsync(string texto)
        {
            try
            {
                // Tentar usar Presidio primeiro
                var request = new PresidioRequest { texto = texto, language = "pt" };
                var json = JsonSerializer.Serialize(request);
                var content = new StringContent(json, System.Text.Encoding.UTF8, "application/json");

                var response = await _httpClient.PostAsync($"{_presidioUrl}/api/processar", content);

                if (response.IsSuccessStatusCode)
                {
                    var responseJson = await response.Content.ReadAsStringAsync();
                    var presidioResponse = JsonSerializer.Deserialize<PresidioResponse>(responseJson, new JsonSerializerOptions 
                    { 
                        PropertyNameCaseInsensitive = true 
                    });

                    if (presidioResponse != null)
                    {
                        _logger.LogInformation("Presidio processou com sucesso: {Count} dados ocultados", presidioResponse.dadosOcultados);
                        return (presidioResponse.textoTarjado, presidioResponse.dadosOcultados);
                    }
                }

                _logger.LogWarning("Presidio não disponível, usando fallback regex");
                return TarjarDadosPessoaisFallback(texto);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Erro ao chamar Presidio, usando fallback");
                return TarjarDadosPessoaisFallback(texto);
            }
        }

        public (string TextoTarjado, int DadosOcultados) TarjarDadosPessoais(string texto)
        {
            // Método síncrono mantido para compatibilidade
            return TarjarDadosPessoaisFallback(texto);
        }

        private (string TextoTarjado, int DadosOcultados) TarjarDadosPessoaisFallback(string texto)
        {
            if (string.IsNullOrWhiteSpace(texto))
            {
                return (texto, 0);
            }

            int contador = 0;
            string textoTarjado = texto;

            // CPF (formato 000.000.000-00 ou 00000000000)
            var cpfMatches = Regex.Matches(textoTarjado, @"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b|\b\d{11}\b");
            contador += cpfMatches.Count;
            textoTarjado = Regex.Replace(textoTarjado, @"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b|\b\d{11}\b", "[CPF OCULTO]");

            // Email
            var emailMatches = Regex.Matches(textoTarjado, @"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}", RegexOptions.IgnoreCase);
            contador += emailMatches.Count;
            textoTarjado = Regex.Replace(textoTarjado, @"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}", "[EMAIL OCULTO]", RegexOptions.IgnoreCase);

            // Telefone (formato (00) 0000-0000 ou (00) 00000-0000)
            var telefoneMatches = Regex.Matches(textoTarjado, @"\b\(?\d{2}\)?\s?\d{4,5}-?\d{4}\b");
            contador += telefoneMatches.Count;
            textoTarjado = Regex.Replace(textoTarjado, @"\b\(?\d{2}\)?\s?\d{4,5}-?\d{4}\b", "[TELEFONE OCULTO]");

            // Endereço (heurística simples)
            var enderecoMatches = Regex.Matches(textoTarjado, @"\b(Rua|Avenida|Av\.|Travessa|Quadra|Condomínio|Conj\.)\s+[\w\s]+", RegexOptions.IgnoreCase);
            contador += enderecoMatches.Count;
            textoTarjado = Regex.Replace(textoTarjado, @"\b(Rua|Avenida|Av\.|Travessa|Quadra|Condomínio|Conj\.)\s+[\w\s]+", "[ENDEREÇO OCULTO]", RegexOptions.IgnoreCase);

            // Nomes próprios (duas palavras começando com maiúscula)
            var nomeMatches = Regex.Matches(textoTarjado, @"\b([A-ZÀÁÂÃÉÊÍÓÔÕÚÇ][a-zàáâãéêíóôõúç]+\s[A-ZÀÁÂÃÉÊÍÓÔÕÚÇ][a-zàáâãéêíóôõúç]+)\b");
            contador += nomeMatches.Count;
            textoTarjado = Regex.Replace(textoTarjado, @"\b([A-ZÀÁÂÃÉÊÍÓÔÕÚÇ][a-zàáâãéêíóôõúç]+\s[A-ZÀÁÂÃÉÊÍÓÔÕÚÇ][a-zàáâãéêíóôõúç]+)\b", "[NOME OCULTO]");

            return (textoTarjado, contador);
        }
    }
}
