from config.page_config import set_page_config
from utils.auditoria import log_action
from auth.login_page import show_login_page, show_user_header, show_logout_button
from auth.auth_utils import (
    is_user_logged_in, setup_sidebar, get_user_email,
    get_effective_user_status, get_effective_user_plan, get_user_role,
    is_admin, is_superuser, get_user_info
)
import streamlit as st
from PIL import Image
import sys
import os

# Adiciona o diretório atual ao path para garantir que os módulos sejam encontrados
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from views import administracao, dashboard, resumo_gerencial, inspecao_extintores, \
                  inspecao_mangueiras, inspecao_scba, inspecao_chuveiros, \
                  inspecao_camaras_espuma, inspecao_multigas, historico, inspecao_alarmes, \
                  utilitarios, demo_page, trial_expired_page, inspecao_canhoes_monitores
from views import is_perfil_available

set_page_config()

# Adiciona perfil apenas se disponível
PERFIL_DISPONIVEL = is_perfil_available()
if PERFIL_DISPONIVEL:
    from views import perfil_usuario


def get_navigation_pages():
    """Cria a estrutura de navegação baseada nas permissões do usuário"""
    user_role = get_user_role()
    user_plan = get_effective_user_plan()
    
    # Páginas base
    pages = {}
    
    # Grupo: Dashboard e Relatórios
    dashboard_pages = []
    if user_plan in ['pro', 'premium_ia'] and user_role != 'viewer':
        dashboard_pages.append(st.Page("pages/01_Dashboard.py", title="Dashboard"))
    dashboard_pages.append(st.Page("pages/02_Resumo_Gerencial.py", title="Resumo Gerencial"))
    
    if dashboard_pages:
        pages["📊 Dashboard e Relatórios"] = dashboard_pages
    
    # Grupo: Inspeções
    inspection_pages = []
    if user_plan in ['pro', 'premium_ia'] and user_role != 'viewer':
        inspection_pages.extend([
            st.Page("pages/03_Extintores.py", title="Extintores"),
            st.Page("pages/04_Mangueiras.py", title="Mangueiras"),
            st.Page("pages/05_SCBA.py", title="SCBA"),
            st.Page("pages/06_Chuveiros_LO.py", title="Chuveiros/LO"),
            st.Page("pages/07_Camaras_Espuma.py", title="Câmaras de Espuma"),
            st.Page("pages/08_Multigas.py", title="Multigás"),
            st.Page("pages/09_Alarmes.py", title="Alarmes"),
            st.Page("pages/10_Canhoes_Monitores.py", title="Canhões Monitores")
        ])
    
    if inspection_pages:
        pages["🔍 Inspeções"] = inspection_pages
    
    # Grupo: Histórico e Utilitários
    utility_pages = []
    if user_plan in ['pro', 'premium_ia']:
        utility_pages.append(st.Page("pages/11_Historico_Logs.py", title="Histórico e Logs"))
    if user_plan in ['pro', 'premium_ia'] and user_role != 'viewer':
        utility_pages.append(st.Page("pages/12_Utilitarios.py", title="Utilitários"))
    
    if utility_pages:
        pages["⚙️ Histórico e Utilitários"] = utility_pages
    
    # Grupo: Perfil e Administração
    admin_pages = []
    if PERFIL_DISPONIVEL:
        admin_pages.append(st.Page("pages/13_Meu_Perfil.py", title="Meu Perfil"))
    if is_admin():
        admin_pages.append(st.Page("pages/14_Super_Admin.py", title="Super Admin"))
    
    if admin_pages:
        pages["👤 Perfil e Administração"] = admin_pages
    
    return pages

