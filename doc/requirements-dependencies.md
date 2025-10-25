# Requirements e Dependências - Streamlit Cloud

## Visão Geral
Este documento detalha como gerenciar dependências Python para aplicações Streamlit Cloud, incluindo otimização, versionamento e troubleshooting.

## Estrutura do requirements.txt

### Formato Básico
```txt
# Dependências principais
streamlit>=1.28.0
pandas>=1.5.0
numpy>=1.24.0

# Dependências opcionais
plotly>=5.15.0
requests>=2.28.0
```

### Formato Avançado com Versões Específicas
```txt
# Core Streamlit
streamlit==1.28.1
streamlit-option-menu==0.3.6
streamlit-aggrid==0.3.4

# Data Processing
pandas==2.0.3
numpy==1.24.3
scipy==1.11.1

# Visualization
plotly==5.15.0
matplotlib==3.7.2
seaborn==0.12.2
altair==5.1.2

# Machine Learning
scikit-learn==1.3.0
tensorflow==2.13.0
torch==2.0.1

# Database
psycopg2-binary==2.9.7
sqlalchemy==2.0.19
pymongo==4.4.1

# APIs and Web
requests==2.31.0
httpx==0.24.1
fastapi==0.100.0

# Utilities
python-dotenv==1.0.0
pyyaml==6.0.1
pillow==10.0.0
```

## Categorização de Dependências

### 1. Dependências Essenciais
```txt
# Essenciais para funcionamento básico
streamlit>=1.28.0
pandas>=1.5.0
numpy>=1.24.0
```

### 2. Dependências de Visualização
```txt
# Gráficos e visualizações
plotly>=5.15.0
matplotlib>=3.7.0
seaborn>=0.12.0
altair>=5.1.0
bokeh>=3.2.0
```

### 3. Dependências de Machine Learning
```txt
# ML e Data Science
scikit-learn>=1.3.0
tensorflow>=2.13.0
torch>=2.0.0
xgboost>=1.7.0
lightgbm>=4.0.0
```

### 4. Dependências de Banco de Dados
```txt
# Bancos de dados
psycopg2-binary>=2.9.0
sqlalchemy>=2.0.0
pymongo>=4.4.0
redis>=4.6.0
```

### 5. Dependências de APIs
```txt
# Integração com APIs
requests>=2.28.0
httpx>=0.24.0
aiohttp>=3.8.0
websockets>=11.0.0
```

## Otimização de Dependências

### 1. Minimizar Tamanho
```txt
# Use versões específicas para evitar conflitos
streamlit==1.28.1
pandas==2.0.3
numpy==1.24.3

# Evite dependências desnecessárias
# requests>=2.28.0  # Remover se não usar
# matplotlib>=3.7.0  # Remover se usar apenas plotly
```

### 2. Resolver Conflitos
```txt
# Especificar versões compatíveis
tensorflow==2.13.0
numpy==1.24.3  # Compatível com TensorFlow 2.13
pandas==2.0.3  # Compatível com NumPy 1.24
```

### 3. Dependências Condicionais
```python
# No código Python
try:
    import tensorflow as tf
    HAS_TENSORFLOW = True
except ImportError:
    HAS_TENSORFLOW = False

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

# Usar condicionalmente
if HAS_TENSORFLOW:
    # Código específico do TensorFlow
    pass
```

## Configurações Específicas por Ambiente

### 1. Desenvolvimento Local
```txt
# requirements-dev.txt
-r requirements.txt

# Ferramentas de desenvolvimento
pytest>=7.4.0
black>=23.7.0
flake8>=6.0.0
mypy>=1.5.0
jupyter>=1.0.0
```

### 2. Produção (Streamlit Cloud)
```txt
# requirements.txt (otimizado para produção)
streamlit>=1.28.0
pandas>=1.5.0
numpy>=1.24.0
plotly>=5.15.0
requests>=2.28.0
python-dotenv>=1.0.0
```

### 3. Testes
```txt
# requirements-test.txt
-r requirements.txt

# Ferramentas de teste
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-mock>=3.11.0
```

## Gerenciamento de Versões

### 1. Versionamento Semântico
```txt
# Major.Minor.Patch
streamlit==1.28.1  # Versão específica
pandas>=1.5.0      # Mínimo 1.5.0
numpy~=1.24.0      # Compatível com 1.24.x
```

### 2. Pinning de Versões
```txt
# Versões fixas para estabilidade
streamlit==1.28.1
pandas==2.0.3
numpy==1.24.3
plotly==5.15.0
```

### 3. Ranges de Versões
```txt
# Ranges flexíveis
streamlit>=1.28.0,<2.0.0
pandas>=1.5.0,<3.0.0
numpy>=1.24.0,<2.0.0
```

## Dependências por Categoria de Aplicação

