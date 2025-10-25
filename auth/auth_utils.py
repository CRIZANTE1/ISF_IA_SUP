# auth/auth_utils.py (REFATORADO)

import streamlit as st
import pandas as pd
from datetime import date, datetime
import pytz
import logging

# DE: from gdrive.gdrive_upload import GoogleDriveUploader
# DE: from gdrive.config import USERS_SHEET_NAME, ACCESS_REQUESTS_SHEET_NAME
# PARA: Importações refatoradas
# Usamos a função genérica que agora usa Supabase
from operations.history import load_sheet_data
from supabase_local import get_supabase_client
from utils.github_notifications import notify_new_access_request

logger = logging.getLogger(__name__)


def is_oidc_available():
    try:
        return hasattr(st.user, 'is_logged_in')
    except Exception:
        return False


def is_user_logged_in():
    try:
        return st.user.is_logged_in
    except Exception:
        return False


def is_superuser() -> bool:
    try:
        user_email = get_user_email()
        superuser_email = st.secrets.get("superuser", {}).get("admin_email", "").lower().strip()
        return user_email is not None and user_email == superuser_email
    except (KeyError, AttributeError):
        return False


def get_user_display_name():
    try:
        if is_superuser():
            return "Desenvolvedor (Mestre)"
        if hasattr(st.user, 'name') and st.user.name:
            return st.user.name
        elif hasattr(st.user, 'email'):
            return st.user.email
        return "Usuário Anônimo"
    except Exception:
        return "Usuário Anônimo"


def get_user_email() -> str | None:
    try:
        if hasattr(st.user, 'email') and st.user.email:
            email = st.user.email
            if isinstance(email, str):
                return email.lower().strip()
        return None
    except Exception:
        return None


@st.cache_data(ttl=300, show_spinner="Verificando permissões...")
def get_users_data():
    """
    Carrega dados de usuários com tratamento robusto de erros, agora do Supabase.
    """
    try:
        logger.info("🔄 Carregando dados de usuários do Supabase...")
        # PARA: A lógica complexa de leitura e normalização foi substituída por uma única chamada.
        df = load_sheet_data("usuarios")
        
        logger.info(f"📊 Dados carregados: {len(df)} registros")
        if not df.empty:
            logger.info(f"📋 Colunas disponíveis: {list(df.columns)}")
            # Converte colunas de data que vêm como string do Supabase
            if 'data_cadastro' in df.columns:
                df['data_cadastro'] = pd.to_datetime(
                    df['data_cadastro'], errors='coerce').dt.date
            if 'trial_end_date' in df.columns:
                df['trial_end_date'] = pd.to_datetime(
                    df['trial_end_date'], errors='coerce').dt.date
        else:
            logger.warning("⚠️ Tabela de usuários está vazia")

        return df

    except Exception as e:
        logger.error(f"❌ Erro crítico ao carregar dados de usuários: {e}")
        st.error(f"Erro crítico ao carregar dados de usuários: {e}")
        return pd.DataFrame()


def get_users_data_no_cache():
    """
    Versão sem cache para debug - carrega dados de usuários diretamente do Supabase.
    """
    try:
        logger.info("🔄 Carregando dados de usuários do Supabase (sem cache)...")
        db_client = get_supabase_client()
        if db_client is None:
            logger.error("❌ Cliente Supabase não disponível")
            return pd.DataFrame()
        
        df = db_client.get_data("usuarios")
        
        logger.info(f"📊 Dados carregados (sem cache): {len(df)} registros")
        if not df.empty:
            logger.info(f"📋 Colunas disponíveis: {list(df.columns)}")
            # Converte colunas de data que vêm como string do Supabase
            if 'data_cadastro' in df.columns:
                df['data_cadastro'] = pd.to_datetime(
                    df['data_cadastro'], errors='coerce').dt.date
            if 'trial_end_date' in df.columns:
                df['trial_end_date'] = pd.to_datetime(
                    df['trial_end_date'], errors='coerce').dt.date
        else:
            logger.warning("⚠️ Tabela de usuários está vazia (sem cache)")

        return df

    except Exception as e:
        logger.error(f"❌ Erro crítico ao carregar dados de usuários (sem cache): {e}")
        return pd.DataFrame()


