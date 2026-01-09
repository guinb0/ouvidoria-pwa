import OuvidoriaAPI from './api';

const api = new OuvidoriaAPI();

// Elementos do DOM
const inputText = document.getElementById('inputText') as HTMLTextAreaElement;
const outputText = document.getElementById('outputText') as HTMLParagraphElement;
const submitButton = document.getElementById('submitButton') as HTMLButtonElement;
const statusMessage = document.getElementById('statusMessage') as HTMLDivElement;

async function processarManifestacao(): Promise<void> {
  const texto = inputText.value.trim();

  if (!texto) {
    mostrarMensagem('Por favor, digite uma manifestação.', 'error');
    return;
  }

  try {
    submitButton.disabled = true;
    submitButton.textContent = 'Processando...';
    mostrarMensagem('Processando manifestação...', 'info');

    const resultado = await api.processar(texto);

    outputText.textContent = resultado.textoTarjado;
    mostrarMensagem(
      `Manifestação registrada! ${resultado.dadosOcultados} dado(s) pessoal(is) ocultado(s).`,
      'success'
    );
  } catch (error) {
    console.error('Erro ao processar:', error);
    mostrarMensagem(
      'Erro ao processar manifestação. Verifique se a API está rodando.',
      'error'
    );
  } finally {
    submitButton.disabled = false;
    submitButton.textContent = 'Enviar manifestação';
  }
}

function mostrarMensagem(mensagem: string, tipo: 'success' | 'error' | 'info'): void {
  statusMessage.textContent = mensagem;
  statusMessage.className = `status-message ${tipo}`;
  statusMessage.style.display = 'block';

  setTimeout(() => {
    if (tipo !== 'success') {
      statusMessage.style.display = 'none';
    }
  }, 5000);
}

// Event listener
submitButton.addEventListener('click', processarManifestacao);

// Verificar saúde da API ao carregar
window.addEventListener('load', async () => {
  try {
    await api.verificarSaude();
    console.log('API conectada com sucesso');
  } catch (error) {
    console.warn('API não está disponível:', error);
    mostrarMensagem(
      'Aviso: API não está disponível. Inicie o backend para processar manifestações.',
      'error'
    );
  }
});
