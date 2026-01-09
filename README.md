# Ouvidoria PWA - Sistema de Anonimização com Microsoft Presidio

Sistema de ouvidoria com proteção automática de dados pessoais (PII) usando .NET 9 Web API, TypeScript/Vite e **Microsoft Presidio** para detecção inteligente de informações sensíveis.

## ⚡ Quick Start - Comandos para Executar

### Pré-requisitos
- .NET 9 SDK - https://dotnet.microsoft.com/download/dotnet/9.0
- Python 3.8+ - https://www.python.org/downloads/
- Node.js 18+ - https://nodejs.org/

### Clone o Repositório
```bash
git clone https://github.com/guinb0/ouvidoria-pwa.git
cd ouvidoria-pwa
```

---

### 🐍 Terminal 1 - Presidio Service (EXECUTAR PRIMEIRO)

```powershell
cd presidio-service
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m spacy download pt_core_news_lg
python main.py
```

**⚠️ Nota sobre o modelo:** O `pt_core_news_lg` (~500MB) tem maior precisão. Se tiver problemas de espaço/memória, use:
```powershell
python -m spacy download pt_core_news_sm
```

**✅ Aguarde até ver:** `Uvicorn running on http://0.0.0.0:8000`

---

### 🔷 Terminal 2 - Backend .NET (EXECUTAR SEGUNDO)

```powershell
cd backend/OuvidoriaApi
dotnet restore
dotnet run
```

**✅ Aguarde até ver:** `Now listening on: http://localhost:5080`

---

### 🌐 Terminal 3 - Frontend (EXECUTAR POR ÚLTIMO)

```powershell
cd frontend
npm install
npm run dev
```

**✅ Acesse no navegador:** http://localhost:5173

---

## 📋 Visão Geral

Este projeto demonstra um sistema completo de anonimização de dados com três componentes principais:
- **Backend .NET**: API REST para processar manifestações
- **Presidio Service**: Serviço Python com IA para detecção de PII
- **Frontend**: Interface web responsiva em TypeScript

## 🏗️ Estrutura do Projeto

```
ouvidoria-pwa/
├── backend/
│   └── OuvidoriaApi/          # API .NET 9
│       ├── Controllers/        # Controladores da API
│       ├── Models/            # Modelos de dados
│       └── Services/          # Serviços de negócio
├── presidio-service/          # Serviço Python com Presidio
│   ├── main.py               # FastAPI com Presidio
│   ├── requirements.txt
│   └── README.md
└── frontend/
    └── src/                   # Frontend TypeScript com Vite
        ├── index.html
        ├── main.ts
        ├── api.ts
        └── style.css
```

## Tecnologias

- **Backend**: .NET 9 Web API com C#
- **PII Detection**: Microsoft Presidio (Python) com suporte a português
- **Frontend**: TypeScript + Vite
- **ML**: spaCy com modelo pt_core_news_sm

## Recursos

✅ **Detecção inteligente com Presidio:**
- Nomes de pessoas (NER com spaCy)
- E-mails
- Telefones
- Localizações
- CPF/SSN
- Cartões de crédito
- IPs e URLs
- Códigos bancários (IBAN)

✅ **Fallback com Regex** quando Presidio não está disponível
✅ **Interface responsiva** com feedback em tempo real

## 🚀 Como Executar (Guia Completo)

### Pré-requisitos

