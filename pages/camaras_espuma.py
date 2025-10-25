import streamlit as st
import sys
import os

# Adiciona o diretório pai ao path para importar os módulos
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from views.inspecao_camaras_espuma import show_page

# Função que será chamada pelo st.navigation
def show_camaras_espuma():
    from views.inspecao_camaras_espuma import show_page as camaras_espuma_show_page
    camaras_espuma_show_page()
