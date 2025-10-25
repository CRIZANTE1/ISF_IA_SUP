# Configuração Supabase + Google AI

## Visão Geral
Este guia específico mostra como configurar e usar Supabase e Google AI em aplicações Streamlit Cloud.

## Configuração de Secrets

### 1. Arquivo secrets.toml
```toml
# ============================================
# SUPABASE
# ============================================
[supabase]  
url = "https://seu-projeto.supabase.co"
key = "sua-anon-key-aqui"
service_key = "sua-service-key-aqui"
connection_string = "postgresql://user:password@host:port/database"

# ============================================
# GOOGLE AI
# ============================================
[google_ai]
api_key = "sua-google-ai-key-aqui"

# ============================================
# GOOGLE OIDC (Autenticação)
# ============================================
[auth]
google_client_id = "seu-client-id.apps.googleusercontent.com"
google_client_secret = "GOCSPX-seu-secret"
google_redirect_uri = "http://localhost:8501"
secret = "sua-chave-secreta-aleatoria-muito-longa-e-segura-aqui"
```

### 2. Arquivo .env (Alternativo)
```env
# Supabase
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua-anon-key-aqui
SUPABASE_SERVICE_KEY=sua-service-key-aqui
SUPABASE_CONNECTION_STRING=postgresql://user:password@host:port/database

# Google AI
GOOGLE_API_KEY=sua-google-ai-key-aqui

# Google OIDC
GOOGLE_CLIENT_ID=seu-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-seu-secret
GOOGLE_REDIRECT_URI=http://localhost:8501
AUTH_SECRET=sua-chave-secreta-aleatoria-muito-longa-e-segura-aqui
```

## Uso no Código Python

### 1. Configuração do Supabase
```python
import streamlit as st
from supabase import create_client, Client
import os

def init_supabase():
    """Inicializa cliente Supabase"""
    try:
        # Usar secrets do Streamlit
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        
        supabase: Client = create_client(url, key)
        return supabase
    except Exception as e:
        st.error(f"Erro na configuração Supabase: {e}")
        return None

# Usar Supabase
supabase = init_supabase()
if supabase:
    st.success("✅ Supabase conectado!")
```

### 2. Configuração do Google AI
```python
import streamlit as st
import google.generativeai as genai

def init_google_ai():
    """Inicializa Google AI"""
    try:
        api_key = st.secrets["google_ai"]["api_key"]
        genai.configure(api_key=api_key)
        return True
    except Exception as e:
        st.error(f"Erro na configuração Google AI: {e}")
        return False

# Usar Google AI
if init_google_ai():
    st.success("✅ Google AI configurado!")
    
    # Exemplo de uso
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content("Olá, como você está?")
    st.write(response.text)
```

### 3. Autenticação Google OIDC
```python
import streamlit as st
import requests
from urllib.parse import urlencode

def get_google_auth_url():
    """Gera URL de autenticação Google"""
    client_id = st.secrets["auth"]["google_client_id"]
    redirect_uri = st.secrets["auth"]["google_redirect_uri"]
    
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'openid email profile',
        'access_type': 'offline'
    }
    
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    return auth_url

def exchange_code_for_token(code):
    """Troca código de autorização por token"""
    client_id = st.secrets["auth"]["google_client_id"]
    client_secret = st.secrets["auth"]["google_client_secret"]
    redirect_uri = st.secrets["auth"]["google_redirect_uri"]
    
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': redirect_uri
    }
    
    response = requests.post(token_url, data=data)
    return response.json()

# Interface de autenticação
if "user" not in st.session_state:
    st.write("Faça login com Google:")
    auth_url = get_google_auth_url()
    st.link_button("Login com Google", auth_url)
else:
    st.write(f"Bem-vindo, {st.session_state.user['name']}!")
```

## Exemplos Práticos

### 1. App com Supabase + Google AI
```python
import streamlit as st
from supabase import create_client, Client
import google.generativeai as genai

# Configuração
st.set_page_config(page_title="App Supabase + Google AI", layout="wide")

# Inicializar serviços
@st.cache_resource
def init_services():
    # Supabase
    supabase = create_client(
        st.secrets["supabase"]["url"],
        st.secrets["supabase"]["key"]
    )
    
    # Google AI
    genai.configure(api_key=st.secrets["google_ai"]["api_key"])
    
    return supabase, genai

supabase, genai = init_services()

# Interface
st.title("🚀 App Supabase + Google AI")

# Seção de dados do Supabase
st.header("📊 Dados do Supabase")
try:
    # Buscar dados
    data = supabase.table("users").select("*").limit(10).execute()
    st.dataframe(data.data)
except Exception as e:
    st.error(f"Erro ao buscar dados: {e}")

# Seção de Google AI
st.header("🤖 Google AI")
prompt = st.text_area("Digite sua pergunta:")
if st.button("Gerar Resposta"):
    if prompt:
        try:
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt)
            st.write("**Resposta:**")
            st.write(response.text)
        except Exception as e:
            st.error(f"Erro na geração: {e}")
```

