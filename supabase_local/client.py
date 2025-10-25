# supabase/client.py (VERSÃO COM INTEGER)

import streamlit as st
from supabase import create_client, Client
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class SupabaseClient:
    """Cliente Supabase com isolamento automático de dados por user_id (multi-tenant)."""
    
    def __init__(self):
        self.client: Client = self._initialize_client()
        # Obtém o user_id do usuário logado (INTEGER)
        self.user_id = self._get_current_user_id()

    def _initialize_client(self) -> Client:
        """Inicializa a conexão com o Supabase."""
        try:
            # Verifica se as credenciais existem
            if "supabase" not in st.secrets:
                raise ValueError("Seção [supabase] não encontrada em secrets.toml")
            
            url = st.secrets["supabase"].get("url")
            key = st.secrets["supabase"].get("key")
            
            if not url or not key:
                raise ValueError("Credenciais do Supabase não encontradas em secrets.toml")
            
            # Valida formato da URL
            if not url.startswith("https://"):
                raise ValueError("URL do Supabase deve começar com https://")
            
            # Cria cliente com timeout
            import requests
            import time
            
            start_time = time.time()
            client = create_client(url, key)
            
            # Testa conexão básica
            try:
                # Teste simples de conectividade
                test_response = client.table("usuarios").select("id").limit(1).execute()
                logger.info("✅ Conexão com Supabase testada com sucesso")
            except Exception as test_error:
                logger.warning(f"⚠️ Aviso: Teste de conexão falhou: {test_error}")
                # Não falha aqui, apenas avisa
            
            elapsed_time = time.time() - start_time
            logger.info(f"✅ Cliente Supabase inicializado em {elapsed_time:.2f}s")
            return client
            
        except KeyError as e:
            error_msg = f"Configuração do Supabase ausente: {e}"
            logger.error(error_msg)
            st.error(error_msg)
            raise
        except Exception as e:
            error_msg = f"Erro ao inicializar cliente Supabase: {e}"
            logger.error(error_msg)
            st.error(error_msg)
            raise

    def _get_current_user_id(self) -> int:
        """Obtém o user_id (INTEGER) do usuário logado da sessão."""
        try:
            # Evita dependência circular - obtém user_id diretamente da sessão
            user_id = st.session_state.get('current_user_id')
            if user_id:
                return int(user_id)
            
            # Fallback: tenta obter via consulta direta ao Supabase
            # para evitar dependência circular com auth_utils
            try:
                user_email = st.session_state.get('user_email')
                if user_email:
                    # Consulta direta ao Supabase para obter user_id
                    response = self.client.table("usuarios").select("id").eq("email", user_email).execute()
                    if response.data:
                        return int(response.data[0]['id'])
            except Exception as fallback_error:
                logger.warning(f"Fallback para obter user_id falhou: {fallback_error}")
            
            return None
        except Exception as e:
            logger.warning(f"Não foi possível obter user_id: {e}")
            return None

    def get_data(self, table_name: str, filters: dict = None) -> pd.DataFrame:
        """
        Busca dados de uma tabela com ISOLAMENTO AUTOMÁTICO por user_id.
        
        Args:
            table_name: Nome da tabela no Supabase
            filters: Filtros adicionais opcionais (dict)
            
        Returns:
            DataFrame com os dados filtrados
        """
        try:
            # Tabelas GLOBAIS que NÃO devem ser filtradas por usuário
            GLOBAL_TABLES = {
                "usuarios", 
                "log_auditoria", 
                "solicitacoes_acesso", 
                "notificacoes_pendentes", 
                "solicitacoes_suporte"
            }
            
            query = self.client.table(table_name).select("*")
            
            # 🔒 APLICA FILTRO DE SEGURANÇA (multi-tenant) usando user_id
            if table_name not in GLOBAL_TABLES:
                if not self.user_id:
                    logger.warning(f"Usuário não identificado. Não é possível acessar '{table_name}'.")
                    st.warning(f"⚠️ Usuário não identificado para acessar '{table_name}'.")
                    return pd.DataFrame()
                
                query = query.eq('user_id', self.user_id)
                logger.info(f"🔒 Filtro de segurança aplicado: user_id={self.user_id}")
            
            # Aplica filtros adicionais se fornecidos
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            response = query.execute()
            
            if response.data:
                logger.info(f"✅ {len(response.data)} registros lidos de '{table_name}'")
                return pd.DataFrame(response.data)
            
            logger.info(f"ℹ️ Nenhum registro encontrado em '{table_name}'")
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"❌ Erro ao ler '{table_name}': {e}")
            st.error(f"Erro ao carregar dados de '{table_name}': {e}")
            return pd.DataFrame()

    def append_data(self, table_name: str, data: dict or list[dict]):
        """
        Adiciona registros com INJEÇÃO AUTOMÁTICA do user_id.
        
        Args:
            table_name: Nome da tabela
            data: Dicionário ou lista de dicionários para inserir
            
        Returns:
            Resposta do Supabase
        """
        if not data:
            logger.warning("Tentativa de inserir dados vazios.")
            return None
        
        try:
            GLOBAL_TABLES = {
                "usuarios", 
                "log_auditoria", 
                "solicitacoes_acesso", 
                "notificacoes_pendentes", 
                "solicitacoes_suporte"
            }
            
            # 🔒 INJETA user_id automaticamente
            if table_name not in GLOBAL_TABLES:
                if not self.user_id:
                    raise ValueError("❌ Usuário não identificado. Impossível salvar dados.")
                
                if isinstance(data, list):
                    for record in data:
                        record['user_id'] = self.user_id
                else:
                    data['user_id'] = self.user_id
                
                logger.info(f"🔒 user_id {self.user_id} injetado nos registros")
            
            response = self.client.table(table_name).insert(data).execute()
            
            count = len(data) if isinstance(data, list) else 1
            logger.info(f"✅ {count} registro(s) inserido(s) em '{table_name}'")
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Erro ao inserir em '{table_name}': {e}")
            st.error(f"Erro ao salvar dados em '{table_name}': {e}")
            raise

    def update_data(self, table_name: str, data: dict, filter_column: str, filter_value):
        """Atualiza registros na tabela com segurança multi-tenant."""
        try:
            GLOBAL_TABLES = {
                "usuarios", "log_auditoria", "solicitacoes_acesso", 
                "notificacoes_pendentes", "solicitacoes_suporte"
            }
            
            query = self.client.table(table_name).update(data)
            
            if table_name not in GLOBAL_TABLES:
                if not self.user_id:
                    raise ValueError("❌ Usuário não identificado.")
                query = query.eq('user_id', self.user_id)
            
            response = query.eq(filter_column, filter_value).execute()
            logger.info(f"✅ Registro atualizado em '{table_name}'")
            return response
            
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar '{table_name}': {e}")
            st.error(f"Erro ao atualizar dados em '{table_name}': {e}")
            raise

    def delete_data(self, table_name: str, filter_column: str, filter_value):
        """Remove registros da tabela com segurança multi-tenant."""
        try:
            GLOBAL_TABLES = {
                "usuarios", "log_auditoria", "solicitacoes_acesso", 
                "notificacoes_pendentes", "solicitacoes_suporte"
            }
            
            query = self.client.table(table_name).delete()
            
            if table_name not in GLOBAL_TABLES:
                if not self.user_id:
                    raise ValueError("❌ Usuário não identificado.")
                query = query.eq('user_id', self.user_id)
            
            response = query.eq(filter_column, filter_value).execute()
            logger.info(f"✅ Registro deletado de '{table_name}'")
            return response
            
        except Exception as e:
            logger.error(f"❌ Erro ao deletar de '{table_name}': {e}")
            st.error(f"Erro ao deletar dados de '{table_name}': {e}")
            raise


@st.cache_resource
def get_supabase_client() -> SupabaseClient:
    """Retorna instância única (singleton) do cliente Supabase."""
    try:
        logger.info("🔄 Inicializando cliente Supabase...")
        client = SupabaseClient()
        logger.info("✅ Cliente Supabase criado com sucesso")
        return client
    except Exception as e:
        logger.error(f"❌ Falha crítica ao criar cliente Supabase: {e}")
        st.error(f"Erro crítico de conexão: {e}")
        # Retorna um cliente "dummy" para evitar travamento total
        return None


def get_supabase_client_no_cache() -> SupabaseClient:
    """Versão sem cache para casos de emergência."""
    try:
        logger.info("🔄 Inicializando cliente Supabase (sem cache)...")
        client = SupabaseClient()
        logger.info("✅ Cliente Supabase criado com sucesso (sem cache)")
        return client
    except Exception as e:
        logger.error(f"❌ Falha crítica ao criar cliente Supabase (sem cache): {e}")
        st.error(f"Erro crítico de conexão: {e}")
        return None
