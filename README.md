Ouvidoria PWA — Sistema de Anonimização com Microsoft Presidio
⚡ Como Executar (Passo a Passo)
Pré-requisitos

.NET 9

Python 3.8–3.12

Node.js 18+

Clone o projeto:

git clone https://github.com/guinb0/ouvidoria-pwa.git
cd ouvidoria-pwa

📂 Estrutura do Projeto
ouvidoria-pwa/
├── backend/           # API .NET
├── presidio-service/  # Serviço Presidio
└── frontend/          # Interface Web

1️⃣ Presidio Service (EXECUTAR PRIMEIRO)
cd presidio-service
python -m venv venv
python -m pip install -r requirements.txt
python -m spacy download pt_core_news_sm
python main.py


➡ Serviço rodando em: http://localhost:8000

2️⃣ Backend .NET (EXECUTAR SEGUNDO)
cd backend/OuvidoriaApi
dotnet restore
dotnet run


➡ API rodando em: http://localhost:5080

3️⃣ Frontend (EXECUTAR POR ÚLTIMO)
cd frontend
npm install
npm run dev


➡ Acesse: http://localhost:5173

🧪 Teste Rápido

Texto de entrada:

Meu nome é João Silva. CPF: 123.456.789-00
Email: joao@email.com
Telefone: (11) 98765-4321


Resultado esperado:

Meu nome é [NOME]. CPF: [CPF]
Email: [EMAIL]
Telefone: [TELEFONE]

📌 Sobre o Projeto

Sistema de Ouvidoria com Proteção Automática de Dados Pessoais (PII) usando:

.NET 9 Web API (backend)

Microsoft Presidio (Python) para detecção inteligente de dados sensíveis

TypeScript + Vite (frontend)

O sistema identifica e anonimiza automaticamente CPF, e-mail, telefone, nomes e localizações, aplicando NLP e boas práticas de LGPD e privacy by design.

🏗 Arquitetura
Frontend → .NET API → Presidio Service (Python)
                    ↓
             Fallback Regex (se indisponível)

🔍 Funcionalidades

-  Detecção automática de dados pessoais
-  Anonimização em tempo real
-  Suporte a português (spaCy)
-  Fallback caso Presidio falhe
-  Interface web simples e responsiva

📡 Endpoints Principais
Backend (.NET)

POST /api/ouvidoria/processar

GET /api/ouvidoria/health

Presidio (Python)

POST /api/processar

GET /api/health

GET /docs
