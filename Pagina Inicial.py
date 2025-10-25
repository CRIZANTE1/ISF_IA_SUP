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

# Importações das páginas
import pages.dashboard as dashboard_page
import pages.resumo_gerencial as resumo_gerencial_page
import pages.extintores as extintores_page
import pages.mangueiras as mangueiras_page
import pages.scba as scba_page
import pages.chuveiros_lo as chuveiros_page
import pages.camaras_espuma as camaras_espuma_page
import pages.multigas as multigas_page
import pages.historico_logs as historico_page
import pages.alarmes as alarmes_page
import pages.utilitarios as utilitarios_page
import pages.canhoes_monitores as canhoes_monitores_page
import pages.super_admin as administracao_page

# Importações das páginas especiais
import pages.demo as demo_page
import pages.trial_expired as trial_expired_page

# Função utilitária para verificar se o perfil está disponível
def is_perfil_available():
    """Verifica se o módulo perfil_usuario está disponível"""
    try:
        from views import perfil_usuario
        return True
    except ImportError:
        return False

set_page_config()

# Adiciona perfil apenas se disponível
PERFIL_DISPONIVEL = is_perfil_available()
if PERFIL_DISPONIVEL:
    from views import perfil_usuario


def create_page_function(page_module, title):
    """Cria uma função que executa uma página importada"""
    def page_wrapper():
        try:
            # Executa a página importada
            page_module.show_page()
        except Exception as e:
            st.error(f"Erro ao carregar a página {title}: {e}")
    
    # Renomeia a função para ter um nome único baseado no título
    page_wrapper.__name__ = f"page_{title.lower().replace(' ', '_').replace('/', '_')}"
    return page_wrapper

def get_navigation_pages():
    """Cria a estrutura de navegação baseada nas permissões do usuário"""
    try:
        user_role = get_user_role()
        user_plan = get_effective_user_plan()
        
        # Páginas base
        pages = {}
        
        # Grupo: Dashboard e Relatórios
        dashboard_pages = []
        if user_plan in ['pro', 'premium_ia'] and user_role != 'viewer':
            dashboard_pages.append(st.Page(
                create_page_function(dashboard_page, "Dashboard"),
                title="Dashboard"
            ))
        dashboard_pages.append(st.Page(
            create_page_function(resumo_gerencial_page, "Resumo Gerencial"),
            title="Resumo Gerencial"
        ))
        
        if dashboard_pages:
            pages["📊 Dashboard e Relatórios"] = dashboard_pages
        
        # Grupo: Inspeções
        inspection_pages = []
        if user_plan in ['pro', 'premium_ia'] and user_role != 'viewer':
            inspection_pages.extend([
                st.Page(create_page_function(extintores_page, "Extintores"), title="Extintores"),
                st.Page(create_page_function(mangueiras_page, "Mangueiras"), title="Mangueiras"),
                st.Page(create_page_function(scba_page, "SCBA"), title="SCBA"),
                st.Page(create_page_function(chuveiros_page, "Chuveiros/LO"), title="Chuveiros/LO"),
                st.Page(create_page_function(camaras_espuma_page, "Câmaras de Espuma"), title="Câmaras de Espuma"),
                st.Page(create_page_function(multigas_page, "Multigás"), title="Multigás"),
                st.Page(create_page_function(alarmes_page, "Alarmes"), title="Alarmes"),
                st.Page(create_page_function(canhoes_monitores_page, "Canhões Monitores"), title="Canhões Monitores")
            ])
        
        if inspection_pages:
            pages["🔍 Inspeções"] = inspection_pages
        
        # Grupo: Histórico e Utilitários
        utility_pages = []
        if user_plan in ['pro', 'premium_ia']:
            utility_pages.append(st.Page(
                create_page_function(historico_page, "Histórico e Logs"),
                title="Histórico e Logs"
            ))
        if user_plan in ['pro', 'premium_ia'] and user_role != 'viewer':
            utility_pages.append(st.Page(
                create_page_function(utilitarios_page, "Utilitários"),
                title="Utilitários"
            ))
        
        if utility_pages:
            pages["⚙️ Histórico e Utilitários"] = utility_pages
        
        # Grupo: Perfil e Administração
        admin_pages = []
        if PERFIL_DISPONIVEL:
            admin_pages.append(st.Page(
                create_page_function(perfil_usuario, "Meu Perfil"),
                title="Meu Perfil"
            ))
        if is_admin():
            admin_pages.append(st.Page(
                create_page_function(administracao_page, "Super Admin"),
                title="Super Admin"
            ))
        
        if admin_pages:
            pages["👤 Perfil e Administração"] = admin_pages
        
        return pages
        
    except Exception as e:
        st.error(f"Erro ao obter informações do usuário: {e}")
        # Retorna páginas básicas em caso de erro
        return {
            "📊 Dashboard e Relatórios": [
                st.Page(
                    create_page_function(resumo_gerencial_page, "Resumo Gerencial"),
                    title="Resumo Gerencial"
                )
            ]
        }

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
        try:
            pg = st.navigation(pages, position="top")
            pg.run()
        except Exception as nav_error:
            st.error(f"Erro na navegação: {nav_error}")
            st.write("Páginas disponíveis:", pages)
            # Fallback: mostra páginas simples
            st.write("Tentando fallback...")
            for group_name, group_pages in pages.items():
                st.write(f"**{group_name}**")
                for page in group_pages:
                    st.write(f"- {page.title}")
            st.stop()

    except Exception as e:
        st.error(f"Erro crítico na aplicação: {e}")
        st.error("Entre em contato com o suporte técnico.")
        st.stop()


if __name__ == "__main__":
    main()
