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
                error_msg = """
                ❌ **Configuração do Supabase não encontrada!**
                
                Para usar este aplicativo, você precisa configurar as credenciais do Supabase no Streamlit Cloud:
                
                1. Acesse as configurações do seu app no Streamlit Cloud
                2. Vá em "Settings" > "Secrets"
                3. Adicione as seguintes configurações:
                
                ```toml
                [supabase]
                url = "https://seu-projeto.supabase.co"
                key = "sua-anon-key"
                ```
                
                **Para obter essas credenciais:**
                - Acesse seu projeto no Supabase
                - Vá em Settings > API
                - Copie a URL do projeto e a anon key
                """
                st.error(error_msg)
                st.stop()
                raise ValueError("Configuração do Supabase ausente")
            
            url = st.secrets["supabase"].get("url")
            key = st.secrets["supabase"].get("key")
            
            if not url or not key:
                error_msg = """
                ❌ **Credenciais do Supabase incompletas!**
                
                Verifique se você configurou corretamente no Streamlit Cloud:
                
                ```toml
                [supabase]
                url = "https://seu-projeto.supabase.co"
                key = "sua-anon-key"
                ```
                """
                st.error(error_msg)
                st.stop()
                raise ValueError("Credenciais do Supabase incompletas")
            
            # Valida formato da URL
            if not url.startswith("https://"):
                st.error("❌ URL do Supabase deve começar com https://")
                st.stop()
                raise ValueError("URL do Supabase inválida")
            
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
            st.stop()
            raise
        except Exception as e:
            error_msg = f"Erro ao inicializar cliente Supabase: {e}"
            logger.error(error_msg)
            st.error(error_msg)
            st.stop()
            raise

    def _is_superuser(self) -> bool:
        """Verifica se o usuário atual é superuser."""
        try:
            from auth.auth_utils import is_superuser
            return is_superuser()
        except Exception:
            return False

    def _get_user_email_directly(self) -> str | None:
        """Obtém o email do usuário diretamente do Streamlit, sem dependências circulares."""
        try:
            if hasattr(st.user, 'email') and st.user.email:
                email = st.user.email
                if isinstance(email, str):
                    return email.lower().strip()
            return None
        except Exception:
            return None

    def _get_users_data_directly(self) -> pd.DataFrame:
        """Obtém dados de usuários diretamente do Supabase, sem cache do Streamlit."""
        try:
            # Busca diretamente na tabela usuarios sem usar auth_utils
            users_data = self.get_data("usuarios")
            if users_data is not None and not users_data.empty:
                # Converte colunas de data que vêm como string do Supabase
                if 'data_cadastro' in users_data.columns:
                    users_data['data_cadastro'] = pd.to_datetime(
                        users_data['data_cadastro'], errors='coerce').dt.date
                if 'trial_end_date' in users_data.columns:
                    users_data['trial_end_date'] = pd.to_datetime(
                        users_data['trial_end_date'], errors='coerce').dt.date
                return users_data
            return pd.DataFrame()
        except Exception as e:
            logger.warning(f"Erro ao obter dados de usuários diretamente: {e}")
            return pd.DataFrame()

    def _get_current_user_id(self) -> int | None:
        """Obtém o user_id (INTEGER) do usuário logado da sessão."""
        try:
            # Evita dependência circular - obtém user_id diretamente da sessão
            user_id = st.session_state.get('current_user_id')
            if user_id:
                try:
                    return int(user_id)
                except (ValueError, TypeError):
                    logger.warning(f"user_id na sessão não é um número válido: {user_id}")
            
            # QUEBRA A DEPENDÊNCIA CIRCULAR: obtém user_id diretamente do Supabase
            # sem passar por auth_utils que chama get_supabase_client novamente
            try:
                user_email = self._get_user_email_directly()
                if user_email:
                    # Busca diretamente na tabela usuarios sem usar auth_utils
                    users_data = self._get_users_data_directly()
                    if not users_data.empty:
                        user_entry = users_data[users_data['email'] == user_email]
                        if not user_entry.empty:
                            user_id = user_entry.iloc[0].get('id')
                            if user_id:
                                try:
                                    user_id = int(user_id)
                                    # Armazena na sessão para próximas consultas
                                    st.session_state['current_user_id'] = user_id
                                    logger.info(f"✅ User ID obtido diretamente: {user_id}")
                                    return user_id
                                except (ValueError, TypeError):
                                    logger.warning(f"ID do usuário não é um número válido: {user_id}")
            except Exception as direct_error:
                logger.warning(f"Erro ao obter user_id diretamente: {direct_error}")
            
            # Se não conseguiu obter user_id, retorna None (não falha)
            logger.info("ℹ️ user_id não disponível - operações serão limitadas")
            return None
        except Exception as e:
            logger.warning(f"Não foi possível obter user_id: {e}")
            return None

    def get_data(self, table_name: str, filters: dict | None = None) -> pd.DataFrame:
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
            if table_name in GLOBAL_TABLES:
                # Tabelas globais - apenas superuser pode acessar
                if not self._is_superuser():
                    logger.warning(f"❌ Acesso negado: apenas superuser pode acessar tabela global '{table_name}'")
                    return pd.DataFrame()
                else:
                    logger.info(f"👑 Superuser acessando tabela global '{table_name}'")
            else:
                # Tabelas normais - filtro por user_id
                if not self.user_id:
                    logger.warning(f"Usuário não identificado. Retornando dados vazios para '{table_name}'.")
                    # Não mostra warning para o usuário, apenas retorna dados vazios
                    return pd.DataFrame()
                
                # Verifica se é superuser - se for, não aplica filtro
                if self._is_superuser():
                    logger.info(f"👑 Superuser acessando todos os dados de '{table_name}'")
                else:
                    query = query.eq('user_id', self.user_id)
                    logger.info(f"🔒 Filtro de segurança aplicado: user_id={self.user_id}")
            
            # Aplica filtros adicionais se fornecidos
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            response = query.execute()
            
            # Verifica se a resposta tem dados
            try:
                if hasattr(response, 'data'):
                    data = getattr(response, 'data', None)
                    if data:
                        logger.info(f"✅ {len(data)} registros lidos de '{table_name}'")
                        return pd.DataFrame(data)
                    else:
                        logger.info(f"ℹ️ Nenhum registro encontrado em '{table_name}'")
                        return pd.DataFrame()
                else:
                    logger.warning(f"⚠️ Resposta inesperada do Supabase para '{table_name}'")
                    return pd.DataFrame()
            except (AttributeError, TypeError) as e:
                # Se response não tem atributo data ou é de tipo inesperado
                logger.warning(f"⚠️ Erro ao processar resposta do Supabase: {e}")
                return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"❌ Erro ao ler '{table_name}': {e}")
            st.error(f"Erro ao carregar dados de '{table_name}': {e}")
            return pd.DataFrame()

    def append_data(self, table_name: str, data: dict | list[dict]):
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
            
            # 🔒 CONTROLE DE ACESSO E INJEÇÃO DE user_id
            if table_name in GLOBAL_TABLES:
                # Tabelas globais - apenas superuser pode acessar
                if not self._is_superuser():
                    raise ValueError(f"❌ Acesso negado: apenas superuser pode acessar tabela global '{table_name}'")
                else:
                    logger.info(f"👑 Superuser salvando em tabela global '{table_name}'")
            else:
                # Tabelas normais - injeta user_id
                if not self.user_id:
                    raise ValueError("❌ Usuário não identificado. Impossível salvar dados.")
                
                # Se não for superuser, injeta user_id
                if not self._is_superuser():
                    if isinstance(data, list):
                        for record in data:
                            record['user_id'] = self.user_id
                    else:
                        data['user_id'] = self.user_id
                    
                    logger.info(f"🔒 user_id {self.user_id} injetado nos registros")
                else:
                    logger.info(f"👑 Superuser salvando dados sem filtro de user_id")
            
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
            
            if table_name in GLOBAL_TABLES:
                # Tabelas globais - apenas superuser pode acessar
                if not self._is_superuser():
                    raise ValueError(f"❌ Acesso negado: apenas superuser pode acessar tabela global '{table_name}'")
                else:
                    logger.info(f"👑 Superuser atualizando tabela global '{table_name}'")
            else:
                # Tabelas normais - filtro por user_id
                if not self.user_id:
                    raise ValueError("❌ Usuário não identificado.")
                
                # Se não for superuser, aplica filtro de user_id
                if not self._is_superuser():
                    query = query.eq('user_id', self.user_id)
                    logger.info(f"🔒 Filtro de user_id aplicado na atualização")
                else:
                    logger.info(f"👑 Superuser atualizando dados sem filtro de user_id")
            
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
            
            if table_name in GLOBAL_TABLES:
                # Tabelas globais - apenas superuser pode acessar
                if not self._is_superuser():
                    raise ValueError(f"❌ Acesso negado: apenas superuser pode acessar tabela global '{table_name}'")
                else:
                    logger.info(f"👑 Superuser excluindo de tabela global '{table_name}'")
            else:
                # Tabelas normais - filtro por user_id
                if not self.user_id:
                    raise ValueError("❌ Usuário não identificado.")
                
                # Se não for superuser, aplica filtro de user_id
                if not self._is_superuser():
                    query = query.eq('user_id', self.user_id)
                    logger.info(f"🔒 Filtro de user_id aplicado na exclusão")
                else:
                    logger.info(f"👑 Superuser excluindo dados sem filtro de user_id")
            
            response = query.eq(filter_column, filter_value).execute()
            logger.info(f"✅ Registro deletado de '{table_name}'")
            return response
            
        except Exception as e:
            logger.error(f"❌ Erro ao deletar de '{table_name}': {e}")
            st.error(f"Erro ao deletar dados de '{table_name}': {e}")
            raise


