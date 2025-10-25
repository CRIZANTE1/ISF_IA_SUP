# Guia de Deploy - Streamlit Cloud

## Visão Geral
Este guia completo explica como fazer deploy de aplicações Streamlit no Streamlit Cloud, desde a preparação até a manutenção.

## Pré-requisitos

### 1. Contas Necessárias
- [x] Conta GitHub ativa
- [x] Repositório público no GitHub
- [x] Aplicação Streamlit funcional localmente

### 2. Estrutura do Projeto
```
projeto/
├── main.py                 # Arquivo principal
├── requirements.txt        # Dependências Python
├── .streamlit/
│   ├── config.toml        # Configurações do Streamlit
│   └── secrets.toml       # Secrets (não commitar)
├── .gitignore             # Ignorar arquivos sensíveis
├── README.md              # Documentação
└── doc/                   # Documentação adicional
```

## Preparação do Projeto

### 1. Arquivo Principal (main.py)
```python
import streamlit as st
import pandas as pd
import numpy as np

# Configuração da página
st.set_page_config(
    page_title="Minha App",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título da aplicação
st.title("🚀 Minha Aplicação Streamlit")

# Sidebar
with st.sidebar:
    st.header("Configurações")
    option = st.selectbox("Escolha uma opção:", ["Opção 1", "Opção 2", "Opção 3"])

# Conteúdo principal
st.header("Dashboard Principal")
st.write(f"Você selecionou: {option}")

# Exemplo de gráfico
chart_data = pd.DataFrame(
    np.random.randn(20, 3),
    columns=['A', 'B', 'C']
)
st.line_chart(chart_data)
```

### 2. Requirements.txt
```txt
streamlit>=1.28.0
pandas>=1.5.0
numpy>=1.24.0
plotly>=5.15.0
requests>=2.28.0
python-dotenv>=1.0.0
```

### 3. Configuração (.streamlit/config.toml)
```toml
[server]
port = 8501
enableCORS = false
enableXsrfProtection = true
maxUploadSize = 200

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#FF6B6B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"
```

### 4. .gitignore
```gitignore
# Secrets e configurações sensíveis
.streamlit/secrets.toml
.env
*.key
*.pem

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
env.bak/
venv.bak/

# IDEs
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/
```

## Processo de Deploy

### Passo 1: Preparar o Repositório
```bash
# Inicializar git (se não existir)
git init

# Adicionar arquivos
git add .

# Commit inicial
git commit -m "Initial commit: Streamlit app"

# Conectar ao GitHub
git remote add origin https://github.com/seu-usuario/seu-repositorio.git

# Push para GitHub
git push -u origin main
```

### Passo 2: Deploy no Streamlit Cloud