Antes de começar, certifique-se de ter instalado:
- **.NET 9 SDK** - [Download aqui](https://dotnet.microsoft.com/download/dotnet/9.0)
- **Python 3.8+** - [Download aqui](https://www.python.org/downloads/)
- **Node.js 18+** - [Download aqui](https://nodejs.org/)
- **Git** - [Download aqui](https://git-scm.com/)

### Clonando o Repositório

```bash
git clone https://github.com/guinb0/ouvidoria-pwa.git
cd ouvidoria-pwa
```

### 1️⃣ Presidio Service (Python) - INICIAR PRIMEIRO

```bash
cd presidio-service

# Criar ambiente virtual
python -m venv venv

# Ativar ambiente
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Windows CMD:
.\venv\Scripts\activate.bat
# Linux/Mac:
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Baixar modelos (IMPORTANTE!)
python -m spacy download pt_core_news_sm

# Executar serviço (Flair será baixado automaticamente na primeira execução)
python main.py
```

✅ **Presidio estará em:** `http://localhost:8000`
✅ **Teste:** Acesse `http://localhost:8000/docs` para ver a documentação interativa

### 2️⃣ Backend (.NET API) - INICIAR SEGUNDO

**Em outro terminal:**

```bash
cd backend/OuvidoriaApi

# Restaurar dependências (primeira vez)
dotnet restore

# Executar API
dotnet run
```

✅ **API estará em:** `http://localhost:5080`
✅ **Teste:** Acesse `http://localhost:5080/api/ouvidoria/health`

### 3️⃣ Frontend (TypeScript + Vite) - INICIAR POR ÚLTIMO

**Em outro terminal:**

```bash
cd frontend

# Instalar dependências (primeira vez)
npm install

# Executar frontend
npm run dev
```

✅ **Frontend estará em:** `http://localhost:5173`
✅ **Acesse no navegador** e teste enviando uma manifestação!

### 🎯 Ordem de Inicialização

**IMPORTANTE**: Execute nesta ordem para evitar erros:
1. 🐍 **Presidio Service** (porta 8000)
2. 🔷 **.NET API** (porta 5080) - depende do Presidio
3. 🌐 **Frontend** (porta 5173) - depende da API

### 🧪 Testando o Sistema

Exemplo de texto para testar:
```
Olá, meu nome é João Silva e meu email é joao@example.com.
Meu telefone é (11) 98765-4321 e moro em São Paulo.
Meu CPF é 123.456.789-00.
```

**Resultado esperado:**
```
Olá, meu nome é [NOME_PESSOA] e meu email é [EMAIL].
Meu telefone é [TELEFONE] e moro em [LOCALIZACAO].
Meu CPF é [CPF].
```

## Arquitetura

```
Frontend (TS) → .NET API → Presidio Service (Python)
                    ↓
              Fallback Regex (se Presidio indisponível)
```

## 📡 Endpoints da API

### Backend API (.NET) - `http://localhost:5080`
- **POST** `/api/ouvidoria/processar` - Processa e anonimiza manifestação
  ```json
  {
    "textoOriginal": "Olá, sou João Silva..."
  }
  ```
- **GET** `/api/ouvidoria/health` - Status da API e do Presidio

### Presidio Service (Python) - `http://localhost:8000`
- **POST** `/api/processar` - Analisa e anonimiza texto diretamente
- **GET** `/api/health` - Status do serviço Presidio
- **GET** `/api/entities` - Lista entidades detectadas suportadas
- **GET** `/docs` - Documentação Swagger interativa

## ⚙️ Configuração Avançada

### Alterar URL do Presidio Service

Editar [appsettings.json](backend/OuvidoriaApi/appsettings.json):

```json
{
  "PresidioService": {
    "Url": "http://localhost:8000"
  }
}
```

### Alterar Portas

- **Presidio**: Editar [main.py](presidio-service/main.py) linha `uvicorn.run(app, host="0.0.0.0", port=8000)`
- **.NET API**: Editar [launchSettings.json](backend/OuvidoriaApi/Properties/launchSettings.json)
- **Frontend**: Editar [vite.config.ts](frontend/vite.config.ts)

## 🛠️ Desenvolvimento e Extensão

### Adicionar Novos Tipos de Entidades no Presidio

Editar [main.py](presidio-service/main.py) e adicionar na lista `entities`:

```python
entities = [
    "PERSON",        # Nomes de pessoas
    "EMAIL_ADDRESS", # E-mails
    "PHONE_NUMBER",  # Telefones
    "LOCATION",      # Localizações
    "CPF",          # CPF brasileiro
    "CREDIT_CARD",  # Cartões de crédito
    "IP_ADDRESS",   # Endereços IP
    "URL",          # URLs
    "IBAN_CODE",    # Códigos bancários
    # Adicione mais aqui...
]
```

### Ajustar Padrões Regex de Fallback

Editar [TarjamentoService.cs](backend/OuvidoriaApi/Services/TarjamentoService.cs) no método de fallback.

### Personalizar Interface

Editar arquivos em [frontend/src](frontend/src):
- [main.ts](frontend/src/main.ts) - Lógica
- [style.css](frontend/src/style.css) - Estilos
- [api.ts](frontend/src/api.ts) - Comunicação com API

## 🚨 Troubleshooting

### Erro: "Presidio service unavailable"
- ✅ Verifique se o Presidio está rodando em `http://localhost:8000`
- ✅ Teste acessando `http://localhost:8000/docs`
- ✅ Confira se instalou o modelo spaCy: `python -m spacy download pt_core_news_sm`

### Erro: "Failed to fetch" no frontend
- ✅ Verifique se a API .NET está rodando em `http://localhost:5080`
- ✅ Confira o console do navegador para erros CORS

### Erro: "Cannot find module" no frontend
- ✅ Execute `npm install` na pasta frontend

### Erro ao ativar venv no PowerShell
- ✅ Execute: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
- ✅ Depois: `.\venv\Scripts\Activate.ps1`

## 📝 Licença

Este projeto foi desenvolvido para fins educacionais e demonstração de tecnologias.

## 👥 Contribuindo

Sinta-se à vontade para:
1. Fazer fork do projeto
2. Criar uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abrir um Pull Request

## 📧 Contato

Para dúvidas ou sugestões sobre o projeto, abra uma issue no GitHub.

---

**Desenvolvido com ❤️ usando .NET 9, TypeScript e Microsoft Presidio**