def get_supabase_client() -> SupabaseClient | None:
    """Retorna instância do cliente Supabase."""
    try:
        # Diagnostica o estado atual antes de tentar inicializar
        init_diagnosis = diagnose_supabase_initialization()
        logger.info(f"🔍 Diagnóstico de inicialização: {init_diagnosis}")
        
        # Se há inicialização travada, força limpeza
        if init_diagnosis.get('status') == 'stuck':
            logger.warning("🔄 Inicialização travada detectada - forçando limpeza")
            force_cleanup_supabase_state()
        
        # Verifica se já existe na sessão para evitar recriação desnecessária
        if 'supabase_client' in st.session_state:
            return st.session_state['supabase_client']
        
        # Verifica se há uma inicialização em andamento para evitar loops
        if 'supabase_client_initializing' in st.session_state:
            # Verifica se a inicialização está travada (mais de 30 segundos)
            import time
            current_time = time.time()
            init_start_time = st.session_state.get('supabase_client_init_start_time', current_time)
            
            if current_time - init_start_time > 30:  # 30 segundos de timeout
                logger.warning("⚠️ Inicialização do Supabase travada há mais de 30s - limpando estado")
                force_cleanup_supabase_state()
                return None
            else:
                logger.warning("⚠️ Cliente Supabase já está sendo inicializado - evitando loop")
                return None
        
        # Verifica se há um erro de inicialização anterior
        if 'supabase_client_error' in st.session_state:
            logger.warning("⚠️ Erro anterior na inicialização do Supabase - retornando None")
            return None
        
        # Marca que está inicializando
        st.session_state['supabase_client_initializing'] = True
        st.session_state['supabase_client_init_start_time'] = time.time()
        
        logger.info("🔄 Inicializando cliente Supabase...")
        
        # Timeout para evitar carregamento infinito
        import time
        start_time = time.time()
        timeout_seconds = 30  # 30 segundos de timeout
        
        try:
            client = SupabaseClient()
            
            # Verifica se não excedeu o timeout
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout_seconds:
                logger.error(f"❌ Timeout na inicialização do cliente Supabase ({elapsed_time:.2f}s)")
                st.error("Timeout na conexão com o banco de dados")
                st.session_state['supabase_client_error'] = True
                return None
            
            logger.info(f"✅ Cliente Supabase criado com sucesso em {elapsed_time:.2f}s")
            
            # Armazena na sessão para reutilização
            st.session_state['supabase_client'] = client
            return client
            
        except Exception as init_error:
            logger.error(f"❌ Erro na inicialização do Supabase: {init_error}")
            st.session_state['supabase_client_error'] = True
            return None
            
        finally:
            # Remove a flag de inicialização
            if 'supabase_client_initializing' in st.session_state:
                del st.session_state['supabase_client_initializing']
                
    except Exception as e:
        logger.error(f"❌ Falha crítica ao criar cliente Supabase: {e}")
        st.error(f"Erro crítico de conexão: {e}")
        
        # Remove a flag de inicialização em caso de erro
        if 'supabase_client_initializing' in st.session_state:
            del st.session_state['supabase_client_initializing']
        
        # Marca erro para evitar tentativas repetidas
        st.session_state['supabase_client_error'] = True
        
        return None