def main():
    """Função principal do aplicativo"""
    try:
        # Verifica se o usuário está logado
        if not is_user_logged_in():
            show_login_page()
            st.stop()

        # Log de login (apenas uma vez por sessão)
        if 'user_logged_in' not in st.session_state:
            user_email = get_user_email()
            log_action("LOGIN_SUCCESS", f"Email: {user_email}")

            if is_superuser():
                log_action("SUPERUSER_LOGIN_SUCCESS", f"Email: {user_email}")

            st.session_state['user_logged_in'] = True

        # Carrega e armazena os dados do usuário na sessão APENAS UMA VEZ
        if 'user_data' not in st.session_state:
            with st.spinner("Carregando perfil e permissões..."):
                user_info = get_user_info()
                if user_info is None:
                    st.session_state.user_data = {
                        'email': get_user_email(),
                        'status': 'not_in_database'
                    }
                else:
                    st.session_state.user_data = user_info

        user_email = st.session_state.user_data.get('email')

        # Lógica de autorização simplificada
        is_authorized = False

        if user_email is not None:
            if is_superuser():
                is_authorized = True
            elif st.session_state.user_data.get('status') != 'not_in_database':
                is_authorized = True
            else:
                is_authorized = False

        # Só registra ACCESS_DENIED_UNAUTHORIZED se realmente não autorizado
        if not is_authorized:
            if 'unauthorized_logged' not in st.session_state:
                log_action("ACCESS_DENIED_UNAUTHORIZED",
                           f"Tentativa de acesso pelo email: {user_email}")
                st.session_state['unauthorized_logged'] = True

            show_user_header()
            demo_page.show_page()
            st.stop()

        effective_status = get_effective_user_status()

        # Usuário com trial expirado
        if effective_status == 'trial_expirado':
            if 'trial_expired_logged' not in st.session_state:
                log_action("ACCESS_DENIED_TRIAL_EXPIRED",
                           f"Usuário: {user_email}")
                st.session_state['trial_expired_logged'] = True

            show_user_header()
            trial_expired_page.show_page()
            st.stop()

        # Usuário inativo (exceto admins)
        if effective_status == 'inativo' and not is_admin():
            if 'inactive_logged' not in st.session_state:
                log_action("ACCESS_DENIED_INACTIVE_ACCOUNT",
                           f"Usuário: {user_email}")
                st.session_state['inactive_logged'] = True

            show_user_header()
            st.warning(
                "🔒 Sua conta está atualmente inativa. Por favor, entre em contato com o suporte para reativá-la.")
            show_logout_button()
            st.stop()

        # Mostra cabeçalho do usuário
        show_user_header()

        # Configura sidebar e verifica se o ambiente foi carregado
        is_user_environment_loaded = setup_sidebar()

        # Configura sidebar com logo e logout
        with st.sidebar:
            # === LOGO NO TOPO DA SIDEBAR ===
            try:
                logo_path = os.path.join(os.path.dirname(
                    __file__), 'assets', 'logo.png')
                logo = Image.open(logo_path)

                # Redimensiona
                max_width = 180
                ratio = max_width / logo.width
                new_height = int(logo.height * ratio)
                logo_resized = logo.resize((max_width, new_height))

                # Centraliza com colunas
                col1, col2, col3 = st.columns([1, 3, 1])
                with col2:
                    st.image(logo_resized, width='content')
            except FileNotFoundError:
                pass
            except Exception as e:
                st.caption(f"Erro ao carregar logo: {e}")

            st.markdown("---")
            show_logout_button()

        # Verifica se o ambiente foi carregado
        if not is_user_environment_loaded and not is_admin():
            st.warning("👈 Seu ambiente de dados não pôde ser carregado. Verifique o status da sua conta ou contate o administrador.")
            st.stop()

        # Cria e executa a navegação
        pages = get_navigation_pages()
        
        if not pages:
            st.error("Nenhuma página disponível para seu perfil.")
            st.stop()
        
        # Executa a navegação
        pg = st.navigation(pages, position="top")
        pg.run()

    except Exception as e:
        st.error(f"Erro crítico na aplicação: {e}")
        st.error("Entre em contato com o suporte técnico.")
        st.stop()


if __name__ == "__main__":
    main()
