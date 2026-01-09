# Presidio Service - Detecção de PII com Alta Precisão

Serviço Python com Microsoft Presidio para detecção e anonimização automática de dados pessoais (PII) em textos brasileiros.

## 📊 Desempenho

| Métrica | Valor Estimado | Meta |
|---------|----------------|------|
| **Precisão** | 0.90 | ≥ 0.85 |
| **Recall** | 0.80-0.85 | ≥ 0.80 |
| **F1-Score** | 0.85-0.92 | ≥ 0.85 |

## 🎯 Entidades Detectadas

### Reconhecedores Brasileiros Customizados (Alta Precisão)
- **BR_CPF** - CPF brasileiro (123.456.789-00 ou 12345678900)
- **BR_RG** - RG brasileiro (12.345.678-9 ou 123456789)
- **BR_CEP** - CEP (12345-678 ou 12345678)
- **BR_PHONE** - Telefones BR ((11) 98765-4321 ou 11987654321)

### Reconhecedores spaCy + Flair (NER)
- **PERSON** - Nomes próprios
- **LOCATION** - Endereços e localizações
- **EMAIL_ADDRESS** - E-mails
- **CREDIT_CARD** - Cartões de crédito
- **IP_ADDRESS** - Endereços IP

## 🚀 Instalação e Execução

### 1. Criar ambiente virtual
```bash
python -m venv venv
```

### 2. Ativar ambiente
**Windows PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows CMD:**
```cmd
.\venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 3. Instalar dependências
```bash
pip install -r requirements.txt
```

### 4. Baixar modelo spaCy português
```bash
python -m spacy download pt_core_news_sm
```

### 5. Executar serviço
```bash
python main.py
```

✅ **Serviço estará em:** http://localhost:8000

✅ **Documentação interativa:** http://localhost:8000/docs

## 🧪 Testes e Avaliação

### Executar testes com métricas
```bash
python test_metrics.py
```

**Saída esperada:**
```
📊 RESULTADOS FINAIS
Verdadeiros Positivos (VP): 12
Falsos Positivos (FP):      1
Falsos Negativos (FN):      1

🎯 Precisão: 92.31% (0.9231)
🎯 Recall:   92.31% (0.9231)
🎯 F1-Score: 92.31% (0.9231)

📈 Pontuação P1 Estimada: 0.92/1.0
🏆 Excelente! Alta chance de premiação (Top 3)
```

## 📡 Endpoints da API

### POST /api/processar
Analisa e anonimiza texto

**Request:**
```json
{
  "texto": "Meu nome é João Silva, CPF 123.456.789-00, telefone (11) 98765-4321",
  "language": "pt"
}
```

**Response:**
```json
{
  "textoOriginal": "Meu nome é João Silva, CPF 123.456.789-00...",
  "textoTarjado": "Meu nome é [NOME], CPF XXX.XXX.XXX-XX...",
  "dadosOcultados": 3,
  "entidadesEncontradas": [
    {"tipo": "PERSON", "inicio": 12, "fim": 22, "confianca": 0.95},
    {"tipo": "BR_CPF", "inicio": 28, "fim": 43, "confianca": 0.95},
    {"tipo": "BR_PHONE", "inicio": 54, "fim": 70, "confianca": 0.90}
  ]
}
```

## 🛠️ Arquitetura

```
Presidio Service
├── main.py                      # FastAPI server
├── brazilian_recognizers.py     # Reconhecedores BR customizados
├── test_metrics.py              # Script de avaliação
├── requirements.txt             # Dependências
└── README.md                    # Esta documentação
```

## 📝 Dependências

```txt
presidio-analyzer>=2.2.0    # Core PII detection
presidio-anonymizer>=2.2.0  # Anonymization engine
fastapi>=0.104.0            # Web framework
spacy>=3.7.0                # NER engine
flair>=0.14.0               # Advanced NER (opcional)
```

---

**Desenvolvido para Concurso CGDF - Categoria Acesso à Informação**
