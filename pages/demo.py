import streamlit as st
import sys
import os

# Adiciona o diretório pai ao path para importar os módulos
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from views.demo_page import show_page

# Função que será chamada pelo st.navigation
def show_page():
    from views.demo_page import show_page as demo_show_page
    demo_show_page()
