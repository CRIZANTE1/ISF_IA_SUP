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


def debug_user_lookup():
    """Função de debug para verificar dados do usuário"""
    try:
        from supabase_local import get_supabase_client
        import pandas as pd
        
        logger.info("🔍 DEBUG: Verificando dados diretamente no Supabase...")
        
        # Conecta diretamente ao Supabase
        db_client = get_supabase_client()
        
        # Busca todos os usuários
        users_data = db_client.get_data("usuarios")
        logger.info(f"📊 Total de usuários no banco: {len(users_data)}")
        
        if not users_data.empty:
            logger.info(f"📋 Colunas: {list(users_data.columns)}")
            logger.info(f"📧 Emails: {users_data['email'].tolist()}")
            
            # Verifica se o email do usuário atual está na lista
            current_email = get_user_email()
            logger.info(f"🔍 Email atual: {current_email}")
            
            if current_email in users_data['email'].values:
                user_row = users_data[users_data['email'] == current_email]
                logger.info(f"✅ Usuário encontrado: {user_row.iloc[0].to_dict()}")
            else:
                logger.warning(f"❌ Email {current_email} não encontrado na tabela")
        else:
            logger.warning("❌ Tabela de usuários está vazia")
            
    except Exception as e:
        logger.error(f"❌ Erro no debug: {e}")

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
    
    # DEBUG: Verifica dados diretamente no Supabase
    debug_user_lookup()
    
    logger.info(f"🔍 Buscando usuário: {user_email}")
    users_df = get_users_data()
    
    if users_df.empty:
        logger.warning("❌ Tabela de usuários está vazia")
        return None
    
    logger.info(f"📊 Total de usuários encontrados: {len(users_df)}")
    logger.info(f"📧 Emails na tabela: {users_df['email'].tolist() if 'email' in users_df.columns else 'Coluna email não encontrada'}")
    
    user_entry = users_df[users_df['email'] == user_email]
    
    if user_entry.empty:
        logger.warning(f"❌ Usuário {user_email} não encontrado na tabela")
        return None
    
    logger.info(f"✅ Usuário encontrado: {user_entry.iloc[0].to_dict()}")
    return user_entry.iloc[0].to_dict()


def get_user_id() -> int:
    """
    Retorna o ID (INTEGER) do usuário logado.
    
    Returns:
        int: ID do usuário ou None se não encontrado
    """
    user_info = get_user_info()
    
    if not user_info:
        logger.warning("Não foi possível obter informações do usuário")
        return None
    
    user_id = user_info.get('id')
    
    if not user_id:
        logger.error(f"Usuário {user_info.get('email')} não possui ID na tabela usuarios!")
        return None
    
    # Garante que retorna um inteiro
    try:
        return int(user_id)
    except (ValueError, TypeError):
        logger.error(f"ID do usuário não é um número válido: {user_id}")
        return None


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
    user_id = user_info.get('id')
    user_email = user_info.get('email')
    
    # Valida que o usuário tem ID
    if not user_id:
        st.sidebar.error("❌ Usuário sem ID no banco de dados.")
        logger.error(f"Usuário {user_email} não possui ID!")
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