def get_user_info() -> dict | None:
    """
    Retorna o registro do usuário. Se for o superusuário, primeiro tenta buscar na tabela,
    se não encontrar, "fabrica" o registro usando os dados dos segredos.
    """
    user_email = get_user_email()
    if not user_email:
        logger.warning("Email do usuário não encontrado")
        return None
    
    # Circuit breaker: evita loops infinitos
    if 'get_user_info_called' in st.session_state:
        call_count = st.session_state.get('get_user_info_call_count', 0)
        if call_count > 5:  # Máximo 5 tentativas (reduzido para ser mais eficiente)
            logger.warning(f"⚠️ Circuit breaker ativado - muitas tentativas para {user_email}")
            # Retorna registro fabricado para superuser SEM tentar buscar na tabela
            if is_superuser():
                logger.info(f"✅ Retornando registro fabricado para superuser {user_email} (circuit breaker ativo)")
                return {
                    'email': user_email,
                    'nome': 'Desenvolvedor (Mestre)',
                    'role': 'admin',
                    'plano': 'premium_ia',
                    'status': 'ativo',
                    'spreadsheet_id': st.secrets.get("superuser", {}).get("spreadsheet_id"),
                    'folder_id': st.secrets.get("superuser", {}).get("folder_id"),
                    'data_cadastro': date.today().isoformat(),
                    'trial_end_date': None
                }
            return None
        st.session_state['get_user_info_call_count'] = call_count + 1
    else:
        st.session_state['get_user_info_called'] = True
        st.session_state['get_user_info_call_count'] = 1
    
    # Verifica se as credenciais do Supabase estão configuradas
    try:
        credentials_check = check_supabase_credentials()
        if credentials_check.get('status') == 'error':
            logger.warning(f"⚠️ Problema com credenciais do Supabase: {credentials_check.get('message')}")
            logger.warning(f"💡 Solução: {credentials_check.get('solution')}")
    except Exception as e:
        logger.warning(f"⚠️ Erro ao verificar credenciais: {e}")
    
    logger.info(f"🔍 Buscando usuário: {user_email}")
    users_df = get_users_data()
    
    logger.info(f"📊 DataFrame de usuários carregado: {len(users_df)} registros")
    if not users_df.empty:
        logger.info(f"📋 Colunas disponíveis: {list(users_df.columns)}")
        logger.info(f"📧 Emails na tabela: {users_df['email'].tolist() if 'email' in users_df.columns else 'Coluna email não encontrada'}")
        
        user_entry = users_df[users_df['email'] == user_email]
        logger.info(f"🔍 Busca por '{user_email}': {len(user_entry)} resultados encontrados")
        
        if not user_entry.empty:
            logger.info(f"✅ Usuário encontrado na tabela: {user_email}")
            user_data = user_entry.iloc[0].to_dict()
            logger.info(f"📋 Dados do usuário: {user_data}")
            return user_data
        else:
            logger.warning(f"❌ Usuário '{user_email}' não encontrado na tabela")
            # Tenta buscar sem cache para debug
            logger.info("🔍 Tentando busca sem cache para debug...")
            users_df_no_cache = get_users_data_no_cache()
            if not users_df_no_cache.empty:
                logger.info(f"📊 DataFrame sem cache: {len(users_df_no_cache)} registros")
                logger.info(f"📧 Emails na tabela (sem cache): {users_df_no_cache['email'].tolist() if 'email' in users_df_no_cache.columns else 'Coluna email não encontrada'}")
                user_entry_no_cache = users_df_no_cache[users_df_no_cache['email'] == user_email]
                if not user_entry_no_cache.empty:
                    logger.info(f"✅ Usuário encontrado na busca sem cache: {user_email}")
                    user_data = user_entry_no_cache.iloc[0].to_dict()
                    logger.info(f"📋 Dados do usuário (sem cache): {user_data}")
                    return user_data
    else:
        logger.warning("⚠️ DataFrame de usuários está vazio")
    
    # Se não encontrou na tabela e é superuser, fabrica o registro
    if is_superuser():
        logger.info("👑 Superuser não encontrado na tabela - verificando se realmente não existe")
        
        # Tenta buscar o usuário novamente sem cache para verificar se realmente não existe
        try:
            users_df_no_cache = get_users_data_no_cache()
            if not users_df_no_cache.empty:
                user_entry_no_cache = users_df_no_cache[users_df_no_cache['email'] == user_email]
                if not user_entry_no_cache.empty:
                    logger.info(f"✅ Superuser {user_email} encontrado na busca sem cache")
                    user_data = user_entry_no_cache.iloc[0].to_dict()
                    logger.info(f"📋 Dados do usuário (sem cache): {user_data}")
                    return user_data
        except Exception as e:
            logger.warning(f"⚠️ Erro na busca sem cache: {e}")
        
        # Diagnostica problema de conexão com Supabase
        try:
            from supabase_local import diagnose_supabase_connection, force_cleanup_supabase_state
            diagnosis = diagnose_supabase_connection()
            logger.warning(f"🔍 Diagnóstico do Supabase: {diagnosis}")
            
            # Se há problema de conexão, tenta limpar o estado e reconectar
            if diagnosis.get('status') == 'error':
                logger.warning("🔄 Tentando limpar estado do Supabase e reconectar...")
                force_cleanup_supabase_state()
                
                # Tenta uma nova busca após limpeza
                try:
                    users_df_retry = get_users_data_no_cache()
                    if not users_df_retry.empty:
                        user_entry_retry = users_df_retry[users_df_retry['email'] == user_email]
                        if not user_entry_retry.empty:
                            logger.info(f"✅ Superuser {user_email} encontrado após limpeza do estado")
                            user_data = user_entry_retry.iloc[0].to_dict()
                            return user_data
                except Exception as retry_error:
                    logger.warning(f"⚠️ Erro na tentativa de reconexão: {retry_error}")
                    
        except Exception as diag_error:
            logger.warning(f"⚠️ Erro no diagnóstico: {diag_error}")
        
        # IMPORTANTE: NÃO cria registro na tabela se o usuário já existir
        # Apenas retorna registro fabricado para uso da sessão atual
        logger.info(f"✅ Registro fabricado para superuser {user_email} (NÃO salvo na tabela - apenas para uso temporário)")
        
        superuser_record = {
            'email': user_email,
            'nome': 'Desenvolvedor (Mestre)',
            'role': 'admin',
            'plano': 'premium_ia',
            'status': 'ativo',
            'spreadsheet_id': st.secrets.get("superuser", {}).get("spreadsheet_id"),
            'folder_id': st.secrets.get("superuser", {}).get("folder_id"),
            'data_cadastro': date.today().isoformat(),
            'trial_end_date': None
        }
        
        return superuser_record
    
    # Se não é superuser e não encontrou na tabela
    logger.warning(f"❌ Usuário {user_email} não encontrado na tabela")
    return None


