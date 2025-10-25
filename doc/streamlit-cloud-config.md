# Configuração do Streamlit Cloud

## Visão Geral
Este documento descreve como configurar e fazer deploy de aplicações Streamlit no Streamlit Cloud.

## Pré-requisitos
- Conta no GitHub
- Repositório público no GitHub
- Aplicação Streamlit funcional localmente

## Configuração Básica

### 1. Estrutura do Projeto
```
projeto/
├── main.py                 # Arquivo principal da aplicação
├── requirements.txt        # Dependências Python
├── .streamlit/
│   └── config.toml        # Configurações do Streamlit
└── README.md              # Documentação do projeto
```

### 2. Arquivo de Configuração (.streamlit/config.toml)
```toml
[server]
port = 8501
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#FF6B6B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
```

### 3. Requirements.txt
```
streamlit>=1.28.0
pandas>=1.5.0
numpy>=1.24.0
plotly>=5.15.0
```

## Deploy no Streamlit Cloud

### Passo 1: Preparar o Repositório
1. Certifique-se de que todos os arquivos estão commitados
2. Faça push para o GitHub
3. Verifique se o repositório é público

### Passo 2: Conectar ao Streamlit Cloud
1. Acesse [share.streamlit.io](https://share.streamlit.io)
2. Faça login com sua conta GitHub
3. Clique em "New app"
4. Selecione o repositório e branch
5. Especifique o arquivo principal (ex: `main.py`)

### Passo 3: Configurações Avançadas
- **Python Version**: Especifique a versão do Python se necessário
- **Secrets**: Configure variáveis de ambiente sensíveis
- **Advanced Settings**: Configurações de recursos e timeout

## Configurações de Secrets

### Secrets Management
```python
import streamlit as st
import os

# Acessar secrets
api_key = st.secrets["api_key"]
database_url = st.secrets["database_url"]
```

### Configuração no Streamlit Cloud
1. Vá para "Settings" da sua app
2. Clique em "Secrets"
3. Adicione as variáveis necessárias:
```toml
[secrets]
api_key = "sua_chave_api"
database_url = "sua_url_banco"
```

## Monitoramento e Logs

### Visualização de Logs
- Acesse o dashboard da sua app
- Clique em "Logs" para ver os logs em tempo real
- Use "Advanced settings" para configurar níveis de log

### Métricas de Performance
- Uptime da aplicação
- Tempo de resposta
- Uso de recursos

## Troubleshooting

### Problemas Comuns
1. **App não carrega**: Verifique se o arquivo principal está correto
2. **Erro de dependências**: Verifique o requirements.txt
3. **Timeout**: Ajuste as configurações de timeout
4. **Secrets não funcionam**: Verifique a sintaxe do secrets.toml

### Logs de Debug
```python
import streamlit as st
import logging

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Usar em sua aplicação
logger.info("Aplicação iniciada")
```

## Boas Práticas

### Performance
- Use cache para operações custosas
- Otimize imports
- Evite recarregar dados desnecessariamente

### Segurança
- Nunca commite secrets no código
- Use variáveis de ambiente
- Valide inputs do usuário

### Manutenção
- Mantenha dependências atualizadas
- Documente mudanças importantes
- Use versionamento adequado

## Recursos Adicionais
- [Documentação Oficial Streamlit](https://docs.streamlit.io/)
- [Streamlit Cloud Documentation](https://docs.streamlit.io/streamlit-community-cloud)
- [Exemplos de Apps](https://streamlit.io/gallery)
