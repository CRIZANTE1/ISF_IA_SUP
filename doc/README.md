# Documentação - Streamlit Cloud

## Visão Geral
Esta pasta contém toda a documentação necessária para configurar, fazer deploy e manter aplicações Streamlit no Streamlit Cloud.

## Estrutura da Documentação

### 📁 Arquivos Disponíveis

| Arquivo | Descrição |
|---------|-----------|
| `streamlit-cloud-config.md` | Configuração básica do Streamlit Cloud |
| `secrets-configuration.md` | Guia completo de configuração de secrets |
| `deployment-guide.md` | Guia passo-a-passo para deploy |
| `requirements-dependencies.md` | Gerenciamento de dependências Python |
| `supabase-google-ai-config.md` | Configuração específica Supabase + Google AI |
| `README.md` | Este arquivo - índice da documentação |

## 🚀 Início Rápido

### 1. Configuração Inicial
- Leia [streamlit-cloud-config.md](streamlit-cloud-config.md) para configuração básica
- Configure secrets seguindo [secrets-configuration.md](secrets-configuration.md)
- Para Supabase + Google AI, use [supabase-google-ai-config.md](supabase-google-ai-config.md)

### 2. Deploy da Aplicação
- Siga o [deployment-guide.md](deployment-guide.md) para fazer deploy
- Configure dependências conforme [requirements-dependencies.md](requirements-dependencies.md)

### 3. Manutenção
- Monitore logs e performance
- Atualize dependências regularmente
- Mantenha secrets seguros

## 📋 Checklist de Deploy

### Pré-requisitos
- [ ] Conta GitHub ativa
- [ ] Repositório público no GitHub
- [ ] Aplicação Streamlit funcional localmente
- [ ] Arquivo `requirements.txt` configurado
- [ ] Secrets configurados (se necessário)

### Configuração
- [ ] Arquivo principal (`main.py`) funcionando
- [ ] Dependências testadas localmente
- [ ] Configurações do Streamlit (`.streamlit/config.toml`)
- [ ] Secrets configurados no Streamlit Cloud

### Deploy
- [ ] Repositório commitado e enviado para GitHub
- [ ] App criada no Streamlit Cloud
- [ ] URL da aplicação funcionando
- [ ] Testes básicos realizados

## 🔧 Configurações Comuns

### Estrutura Mínima do Projeto
```
projeto/
├── main.py                 # Arquivo principal
├── requirements.txt        # Dependências
├── .streamlit/
│   └── config.toml        # Configurações
├── .gitignore             # Ignorar arquivos sensíveis
└── README.md              # Documentação
```

### Requirements.txt Básico
```txt
streamlit>=1.28.0
pandas>=1.5.0
numpy>=1.24.0
```

### Configuração Básica (.streamlit/config.toml)
```toml
[server]
port = 8501
enableCORS = false

[theme]
primaryColor = "#FF6B6B"
backgroundColor = "#FFFFFF"
```

## 🛠️ Troubleshooting

### Problemas Comuns

#### App não carrega
1. Verifique se o arquivo principal está correto
2. Confirme se todas as dependências estão no `requirements.txt`
3. Verifique os logs na interface do Streamlit Cloud

#### Erro de dependências
1. Teste localmente: `pip install -r requirements.txt`
2. Verifique compatibilidade de versões
3. Use versões específicas se necessário

#### Secrets não funcionam
1. Verifique a sintaxe do TOML
2. Confirme se os secrets estão na interface web
3. Reinicie a aplicação

#### Timeout da aplicação
1. Otimize operações custosas
2. Use cache adequadamente
3. Considere aumentar o timeout nas configurações

## 📚 Recursos Adicionais

### Documentação Oficial
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Streamlit Cloud Documentation](https://docs.streamlit.io/streamlit-community-cloud)
- [Streamlit API Reference](https://docs.streamlit.io/library/api-reference)

### Comunidade
- [Streamlit Forum](https://discuss.streamlit.io/)
- [GitHub Issues](https://github.com/streamlit/streamlit/issues)
- [Discord Community](https://discord.gg/streamlit)

### Exemplos e Tutoriais
- [Streamlit Gallery](https://streamlit.io/gallery)
- [Awesome Streamlit](https://github.com/MarcSkovMadsen/awesome-streamlit)
- [Streamlit Examples](https://github.com/streamlit/streamlit-example-apps)

## 🔒 Segurança

### Boas Práticas
- Nunca commite secrets no código
- Use variáveis de ambiente para dados sensíveis
- Mantenha dependências atualizadas
- Valide inputs do usuário

### Configuração de Secrets
```toml
[secrets]
# Nunca commitar este arquivo
API_KEY = "sua_chave_aqui"
DATABASE_URL = "sua_url_aqui"
```

## 📈 Performance

### Otimizações
- Use `@st.cache_data` para operações custosas
- Otimize imports
- Evite recarregar dados desnecessariamente
- Use paginação para grandes datasets

### Monitoramento
- Acompanhe logs da aplicação
- Monitore tempo de resposta
- Verifique uso de recursos

## 🆘 Suporte

### Como Obter Ajuda
1. Consulte esta documentação
2. Verifique a documentação oficial
3. Procure na comunidade Streamlit
4. Abra uma issue no GitHub se necessário

### Informações para Suporte
- Versão do Streamlit
- Versão do Python
- Logs de erro
- Configurações relevantes

---

**Última atualização**: $(date)
**Versão da documentação**: 1.0.0