def is_uuid_unique(uuid_value: int) -> bool:
    """
    Verifica se o UUID gerado é único na tabela usuarios.
    
    Args:
        uuid_value: UUID a verificar
        
    Returns:
        bool: True se único, False se já existe
    """
    try:
        db_client = get_supabase_client()
        
        if db_client is None:
            return True  # Se não conseguir conectar, assume que é único
        
        # Busca se já existe um usuário com esse ID
        existing_users = db_client.get_data("usuarios")
        if existing_users is not None and not existing_users.empty and 'id' in existing_users.columns:
            existing_ids = existing_users['id'].tolist()
            return uuid_value not in existing_ids
        
        return True  # Se não conseguir verificar, assume que é único
        
    except Exception as e:
        logger.warning(f"Erro ao verificar unicidade do UUID: {e}")
        return True  # Em caso de erro, assume que é único


def generate_strong_uuid(user_email: str) -> int:
    """
    Gera um UUID forte e único para o usuário.
    Compatível com PostgreSQL integer (até 2,147,483,647).
    
    Args:
        user_email: Email do usuário
        
    Returns:
        int: UUID forte como inteiro (dentro do range de integer)
    """
    import hashlib
    import time
    import random
    import uuid
    
    # Método 1: UUID4 padrão (mais forte) - limitado ao range de integer
    uuid4_string = str(uuid.uuid4()).replace('-', '')
    uuid4_int = int(uuid4_string[:8], 16) % 2147483647  # Limita ao range de integer
    
    # Método 2: Hash SHA-256 com múltiplos fatores
    timestamp = str(int(time.time() * 1000))  # milissegundos
    random_salt = str(random.randint(100000, 999999))
    email_hash = hashlib.sha256(user_email.encode()).hexdigest()[:6]
    
    combined_string = f"{user_email}{timestamp}{random_salt}{email_hash}"
    strong_hash = hashlib.sha256(combined_string.encode()).hexdigest()
    hash_int = int(strong_hash[:8], 16) % 2147483647  # Limita ao range de integer
    
    # Combina ambos os métodos para máxima robustez
    final_uuid = (uuid4_int + hash_int) % 2147483647  # Garante que está no range
    
    # Garante que não seja muito pequeno (pelo menos 6 dígitos)
    if final_uuid < 100000:
        final_uuid += 100000
    
    # Verifica se é único, se não for, gera outro (limitado a 3 tentativas para evitar loops)
    attempts = 0
    while attempts < 3:
        try:
            if is_uuid_unique(final_uuid):
                break
        except Exception as e:
            logger.warning(f"Erro ao verificar unicidade do UUID: {e}")
            break
            
        attempts += 1
        # Gera um novo UUID com timestamp atualizado
        timestamp = str(int(time.time() * 1000) + attempts)
        combined_string = f"{user_email}{timestamp}{random.randint(100000, 999999)}"
        strong_hash = hashlib.sha256(combined_string.encode()).hexdigest()
        final_uuid = int(strong_hash[:8], 16) % 2147483647
        
        if final_uuid < 100000:
            final_uuid += 100000
    
    logger.info(f"🔐 UUID forte gerado: {final_uuid} (compatível com PostgreSQL integer)")
    return final_uuid

