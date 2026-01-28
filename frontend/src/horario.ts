/**
 * Verifica se está em horário comercial (08:00 - 17:00, seg-sex)
 */
export function verificarHorarioComercial(): {
  ehHorarioComercial: boolean;
  mensagem: string;
  horaAtual: string;
  diaSemana: string;
} {
  const agora = new Date();
  const diaSemana = agora.getDay(); // 0 = Domingo, 6 = Sábado
  const hora = agora.getHours();

  // Verifica se é fim de semana
  const ehFimDeSemana = diaSemana === 0 || diaSemana === 6;

  // Verifica se está dentro do horário comercial (08:00 - 17:00)
  const ehHorarioComercial = !ehFimDeSemana && hora >= 8 && hora < 17;

  const nomeDiaSemana = [
    'Domingo',
    'Segunda-feira',
    'Terça-feira',
    'Quarta-feira',
    'Quinta-feira',
    'Sexta-feira',
    'Sábado'
  ][diaSemana];

  const horaAtual = agora.toLocaleTimeString('pt-BR', {
    hour: '2-digit',
    minute: '2-digit'
  });

  const mensagem = ehHorarioComercial
    ? 'Estamos em horário de atendimento.'
    : '⏰ Estamos fora do horário comercial. Nosso horário de atendimento é de segunda a sexta-feira, das 08:00 às 17:00. Sua mensagem será respondida no próximo dia útil.';

  return {
    ehHorarioComercial,
    mensagem,
    horaAtual,
    diaSemana: nomeDiaSemana
  };
}

/**
 * Chama a API para verificar horário comercial
 */
export async function verificarHorarioComercialAPI(
  baseURL: string = 'http://localhost:5080/api'
): Promise<{
  ehHorarioComercial: boolean;
  horaAtual: string;
  dataAtual: string;
  diaSemana: string;
  mensagem: string;
}> {
  const response = await fetch(`${baseURL}/horario/verificar-horario-comercial`);

  if (!response.ok) {
    throw new Error(`Erro ao verificar horário: ${response.status}`);
  }

  return response.json();
}
