# Instalar Presidio Service

## 1. Instalar Python (se necessário)
Certifique-se de ter Python 3.8+ instalado

## 2. Criar ambiente virtual
```bash
cd presidio-service
python -m venv venv
```

## 3. Ativar ambiente virtual
Windows:
```bash
.\venv\Scripts\Activate.ps1
```

Linux/Mac:
```bash
source venv/bin/activate
```

## 4. Instalar dependências
```bash
pip install -r requirements.txt
```

## 5. Baixar modelo de português do spaCy
```bash
python -m spacy download pt_core_news_sm
```

## 6. Executar serviço
```bash
python main.py
```

O serviço estará disponível em: http://localhost:8000

## Testar
```bash
curl -X POST http://localhost:8000/api/processar \
  -H "Content-Type: application/json" \
  -d '{"texto": "Meu nome é João Silva e meu email é joao@example.com"}'
```