### 2. Sistema de Autenticação Completo
```python
import streamlit as st
import requests
from urllib.parse import urlencode, parse_qs
import jwt
from datetime import datetime, timedelta

def create_jwt_token(user_data):
    """Cria JWT token para sessão"""
    secret = st.secrets["auth"]["secret"]
    payload = {
        'user_id': user_data['id'],
        'email': user_data['email'],
        'name': user_data['name'],
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, secret, algorithm='HS256')

def verify_jwt_token(token):
    """Verifica JWT token"""
    try:
        secret = st.secrets["auth"]["secret"]
        payload = jwt.decode(token, secret, algorithms=['HS256'])
        return payload
    except:
        return None

def handle_google_callback():
    """Processa callback do Google OAuth"""
    query_params = st.query_params
    
    if 'code' in query_params:
        code = query_params['code']
        
        # Trocar código por token
        token_data = exchange_code_for_token(code)
        
        if 'access_token' in token_data:
            # Buscar informações do usuário
            user_info = get_user_info(token_data['access_token'])
            
            # Criar JWT para sessão
            jwt_token = create_jwt_token(user_info)
            
            # Salvar na sessão
            st.session_state['jwt_token'] = jwt_token
            st.session_state['user'] = user_info
            
            # Redirecionar
            st.rerun()

def get_user_info(access_token):
    """Busca informações do usuário no Google"""
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get('https://www.googleapis.com/oauth2/v2/userinfo', headers=headers)
    return response.json()

# Verificar autenticação
if 'jwt_token' in st.session_state:
    user_data = verify_jwt_token(st.session_state['jwt_token'])
    if user_data:
        st.write(f"Bem-vindo, {user_data['name']}!")
        if st.button("Logout"):
            for key in ['jwt_token', 'user']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    else:
        st.error("Sessão inválida. Faça login novamente.")
else:
    st.write("Faça login para continuar:")
    auth_url = get_google_auth_url()
    st.link_button("Login com Google", auth_url)
    
    # Processar callback
    handle_google_callback()
```

## Configuração no Streamlit Cloud

### 1. Secrets no Streamlit Cloud
1. Vá para sua aplicação no Streamlit Cloud
2. Clique em "Settings" → "Secrets"
3. Adicione a configuração TOML:

```toml
[supabase]  
url = "https://seu-projeto.supabase.co"
key = "sua-anon-key-aqui"
service_key = "sua-service-key-aqui"
connection_string = "postgresql://user:password@host:port/database"

[google_ai]
api_key = "sua-google-ai-key-aqui"

[auth]
google_client_id = "seu-client-id.apps.googleusercontent.com"
google_client_secret = "GOCSPX-seu-secret"
google_redirect_uri = "https://sua-app.streamlit.app"
secret = "sua-chave-secreta-aleatoria-muito-longa-e-segura-aqui"
```

### 2. Configuração do Google OAuth
1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um projeto ou selecione existente
3. Ative a API "Google+ API"
4. Vá para "Credenciais" → "Criar credenciais" → "ID do cliente OAuth 2.0"
5. Configure:
   - **Tipo de aplicação**: Aplicação da Web
   - **URIs de redirecionamento autorizados**: 
     - `http://localhost:8501` (desenvolvimento)
     - `https://sua-app.streamlit.app` (produção)

## Troubleshooting

### Problemas Comuns

#### 1. Erro de CORS no Supabase
```python
# Configurar CORS no Supabase
# Vá para Settings → API → CORS
# Adicione: http://localhost:8501, https://sua-app.streamlit.app
```

#### 2. Google AI não funciona
```python
# Verificar se a API está habilitada
# Acesse: https://console.cloud.google.com/apis/library
# Procure por "Generative AI API" e habilite
```

#### 3. Autenticação Google falha
```python
# Verificar configurações:
# 1. Client ID correto
# 2. Redirect URI correto
# 3. API habilitada
# 4. Domínio autorizado
```

## Recursos Adicionais

### Links Úteis
- [Supabase Documentation](https://supabase.com/docs)
- [Google AI Documentation](https://ai.google.dev/docs)
- [Google OAuth 2.0](https://developers.google.com/identity/protocols/oauth2)

### Exemplos de Código
- [Supabase Python Client](https://github.com/supabase/supabase-py)
- [Google AI Python SDK](https://github.com/google/generative-ai-python)
- [Streamlit Authentication](https://github.com/streamlit/streamlit-authenticator)
