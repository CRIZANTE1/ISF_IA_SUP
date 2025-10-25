# Configuração de Secrets no Streamlit Cloud

## Visão Geral
Este guia explica como configurar e gerenciar secrets (variáveis sensíveis) no Streamlit Cloud de forma segura.

## O que são Secrets?
Secrets são variáveis de ambiente que contêm informações sensíveis como:
- Chaves de API
- URLs de banco de dados
- Senhas
- Tokens de autenticação
- Configurações privadas

## Configuração de Secrets

### 1. Método via Interface Web (Recomendado)

#### Passo 1: Acessar Configurações
1. Vá para sua aplicação no Streamlit Cloud
2. Clique em "Settings" (Configurações)
3. Selecione a aba "Secrets"

#### Passo 2: Adicionar Secrets
```toml
[secrets]
# Chaves de API
OPENAI_API_KEY = "sk-..."
GOOGLE_API_KEY = "AIza..."

# URLs de Banco de Dados
DATABASE_URL = "postgresql://user:pass@host:port/db"
REDIS_URL = "redis://localhost:6379"

# Configurações de Autenticação
JWT_SECRET = "seu_jwt_secret"
ENCRYPTION_KEY = "sua_chave_criptografia"

# Configurações de Serviços Externos
SUPABASE_URL = "https://xxx.supabase.co"
SUPABASE_KEY = "eyJ..."
```

### 2. Método via Arquivo secrets.toml

#### Estrutura do Arquivo
```
projeto/
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml        # Arquivo de secrets (NÃO commitar)
├── main.py
└── requirements.txt
```

#### Exemplo de secrets.toml
```toml
# Configurações de API
[api]
openai_key = "sk-..."
google_key = "AIza..."
anthropic_key = "sk-ant-..."

# Configurações de Banco de Dados
[database]
url = "postgresql://user:pass@host:port/db"
username = "db_user"
password = "db_password"

# Configurações de Autenticação
[auth]
jwt_secret = "seu_jwt_secret_aqui"
session_timeout = 3600

# Configurações de Serviços
[services]
supabase_url = "https://xxx.supabase.co"
supabase_key = "eyJ..."
redis_url = "redis://localhost:6379"
```

## Uso de Secrets no Código

### 1. Acesso Básico
```python
import streamlit as st

# Acessar secrets individuais
api_key = st.secrets["OPENAI_API_KEY"]
database_url = st.secrets["DATABASE_URL"]
```

### 2. Acesso com Seções
```python
import streamlit as st

# Acessar secrets organizados em seções
openai_key = st.secrets["api"]["openai_key"]
db_url = st.secrets["database"]["url"]
jwt_secret = st.secrets["auth"]["jwt_secret"]
```

### 3. Verificação de Existência
```python
import streamlit as st

# Verificar se secret existe
if "OPENAI_API_KEY" in st.secrets:
    api_key = st.secrets["OPENAI_API_KEY"]
    st.success("API Key configurada!")
else:
    st.error("API Key não encontrada!")
    st.stop()
```

### 4. Validação de Secrets
```python
import streamlit as st
import os

def validate_secrets():
    """Valida se todos os secrets necessários estão configurados"""
    required_secrets = [
        "OPENAI_API_KEY",
        "DATABASE_URL",
        "JWT_SECRET"
    ]
    
    missing_secrets = []
    for secret in required_secrets:
        if secret not in st.secrets:
            missing_secrets.append(secret)
    
    if missing_secrets:
        st.error(f"Secrets faltando: {', '.join(missing_secrets)}")
        st.stop()
    
    return True

# Usar a validação
if validate_secrets():
    st.success("Todos os secrets estão configurados!")
```

## Exemplos Práticos

### 1. Configuração de OpenAI
```python
import streamlit as st
import openai

# Configurar OpenAI
openai.api_key = st.secrets["OPENAI_API_KEY"]

def generate_response(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Erro na API: {e}")
        return None
```

### 2. Conexão com Banco de Dados
```python
import streamlit as st
import psycopg2
import pandas as pd

def get_database_connection():
    """Cria conexão com o banco de dados"""
    try:
        conn = psycopg2.connect(st.secrets["DATABASE_URL"])
        return conn
    except Exception as e:
        st.error(f"Erro na conexão: {e}")
        return None

def query_data(query):
    """Executa query no banco"""
    conn = get_database_connection()
    if conn:
        try:
            df = pd.read_sql(query, conn)
            conn.close()
            return df
        except Exception as e:
            st.error(f"Erro na query: {e}")
            return None
```

### 3. Configuração de Supabase
```python
import streamlit as st
from supabase import create_client, Client

def init_supabase():
    """Inicializa cliente Supabase"""
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        supabase: Client = create_client(url, key)
        return supabase
    except Exception as e:
        st.error(f"Erro na configuração Supabase: {e}")
        return None

# Usar Supabase
supabase = init_supabase()
if supabase:
    # Fazer queries
    data = supabase.table("users").select("*").execute()
```

## Segurança e Boas Práticas

### 1. Nunca Commitar Secrets
```gitignore
# Adicionar ao .gitignore
.streamlit/secrets.toml
.env
*.key
```

### 2. Rotação de Secrets
- Mude secrets regularmente
- Use diferentes secrets para ambientes
- Monitore uso de secrets

### 3. Validação de Entrada
```python
import streamlit as st
import re

def validate_api_key(api_key):
    """Valida formato da API key"""
    if not api_key:
        return False
    
    # Exemplo de validação para OpenAI
    if api_key.startswith("sk-") and len(api_key) > 20:
        return True
    
    return False

# Usar validação
api_key = st.secrets.get("OPENAI_API_KEY")
if not validate_api_key(api_key):
    st.error("API Key inválida!")
    st.stop()
```

### 4. Logging Seguro
```python
import streamlit as st
import logging

# Configurar logging sem expor secrets
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def log_operation(operation, success=True):
    """Log operações sem expor dados sensíveis"""
    if success:
        logging.info(f"Operação {operation} executada com sucesso")
    else:
        logging.error(f"Falha na operação {operation}")
```

## Troubleshooting

### Problemas Comuns

#### 1. Secret não encontrado
```python
# Verificar se secret existe
if "MY_SECRET" in st.secrets:
    value = st.secrets["MY_SECRET"]
else:
    st.error("Secret MY_SECRET não configurado")
```

#### 2. Formato incorreto
```python
# Verificar tipo do secret
secret_value = st.secrets.get("DATABASE_URL")
if isinstance(secret_value, str):
    # Usar como string
    pass
else:
    st.error("DATABASE_URL deve ser uma string")
```

#### 3. Secrets não carregam
- Verifique a sintaxe do TOML
- Confirme se os secrets estão na interface web
- Reinicie a aplicação

## Recursos Adicionais
- [Documentação de Secrets do Streamlit](https://docs.streamlit.io/streamlit-community-cloud/get-started/deploy-an-app/connect-to-data-sources/secrets-management)
- [Formato TOML](https://toml.io/)
- [Boas Práticas de Segurança](https://docs.streamlit.io/streamlit-community-cloud/get-started/deploy-an-app/connect-to-data-sources/secrets-management#secrets-management-best-practices)
