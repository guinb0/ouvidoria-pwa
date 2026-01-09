export interface ProcessamentoRequest {
  texto: string;
}

export interface ProcessamentoResponse {
  textoOriginal: string;
  textoTarjado: string;
  dadosOcultados: number;
}

class OuvidoriaAPI {
  private baseURL: string;

  constructor(baseURL: string = 'http://localhost:5080/api') {
    this.baseURL = baseURL;
  }

  async processar(texto: string): Promise<ProcessamentoResponse> {
    const response = await fetch(`${this.baseURL}/ouvidoria/processar`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ texto } as ProcessamentoRequest),
    });

    if (!response.ok) {
      throw new Error(`Erro na API: ${response.status}`);
    }

    return response.json();
  }

  async verificarSaude(): Promise<{ status: string; timestamp: string }> {
    const response = await fetch(`${this.baseURL}/ouvidoria/health`);
    
    if (!response.ok) {
      throw new Error(`Erro ao verificar saúde da API: ${response.status}`);
    }

    return response.json();
  }
}

export default OuvidoriaAPI;