def get_user_id() -> int | None:
    """
    Retorna o ID (INTEGER) do usuário logado.
    Aceita qualquer ID existente (simples como 1, 2, 3 ou UUID forte como 308380173).
    NÃO gera UUIDs automaticamente - apenas retorna o ID existente.
    
    Returns:
        int | None: ID do usuário ou None se não encontrado
    """
    # Verifica se já temos o user_id na sessão (evita loops)
    if 'current_user_id' in st.session_state and st.session_state['current_user_id']:
        try:
            cached_id = int(st.session_state['current_user_id'])
            logger.info(f"✅ ID do usuário da sessão: {cached_id}")
            return cached_id
        except (ValueError, TypeError):
            logger.warning(f"ID da sessão inválido: {st.session_state['current_user_id']}")
    
    user_info = get_user_info()
    
    if not user_info:
        logger.warning("Não foi possível obter informações do usuário")
        return None
    
    user_id = user_info.get('id')
    user_email = user_info.get('email')
    
    # Converte ID para inteiro se for string
    # Aceita qualquer ID existente (simples ou UUID forte)
    if user_id is not None:
        try:
            user_id = int(user_id)
            logger.info(f"✅ ID do usuário {user_email}: {user_id} (aceito como válido)")
            # Armazena na sessão para evitar consultas repetidas
            st.session_state['current_user_id'] = user_id
            return user_id
        except (ValueError, TypeError):
            logger.warning(f"ID do usuário não é um número válido: {user_id}")
    
    # Se não tem ID, verifica se é um registro fabricado (superuser)
    if is_superuser():
        logger.warning(f"Superuser {user_email} não possui ID - pode ser um usuário novo")
        # Para superuser sem ID, gera um ID temporário apenas para a sessão
        # NÃO salva na tabela - apenas para uso da sessão atual
        temp_id = generate_strong_uuid(user_email)
        st.session_state['current_user_id'] = temp_id
        logger.info(f"🔐 ID temporário gerado para superuser: {temp_id}")
        return temp_id
    else:
        logger.warning(f"Usuário {user_email} não possui ID na tabela usuarios!")
        return None


