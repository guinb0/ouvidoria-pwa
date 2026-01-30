# 🛡️ Ouvidoria PWA — Sistema de Anonimização com Microsoft Presidio

Sistema de **Ouvidoria com Proteção Automática de Dados Pessoais (PII)** utilizando **.NET 9 Web API**, **Microsoft Presidio (Python)** e **TypeScript + Vite**, com foco em **LGPD**, **Privacy by Design** e **anonimização inteligente de dados sensíveis**.

---

## ⚡ Como Executar (Passo a Passo)

### 📋 Pré-requisitos

Instale antes de começar:

* **.NET 9 SDK**
  👉 [https://dotnet.microsoft.com/download/dotnet/9.0](https://dotnet.microsoft.com/download/dotnet/9.0)

* **Python 3.8 – 3.12**
  👉 [https://www.python.org/downloads/](https://www.python.org/downloads/)

* **Node.js 18+**
  👉 [https://nodejs.org/](https://nodejs.org/)

* **Git**
  👉 [https://git-scm.com/downloads](https://git-scm.com/downloads)

---

## 📥 Clone o Projeto

```bash
git clone https://github.com/guinb0/ouvidoria-pwa.git
cd ouvidoria-pwa
```

---

## 📂 Estrutura do Projeto

```text
ouvidoria-pwa/
├── backend/           # API .NET 9
├── presidio-service/  # Serviço Python com Microsoft Presidio
└── frontend/          # Interface Web (TypeScript + Vite)
```

---

## 1️⃣ Presidio Service (EXECUTAR PRIMEIRO)

```bash
cd presidio-service

python -m venv venv
python -m pip install -r requirements.txt

python main.py
```

➡ Serviço rodando em:

```
http://localhost:8000
```

---

## 2️⃣ Backend .NET (EXECUTAR SEGUNDO)

```bash
cd backend/OuvidoriaApi

dotnet restore
dotnet run
```

➡ API rodando em:

```
http://localhost:5080
```

---

## 3️⃣ Frontend (EXECUTAR POR ÚLTIMO)

```bash
cd frontend

npm install
npm run dev
```

➡ Acesse no navegador:

```
http://localhost:5173
```

---

## 🧪 Teste Rápido

### Texto de entrada

```text
Meu nome é João Silva.
CPF: 123.456.789-00
Email: joao@email.com
Telefone: (11) 98765-4321
```

### Resultado esperado

```text
Meu nome é [NOME].
CPF: [CPF]
Email: [EMAIL]
Telefone: [TELEFONE]
```

---

## 📌 Sobre o Projeto

Sistema de **Ouvidoria com Anonimização Automática de Dados Sensíveis**, capaz de detectar e mascarar:

* CPF
* E-mails
* Telefones
* Nomes de pessoas
* Localizações
* Outros identificadores pessoais

---

## 🛠 Tecnologias Utilizadas

* **.NET 9 Web API** — backend
* **Microsoft Presidio (Python)** — detecção inteligente de PII
* **spaCy (Português)** — NLP
* **TypeScript + Vite** — frontend moderno

---

## 🔐 Princípios Aplicados

* LGPD
* Privacy by Design
* Segurança de dados
* Automação de anonimização

---

## 🏗 Arquitetura do Sistema

```text
Frontend (TypeScript)
        ↓
.NET 9 API
        ↓
Microsoft Presidio (Python)
        ↓
Fallback Regex (caso indisponível)
```

---

## 🔍 Funcionalidades

*  Detecção automática de dados pessoais
*  Anonimização em tempo real
*  Processamento em português (spaCy)
*  Fallback com Regex caso IA falhe
*  Interface web simples e responsiva
*  API REST pronta para integração

---

## 📡 Endpoints Principais

### Backend (.NET)

| Método | Endpoint                   | Descrição                    |
| ------ | -------------------------- | ---------------------------- |
| POST   | `/api/ouvidoria/processar` | Processa e anonimiza o texto |
| GET    | `/api/ouvidoria/health`    | Status da API                |

---

### Presidio Service (Python)

| Método | Endpoint         | Descrição                 |
| ------ | ---------------- | ------------------------- |
| POST   | `/api/processar` | Analisa e anonimiza texto |
| GET    | `/api/health`    | Status do serviço         |
| GET    | `/docs`          | Documentação Swagger      |

---

