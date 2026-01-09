using Microsoft.AspNetCore.Mvc;
using OuvidoriaApi.Models;
using OuvidoriaApi.Services;

namespace OuvidoriaApi.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class OuvidoriaController : ControllerBase
    {
        private readonly TarjamentoService _tarjamentoService;
        private readonly ILogger<OuvidoriaController> _logger;

        public OuvidoriaController(TarjamentoService tarjamentoService, ILogger<OuvidoriaController> logger)
        {
            _tarjamentoService = tarjamentoService;
            _logger = logger;
        }

        [HttpPost("processar")]
        public async Task<ActionResult<ProcessamentoResponse>> ProcessarManifestacao([FromBody] ProcessamentoRequest request)
        {
            if (string.IsNullOrWhiteSpace(request.Texto))
            {
                return BadRequest(new { erro = "Texto não pode ser vazio" });
            }

            _logger.LogInformation("Processando manifestação de tamanho: {Length}", request.Texto.Length);

            var (textoTarjado, dadosOcultados) = await _tarjamentoService.TarjarDadosPessoaisAsync(request.Texto);

            var response = new ProcessamentoResponse
            {
                TextoOriginal = request.Texto,
                TextoTarjado = textoTarjado,
                DadosOcultados = dadosOcultados
            };

            return Ok(response);
        }

        [HttpGet("health")]
        public ActionResult Health()
        {
            return Ok(new { status = "OK", timestamp = DateTime.UtcNow });
        }
    }
}