def save_new_user_with_id(user_email: str, user_data: dict) -> int:
    """
    Salva um NOVO usuário na tabela com ID gerado.
    Usado apenas para usuários que realmente não existem na tabela.
    
    Args:
        user_email: Email do novo usuário
        user_data: Dados do usuário para salvar
        
    Returns:
        int: UUID forte para o novo usuário
    """
    logger.info(f"🔧 Salvando NOVO usuário com ID: {user_email}")
    
    new_uuid = generate_strong_uuid(user_email)
    
    try:
        db_client = get_supabase_client()
        
        if db_client is None:
            logger.warning("Cliente Supabase não disponível")
            return new_uuid
        
        # Adiciona o ID aos dados do usuário
        user_data_with_id = user_data.copy()
        user_data_with_id['id'] = new_uuid
        
        # Salva o novo usuário na tabela
        db_client.append_data("usuarios", user_data_with_id)
        
        logger.info(f"✅ NOVO usuário {user_email} salvo com ID {new_uuid}")
        return new_uuid
        
    except Exception as e:
        logger.error(f"❌ Erro ao salvar novo usuário: {e}")
        return new_uuid


def generate_uuid_for_new_user(user_email: str) -> int:
    """
    Gera UUID forte APENAS para novos usuários.
    Usado quando um novo usuário é cadastrado no sistema.
    
    Args:
        user_email: Email do novo usuário
        
    Returns:
        int: UUID forte para o novo usuário
    """
    logger.info(f"🔧 Gerando UUID forte para NOVO usuário: {user_email}")
    
    new_uuid = generate_strong_uuid(user_email)
    
    try:
        db_client = get_supabase_client()
        
        if db_client is None:
            logger.warning("Cliente Supabase não disponível")
            return new_uuid
        
        # Atualiza o registro do usuário com o novo UUID
        update_data = {'id': new_uuid}
        db_client.update_data("usuarios", update_data, "email", user_email)
        
        logger.info(f"✅ UUID forte {new_uuid} salvo para NOVO usuário {user_email}")
        return new_uuid
        
    except Exception as e:
        logger.error(f"❌ Erro ao salvar UUID para novo usuário: {e}")
        return new_uuid

def reset_user_info_circuit_breaker():
    """Limpa o circuit breaker do get_user_info para permitir novas tentativas."""
    if 'get_user_info_called' in st.session_state:
        del st.session_state['get_user_info_called']
    if 'get_user_info_call_count' in st.session_state:
        del st.session_state['get_user_info_call_count']
    logger.info("🔄 Circuit breaker do get_user_info limpo - novas tentativas permitidas")


def check_supabase_credentials():
    """Verifica se as credenciais do Supabase estão configuradas corretamente."""
    try:
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
        
        return {
            "status": "success",
            "message": "Credenciais do Supabase configuradas corretamente",
            "url": url,
            "key_length": len(key)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Erro ao verificar credenciais: {e}",
            "solution": "Verifique a configuração do Streamlit"
        }