#### 2.1 Acessar Streamlit Cloud
1. Vá para [share.streamlit.io](https://share.streamlit.io)
2. Clique em "Sign in with GitHub"
3. Autorize o acesso ao GitHub

#### 2.2 Criar Nova Aplicação
1. Clique em "New app"
2. Preencha os campos:
   - **Repository**: `seu-usuario/seu-repositorio`
   - **Branch**: `main` (ou sua branch principal)
   - **Main file path**: `main.py`
   - **App URL**: `https://seu-app-name.streamlit.app`

#### 2.3 Configurações Avançadas
```toml
# Python version (se necessário)
python_version = "3.9"

# Resources
[resources]
cpu = "1"
memory = "1Gi"

# Timeout
[timeout]
default = 300
```

### Passo 3: Configurar Secrets
1. Vá para "Settings" da sua app
2. Clique em "Secrets"
3. Adicione as variáveis necessárias:

```toml
[secrets]
# APIs
OPENAI_API_KEY = "sk-..."
GOOGLE_API_KEY = "AIza..."

# Banco de dados
DATABASE_URL = "postgresql://user:pass@host:port/db"

# Autenticação
JWT_SECRET = "seu_jwt_secret"
```

## Configurações de Produção

### 1. Otimização de Performance
```python
import streamlit as st
import pandas as pd
from functools import lru_cache

# Cache para operações custosas
@st.cache_data
def load_data():
    """Carrega dados com cache"""
    return pd.read_csv("data.csv")

@st.cache_data
def expensive_computation(data):
    """Computação custosa com cache"""
    return data.groupby("category").sum()

# Usar cache
data = load_data()
result = expensive_computation(data)
```

### 2. Gerenciamento de Estado
```python
import streamlit as st

# Inicializar estado da sessão
if "counter" not in st.session_state:
    st.session_state.counter = 0

# Botões para controlar estado
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Incrementar"):
        st.session_state.counter += 1

with col2:
    if st.button("Decrementar"):
        st.session_state.counter -= 1

with col3:
    if st.button("Reset"):
        st.session_state.counter = 0

st.write(f"Contador: {st.session_state.counter}")
```

### 3. Tratamento de Erros
```python
import streamlit as st
import traceback

def safe_operation():
    """Operação com tratamento de erro"""
    try:
        # Sua operação aqui
        result = some_risky_operation()
        return result
    except Exception as e:
        st.error(f"Erro: {str(e)}")
        st.code(traceback.format_exc())
        return None

# Usar operação segura
result = safe_operation()
if result:
    st.success("Operação executada com sucesso!")
```

## Monitoramento e Manutenção

### 1. Logs e Debugging
```python
import streamlit as st
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Usar logging
logger.info("Aplicação iniciada")
logger.warning("Aviso: operação pode ser lenta")
logger.error("Erro crítico detectado")
```

### 2. Métricas de Uso
```python
import streamlit as st
import time

# Medir tempo de execução
start_time = time.time()

# Sua operação aqui
st.write("Processando dados...")

end_time = time.time()
execution_time = end_time - start_time

st.metric("Tempo de Execução", f"{execution_time:.2f}s")
```

### 3. Health Check
```python
import streamlit as st
import requests

def health_check():
    """Verifica saúde da aplicação"""
    checks = {
        "Streamlit": True,
        "APIs": False,
        "Database": False
    }
    
    # Verificar APIs
    try:
        response = requests.get("https://api.exemplo.com/health", timeout=5)
        checks["APIs"] = response.status_code == 200
    except:
        checks["APIs"] = False
    
    # Verificar banco de dados
    try:
        # Sua verificação de DB aqui
        checks["Database"] = True
    except:
        checks["Database"] = False
    
    return checks

# Exibir status
if st.button("Verificar Status"):
    status = health_check()
    
    for service, is_healthy in status.items():
        if is_healthy:
            st.success(f"✅ {service}: OK")
        else:
            st.error(f"❌ {service}: Erro")
```

## Troubleshooting

### Problemas Comuns

#### 1. App não carrega
- Verifique se o arquivo principal está correto
- Confirme se todas as dependências estão no requirements.txt
- Verifique os logs na interface do Streamlit Cloud

#### 2. Erro de dependências
```bash
# Testar localmente
pip install -r requirements.txt
streamlit run main.py
```

#### 3. Timeout da aplicação
- Otimize operações custosas
- Use cache adequadamente
- Considere aumentar o timeout nas configurações

#### 4. Secrets não funcionam
- Verifique a sintaxe do TOML
- Confirme se os secrets estão na interface web
- Reinicie a aplicação

### Debugging Avançado
```python
import streamlit as st
import sys
import os

# Informações do sistema
st.subheader("Informações do Sistema")
st.write(f"Python version: {sys.version}")
st.write(f"Streamlit version: {st.__version__}")
st.write(f"Working directory: {os.getcwd()}")

# Verificar variáveis de ambiente
st.subheader("Variáveis de Ambiente")
for key, value in os.environ.items():
    if "STREAMLIT" in key.upper():
        st.write(f"{key}: {value}")
```

## Atualizações e Versionamento

### 1. Deploy de Atualizações
```bash
# Fazer mudanças no código
git add .
git commit -m "feat: nova funcionalidade"
git push origin main

# O Streamlit Cloud detecta automaticamente as mudanças
```

### 2. Rollback
- Use tags do Git para marcar versões estáveis
- Mantenha branches para diferentes versões
- Use o histórico do GitHub para reverter mudanças

### 3. CI/CD Básico
```yaml
# .github/workflows/deploy.yml
name: Deploy to Streamlit Cloud

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Setup Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    - name: Install dependencies
      run: pip install -r requirements.txt
    - name: Test app
      run: streamlit run main.py --server.headless true
```

## Recursos Adicionais

### Links Úteis
- [Streamlit Cloud Documentation](https://docs.streamlit.io/streamlit-community-cloud)
- [Streamlit API Reference](https://docs.streamlit.io/library/api-reference)
- [GitHub Actions](https://docs.github.com/en/actions)

### Comunidade
- [Streamlit Forum](https://discuss.streamlit.io/)
- [GitHub Issues](https://github.com/streamlit/streamlit/issues)
- [Discord Community](https://discord.gg/streamlit)

### Exemplos
- [Streamlit Gallery](https://streamlit.io/gallery)
- [Awesome Streamlit](https://github.com/MarcSkovMadsen/awesome-streamlit)
- [Streamlit Examples](https://github.com/streamlit/streamlit-example-apps)
