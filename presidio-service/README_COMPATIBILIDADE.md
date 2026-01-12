# Compatibilidade de Versão Python

## Versões Recomendadas
- **Python 3.10, 3.11 ou 3.12**

## Problema Conhecido
Se você está usando Python 3.13+ ou versões muito recentes, algumas dependências podem não ser compatíveis ainda, especialmente:
- `torch` (PyTorch)
- `flair`
- `stanza`

## Solução

### Opção 1: Usar pyenv (Recomendado)
```bash
# Instalar Python 3.11
pyenv install 3.11
pyenv local 3.11

# Criar ambiente virtual
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Instalar dependências
pip install -r requirements.txt
```

### Opção 2: Usar conda
```bash
# Criar ambiente com Python 3.11
conda create -n ouvidoria python=3.11
conda activate ouvidoria

# Instalar dependências
pip install -r requirements.txt
```

### Opção 3: Instalar Python 3.11 diretamente
1. Baixe Python 3.11 de [python.org](https://www.python.org/downloads/)
2. Instale em um diretório separado
3. Crie ambiente virtual com essa versão específica:
```bash
C:\Python311\python.exe -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Verificar Versão
```bash
python --version
# Deve mostrar Python 3.10.x, 3.11.x ou 3.12.x
```
