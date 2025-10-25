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
            return st.user.email.lower().strip()
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


def get_user_info() -> dict | None:
    """
    Retorna o registro do usuário. Se for o superusuário, "fabrica" o registro
    usando os dados dos segredos, incluindo o ambiente de testes.
    """
    if is_superuser():
        # "Fabrica" um registro de usuário mestre, agora incluindo o ambiente de testes dos segredos.
        return {
            'email': get_user_email(),
            'nome': 'Desenvolvedor (Mestre)',
            'role': 'admin',
            'plano': 'premium_ia',
            'status': 'ativo',
            'spreadsheet_id': st.secrets.get("superuser", {}).get("spreadsheet_id"),
            'folder_id': st.secrets.get("superuser", {}).get("folder_id"),
            'data_cadastro': date.today().isoformat(),
            'trial_end_date': None
        }

    # Se não for o superusuário, executa a lógica normal.
    user_email = get_user_email()
    if not user_email:
        logger.warning("Email do usuário não encontrado")
        return None
    
    logger.info(f"🔍 Buscando usuário: {user_email}")
    users_df = get_users_data()
    
    if users_df.empty:
        logger.warning("❌ Tabela de usuários está vazia")
        return None
    
    user_entry = users_df[users_df['email'] == user_email]
    
    if user_entry.empty:
        logger.warning(f"❌ Usuário {user_email} não encontrado na tabela")
        return None
    
    logger.info(f"✅ Usuário encontrado: {user_email}")
    return user_entry.iloc[0].to_dict()


def is_uuid_unique(uuid_value: int) -> bool:
    """
    Verifica se o UUID gerado é único na tabela usuarios.
    
    Args:
        uuid_value: UUID a verificar
        
    Returns:
        bool: True se único, False se já existe
    """
    try:
        from supabase_local import get_supabase_client
        db_client = get_supabase_client()
        
        # Busca se já existe um usuário com esse ID
        existing_users = db_client.get_data("usuarios")
        if not existing_users.empty and 'id' in existing_users.columns:
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
    
    # Verifica se é único, se não for, gera outro
    attempts = 0
    while not is_uuid_unique(final_uuid) and attempts < 5:
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

def get_user_id() -> int:
    """
    Retorna o ID (INTEGER) do usuário logado.
    SUPERUSERS NÃO TÊM ID - retorna None para superusers.
    Apenas usuários normais têm ID na tabela.
    
    Returns:
        int: ID do usuário ou None se não encontrado/superuser
    """
    # SUPERUSERS NÃO TÊM ID - retorna None imediatamente
    if is_superuser():
        logger.info("👑 Superuser não possui ID - usando None")
        return None
    
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
    
    # Se não tem ID, retorna None (não gera automaticamente)
    logger.warning(f"Usuário {user_email} não possui ID na tabela usuarios!")
    return None


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
        from supabase_local import get_supabase_client
        db_client = get_supabase_client()
        
        # Atualiza o registro do usuário com o novo UUID
        update_data = {'id': new_uuid}
        db_client.update_data("usuarios", update_data, "email", user_email)
        
        logger.info(f"✅ UUID forte {new_uuid} salvo para NOVO usuário {user_email}")
        return new_uuid
        
    except Exception as e:
        logger.error(f"❌ Erro ao salvar UUID para novo usuário: {e}")
        return new_uuid

def save_access_request(user_name, user_email, justification):
    """Salva uma solicitação de acesso na tabela 'solicitacoes_acesso' do Supabase."""
    try:
        sao_paulo_tz = pytz.timezone("America/Sao_Paulo")
        timestamp = datetime.now(sao_paulo_tz).strftime('%Y-%m-%d %H:%M:%S')

        # PARA: Usa o cliente Supabase e um dicionário
        db_client = get_supabase_client()

        # Verifica se já existe solicitação pendente
        df_requests = db_client.get_data("solicitacoes_acesso")
        if not df_requests.empty:
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
    if not pd.isna(trial_end_date) and isinstance(trial_end_date, date) and date.today() > trial_end_date:
        return 'trial_expirado'
    return sheet_status


def is_on_trial() -> bool:
    user_info = get_current_user_info()  # <-- MUDANÇA AQUI
    if not user_info:
        return False
    trial_end_date = user_info.get('trial_end_date')
    if pd.isna(trial_end_date):
        return False
    return date.today() <= trial_end_date


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
        if is_superuser():
            st.sidebar.info("👑 Superuser - acesso total ao sistema")
            logger.info(f"👑 Superuser {user_email} - sem ID (normal para superusers)")
        else:
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
    
    if is_superuser():
        logger.info(f"✅ Sidebar configurado para {user_email} (Superuser) - {plan_display}")
    else:
        logger.info(f"✅ Sidebar configurado para {user_email} (ID: {user_id}) - {plan_display}")
    
    return True  # ✅ Ambiente carregado com sucesso