def get_supabase_client_no_cache() -> SupabaseClient | None:
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


def reset_supabase_client():
    """Limpa o estado do cliente Supabase para permitir nova inicialização."""
    if 'supabase_client' in st.session_state:
        del st.session_state['supabase_client']
    if 'supabase_client_initializing' in st.session_state:
        del st.session_state['supabase_client_initializing']
    if 'supabase_client_error' in st.session_state:
        del st.session_state['supabase_client_error']
    if 'supabase_client_init_start_time' in st.session_state:
        del st.session_state['supabase_client_init_start_time']
    logger.info("🔄 Estado do cliente Supabase limpo - nova inicialização permitida")


def force_cleanup_supabase_state():
    """Força a limpeza do estado do Supabase quando travado."""
    logger.warning("🔄 Forçando limpeza do estado do Supabase...")
    
    # Limpa todas as flags de estado
    state_keys = [
        'supabase_client',
        'supabase_client_initializing', 
        'supabase_client_init_start_time',
        'supabase_client_error'
    ]
    
    for key in state_keys:
        if key in st.session_state:
            del st.session_state[key]
    
    # Aguarda um momento para garantir que o estado foi limpo
    import time
    time.sleep(0.1)
    
    logger.info("✅ Estado do Supabase limpo com sucesso")