def save_access_request(user_name, user_email, justification):
    """Salva uma solicitação de acesso na tabela 'solicitacoes_acesso' do Supabase."""
    try:
        sao_paulo_tz = pytz.timezone("America/Sao_Paulo")
        timestamp = datetime.now(sao_paulo_tz).strftime('%Y-%m-%d %H:%M:%S')

        # PARA: Usa o cliente Supabase e um dicionário
        db_client = get_supabase_client()

        if db_client is None:
            st.error("Cliente de banco de dados não disponível")
            return False

        # Verifica se já existe solicitação pendente
        df_requests = db_client.get_data("solicitacoes_acesso")
        if df_requests is not None and not df_requests.empty:
            if not df_requests[(df_requests['email_usuario'] == user_email) & (df_requests['status'] == 'Pendente')].empty:
                st.warning(
                    "Você já possui uma solicitação de acesso pendente.")
                return False

        # PARA: Cria um dicionário em vez de uma lista
        request_record = {
            "timestamp_solicitacao": timestamp,
            "nome_usuario": user_name,
            "email_usuario": user_email,
            "tipo_solicitacao": "Solicitação de Trial",
            "justificativa": justification,
            "status": "Pendente"
        }

        # PARA: Usa o método append_data
        db_client.append_data("solicitacoes_acesso", request_record)

        # A lógica de notificação permanece a mesma
        try:
            admin_email = st.secrets.get("superuser", {}).get("admin_email")
            if admin_email:
                notify_new_access_request(
                    admin_email=admin_email,
                    user_email=user_email,
                    user_name=user_name,
                    justification=justification or "Nenhuma justificativa fornecida"
                )
                st.info(" O administrador foi notificado sobre sua solicitação.")
        except Exception as notification_error:
            print(
                f"Aviso: Falha ao enviar notificação para admin: {notification_error}")

        return True

    except Exception as e:
        st.error(f"Ocorreu um erro ao enviar sua solicitação: {e}")
        return False

# --- NOVAS FUNÇÕES RÁPIDAS ---


def get_current_user_info() -> dict | None:
    """Retorna os dados do usuário logado diretamente da sessão. É super rápido."""
    return st.session_state.get('user_data')


def get_current_user_role() -> str:
    """Retorna o 'role' do usuário da sessão."""
    user_data = get_current_user_info()
    return user_data.get('role', 'viewer') if user_data else 'viewer'
# --- FIM DAS NOVAS FUNÇÕES ---


def get_effective_user_status() -> str:
    user_info = get_current_user_info()  # <-- MUDANÇA AQUI
    if not user_info:
        return 'inativo'
    sheet_status = user_info.get('status', 'inativo')
    trial_end_date = user_info.get('trial_end_date')
    if sheet_status != 'ativo':
        return sheet_status
    # Verifica se trial_end_date é uma data válida e se já expirou
    if trial_end_date is not None:
        try:
            if isinstance(trial_end_date, date) and date.today() > trial_end_date:
                return 'trial_expirado'
        except (TypeError, ValueError):
            # Se houver erro na comparação, ignora
            pass
    return sheet_status


def is_on_trial() -> bool:
    user_info = get_current_user_info()  # <-- MUDANÇA AQUI
    if not user_info:
        return False
    trial_end_date = user_info.get('trial_end_date')
    if trial_end_date is None:
        return False
    try:
        if pd.isna(trial_end_date):
            return False
    except (TypeError, ValueError):
        # Se pd.isna falhar, assume que não é NaN
        pass
    if isinstance(trial_end_date, date):
        return date.today() <= trial_end_date
    return False


def get_effective_user_plan() -> str:
    user_info = get_current_user_info()  # <-- MUDANÇA AQUI
    if not user_info:
        return 'nenhum'
    sheet_plan = user_info.get('plano', 'nenhum')
    if is_on_trial():
        return 'premium_ia'
    return sheet_plan


def get_user_role():
    """Retorna o role do usuário logado - agora ultra rápido!"""
    return get_current_user_role()  # <-- MUDANÇA AQUI