### 1. Dashboard de Dados
```txt
streamlit>=1.28.0
pandas>=1.5.0
numpy>=1.24.0
plotly>=5.15.0
seaborn>=0.12.0
altair>=5.1.0
```

### 2. Machine Learning
```txt
streamlit>=1.28.0
pandas>=1.5.0
numpy>=1.24.0
scikit-learn>=1.3.0
tensorflow>=2.13.0
plotly>=5.15.0
```

### 3. Análise Financeira
```txt
streamlit>=1.28.0
pandas>=1.5.0
numpy>=1.24.0
yfinance>=0.2.18
plotly>=5.15.0
ta>=0.10.2
```

### 4. Processamento de Imagens
```txt
streamlit>=1.28.0
pillow>=10.0.0
opencv-python>=4.8.0
numpy>=1.24.0
matplotlib>=3.7.0
```

### 5. Integração com APIs
```txt
streamlit>=1.28.0
requests>=2.28.0
httpx>=0.24.0
aiohttp>=3.8.0
websockets>=11.0.0
```

## Troubleshooting de Dependências

### 1. Conflitos de Versões
```bash
# Verificar dependências instaladas
pip list

# Verificar conflitos
pip check

# Resolver conflitos
pip install --upgrade package-name
```

### 2. Dependências Incompatíveis
```txt
# Exemplo de resolução de conflito
# TensorFlow requer NumPy específico
tensorflow==2.13.0
numpy==1.24.3  # Versão compatível
```

### 3. Dependências Opcionais
```python
# No código Python
def optional_import(module_name, package_name=None):
    """Importa módulo opcionalmente"""
    try:
        return __import__(module_name)
    except ImportError:
        if package_name:
            st.warning(f"Instale {package_name} para usar esta funcionalidade")
        return None

# Usar importação opcional
tensorflow = optional_import("tensorflow", "tensorflow>=2.13.0")
if tensorflow:
    # Usar TensorFlow
    pass
```

### 4. Dependências de Sistema
```txt
# Para dependências que requerem compilação
# Use versões pré-compiladas quando possível
psycopg2-binary>=2.9.0  # Em vez de psycopg2
pillow>=10.0.0          # Em vez de PIL
```

## Boas Práticas

### 1. Organização
```txt
# Agrupar por categoria
# === Core Dependencies ===
streamlit>=1.28.0
pandas>=1.5.0
numpy>=1.24.0

# === Visualization ===
plotly>=5.15.0
matplotlib>=3.7.0

# === Machine Learning ===
scikit-learn>=1.3.0
tensorflow>=2.13.0
```

### 2. Comentários
```txt
# Core Streamlit dependencies
streamlit>=1.28.0
streamlit-option-menu>=0.3.6

# Data processing
pandas>=1.5.0
numpy>=1.24.0

# Visualization libraries
plotly>=5.15.0
matplotlib>=3.7.0
```

### 3. Versionamento
```txt
# Usar versões específicas para produção
streamlit==1.28.1
pandas==2.0.3
numpy==1.24.3

# Usar ranges para desenvolvimento
plotly>=5.15.0,<6.0.0
```

## Exemplos Práticos

### 1. App de Análise de Dados
```txt
streamlit>=1.28.0
pandas>=1.5.0
numpy>=1.24.0
plotly>=5.15.0
seaborn>=0.12.0
altair>=5.1.0
scipy>=1.11.0
```

### 2. App de Machine Learning
```txt
streamlit>=1.28.0
pandas>=1.5.0
numpy>=1.24.0
scikit-learn>=1.3.0
tensorflow>=2.13.0
plotly>=5.15.0
joblib>=1.3.0
```

### 3. App de Visualização
```txt
streamlit>=1.28.0
plotly>=5.15.0
matplotlib>=3.7.0
seaborn>=0.12.0
bokeh>=3.2.0
altair>=5.1.0
```

### 4. App de Integração com APIs
```txt
streamlit>=1.28.0
requests>=2.28.0
httpx>=0.24.0
aiohttp>=3.8.0
websockets>=11.0.0
python-dotenv>=1.0.0
```

## Recursos Adicionais

### Links Úteis
- [PyPI - Python Package Index](https://pypi.org/)
- [pip Documentation](https://pip.pypa.io/)
- [Python Packaging User Guide](https://packaging.python.org/)

### Ferramentas
- [pip-tools](https://github.com/jazzband/pip-tools) - Gerenciamento de dependências
- [pipenv](https://pipenv.pypa.io/) - Gerenciador de dependências
- [poetry](https://python-poetry.org/) - Gerenciamento moderno de dependências

### Verificação de Compatibilidade
```bash
# Verificar compatibilidade
pip check

# Verificar dependências
pip show package-name

# Listar dependências
pip list --format=freeze
```