def diagnose_supabase_connection():
    """Diagnostica problemas de conexão com o Supabase."""
    try:
        # Verifica se as credenciais existem
        if "supabase" not in st.secrets:
            return {
                "status": "error",
                "message": "Configuração do Supabase não encontrada em st.secrets",
                "solution": "Configure as credenciais do Supabase no Streamlit Cloud"
            }
        
        url = st.secrets["supabase"].get("url")
        key = st.secrets["supabase"].get("key")
        
        if not url or not key:
            return {
                "status": "error", 
                "message": "Credenciais do Supabase incompletas",
                "solution": "Verifique se url e key estão configurados corretamente"
            }
        
        if not url.startswith("https://"):
            return {
                "status": "error",
                "message": "URL do Supabase inválida",
                "solution": "A URL deve começar com https://"
            }
        
        # Tenta uma conexão simples
        try:
            from supabase import create_client
            test_client = create_client(url, key)
            test_response = test_client.table("usuarios").select("id").limit(1).execute()
            return {
                "status": "success",
                "message": "Conexão com Supabase funcionando",
                "url": url,
                "key_length": len(key)
            }
        except Exception as conn_error:
            return {
                "status": "error",
                "message": f"Erro de conexão: {conn_error}",
                "solution": "Verifique se o projeto Supabase está ativo e acessível"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Erro no diagnóstico: {e}",
            "solution": "Verifique a configuração do Streamlit"
        }


def diagnose_supabase_initialization():
    """Diagnostica especificamente problemas de inicialização travada."""
    try:
        # Verifica estado atual da sessão
        state_info = {
            "supabase_client_exists": 'supabase_client' in st.session_state,
            "initializing": 'supabase_client_initializing' in st.session_state,
            "error_flag": 'supabase_client_error' in st.session_state,
            "init_start_time": st.session_state.get('supabase_client_init_start_time')
        }
        
        # Se há inicialização em andamento, verifica se está travada
        if state_info["initializing"]:
            import time
            current_time = time.time()
            init_start = state_info["init_start_time"]
            
            if init_start:
                elapsed = current_time - init_start
                if elapsed > 30:
                    return {
                        "status": "stuck",
                        "message": f"Inicialização travada há {elapsed:.1f}s",
                        "solution": "Execute force_cleanup_supabase_state() para limpar",
                        "elapsed_time": elapsed
                    }
                else:
                    return {
                        "status": "initializing",
                        "message": f"Inicialização em andamento há {elapsed:.1f}s",
                        "elapsed_time": elapsed
                    }
        
        # Se há flag de erro
        if state_info["error_flag"]:
            return {
                "status": "error",
                "message": "Erro anterior na inicialização",
                "solution": "Execute reset_supabase_client() para tentar novamente"
            }
        
        # Se cliente existe
        if state_info["supabase_client_exists"]:
            return {
                "status": "success",
                "message": "Cliente Supabase já inicializado",
                "client_type": type(st.session_state['supabase_client']).__name__
            }
        
        return {
            "status": "ready",
            "message": "Pronto para inicialização",
            "state_info": state_info
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Erro no diagnóstico de inicialização: {e}",
            "solution": "Verifique os logs para mais detalhes"
        }