def check_user_access(required_role="viewer"):
    """
    Checks if the current user has the required role or higher.
    Returns True if authorized, False otherwise.

    Roles hierarchy (highest to lowest):
    - superuser (special role)
    - admin
    - editor
    - viewer

    Usage:
        if not check_user_access("editor"):
            st.warning("You need editor permissions or higher.")
            return
    """
    role_hierarchy = {"viewer": 1, "editor": 2, "admin": 3}
    user_role = get_user_role()

    # Superuser always has access
    if is_superuser():
        return True

    # If required_role isn't in the hierarchy, default to viewer
    required_level = role_hierarchy.get(required_role, 1)
    user_level = role_hierarchy.get(user_role, 0)

    return user_level >= required_level


def can_edit(): return check_user_access("editor")
def can_view(): return check_user_access("viewer")
def is_admin(): return check_user_access("admin")
def has_pro_features(): return get_effective_user_plan() in [
    'pro', 'premium_ia']


def has_ai_features(): return get_effective_user_plan() == 'premium_ia'


def setup_sidebar():
    """
    Configura a sidebar com informações do usuário.
    VERSÃO CORRIGIDA - Usa user_id para isolamento de dados.
    
    Returns:
        bool: True se o ambiente está OK, False caso contrário
    """
    user_info = get_user_info()
    
    if not user_info:
        st.sidebar.error("❌ Erro ao carregar dados do usuário.")
        return False
    
    effective_status = get_effective_user_status()
    user_email = user_info.get('email')
    
    # Obtém o user_id (não gera automaticamente)
    user_id = get_user_id()
    if not user_id:
        st.sidebar.warning("⚠️ Usuário sem ID no sistema.")
        logger.warning(f"Usuário {user_email} não possui ID - pode ser um usuário novo")
        # Para usuários sem ID, ainda permite acesso (pode ser superuser ou novo usuário)
        st.session_state['current_user_id'] = None
        st.session_state['current_user_email'] = user_email
        return True  # Permite acesso mesmo sem ID
    
    # Garante que user_id é inteiro
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        logger.error(f"ID do usuário não é um número válido: {user_id}")
        st.sidebar.error("❌ ID do usuário inválido.")
        return False
    
    # Valida status do usuário
    if effective_status not in ['ativo', 'superuser']:
        if effective_status == 'trial_expirado':
            st.sidebar.warning("⏳ Trial expirado")
        elif effective_status == 'inativo':
            st.sidebar.warning("🔒 Conta inativa")
        else:
            st.sidebar.error(f"❌ Status: {effective_status}")
        
        if not is_admin():
            return False
    
    # ✅ Armazena user_id na sessão para uso pelo SupabaseClient
    if st.session_state.get('current_user_id') != user_id:
        # Só limpa cache se realmente mudou de usuário
        if st.session_state.get('current_user_id') is not None:
            st.cache_data.clear()
            logger.info(f"🔄 Cache limpo para novo usuário: {user_email}")
    
    st.session_state['current_user_id'] = user_id
    st.session_state['current_user_email'] = user_email
    
    # Exibe informações do plano
    current_plan = get_effective_user_plan()
    plan_emoji = {
        'basico': '📊',
        'pro': '🔧',
        'premium_ia': '🤖'
    }.get(current_plan, '📦')
    
    plan_display = {
        'basico': 'Básico',
        'pro': 'Pro',
        'premium_ia': 'Premium IA'
    }.get(current_plan, current_plan.title())
    
    # Trial badge
    if is_on_trial():
        trial_end = user_info.get('trial_end_date')
        if trial_end and isinstance(trial_end, date):
            days_left = (trial_end - date.today()).days
            if days_left > 0:
                st.sidebar.success(f"🚀 Trial Premium: {days_left} dias")
            else:
                st.sidebar.warning("⏳ Trial expirado")
    
    st.sidebar.info(f"{plan_emoji} **Plano:** {plan_display}")
    
    logger.info(f"✅ Sidebar configurado para {user_email} (ID: {user_id}) - {plan_display}")
    
    return True  # ✅ Ambiente carregado com sucesso
