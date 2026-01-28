using Microsoft.AspNetCore.Mvc;

namespace OuvidoriaApi.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class HorarioController : ControllerBase
    {
        private readonly ILogger<HorarioController> _logger;

        public HorarioController(ILogger<HorarioController> logger)
        {
            _logger = logger;
        }

        [HttpGet("verificar-horario-comercial")]
        public ActionResult<HorarioComercialResponse> VerificarHorarioComercial()
        {
            var agora = DateTime.Now;
            var diaSemana = agora.DayOfWeek;
            var hora = agora.Hour;

            // Verifica se é fim de semana
            bool ehFimDeSemana = diaSemana == DayOfWeek.Saturday || diaSemana == DayOfWeek.Sunday;

            // Verifica se está dentro do horário comercial (08:00 - 17:00)
            bool ehHorarioComercial = !ehFimDeSemana && hora >= 8 && hora < 17;

            var response = new HorarioComercialResponse
            {
                EhHorarioComercial = ehHorarioComercial,
                HoraAtual = agora.ToString("HH:mm"),
                DataAtual = agora.ToString("dd/MM/yyyy"),
                DiaSemana = ObterNomeDiaSemana(diaSemana),
                Mensagem = ehHorarioComercial 
                    ? "Estamos em horário de atendimento." 
                    : "Estamos fora do horário comercial. Nosso horário de atendimento é de segunda a sexta-feira, das 08:00 às 17:00. Sua mensagem será respondida no próximo dia útil."
            };

            _logger.LogInformation(
                "Verificação de horário: {Data} {Hora} - {DiaSemana} - Comercial: {EhComercial}",
                response.DataAtual, response.HoraAtual, response.DiaSemana, ehHorarioComercial
            );

            return Ok(response);
        }

        private string ObterNomeDiaSemana(DayOfWeek dia)
        {
            return dia switch
            {
                DayOfWeek.Sunday => "Domingo",
                DayOfWeek.Monday => "Segunda-feira",
                DayOfWeek.Tuesday => "Terça-feira",
                DayOfWeek.Wednesday => "Quarta-feira",
                DayOfWeek.Thursday => "Quinta-feira",
                DayOfWeek.Friday => "Sexta-feira",
                DayOfWeek.Saturday => "Sábado",
                _ => "Desconhecido"
            };
        }
    }

    public class HorarioComercialResponse
    {
        public bool EhHorarioComercial { get; set; }
        public string HoraAtual { get; set; } = string.Empty;
        public string DataAtual { get; set; } = string.Empty;
        public string DiaSemana { get; set; } = string.Empty;
        public string Mensagem { get; set; } = string.Empty;
    }
}
