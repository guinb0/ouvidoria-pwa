namespace OuvidoriaApi.Models
{
    public class ProcessamentoResponse
    {
        public string TextoOriginal { get; set; } = string.Empty;
        public string TextoTarjado { get; set; } = string.Empty;
        public int DadosOcultados { get; set; }
    }
}
