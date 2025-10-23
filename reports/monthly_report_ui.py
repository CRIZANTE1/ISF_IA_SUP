from operations.history import load_sheet_data
import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os
import json
import base64
import requests
from streamlit_js_eval import streamlit_js_eval

# Adiciona o diretório raiz ao path para encontrar a pasta 'operations'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- FUNÇÃO PARA EMBUTIR IMAGENS ---


def get_image_as_base64(url):
    """Baixa uma imagem de uma URL e a converte para o formato base64."""
    if not isinstance(url, str) or not url.strip() or 'drive.google.com' not in url:
        return None
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        b64_string = base64.b64encode(response.content).decode()
        # Determina o tipo de imagem (assumindo jpeg como padrão)
        content_type = response.headers.get('Content-Type', 'image/jpeg')
        return f"data:{content_type};base64,{b64_string}"
    except requests.exceptions.RequestException:
        # Retorna o link original como fallback se o download falhar
        return url


def generate_report_html(df_inspections_month, df_action_log, df_locais, month, year):
    """Gera o conteúdo do relatório como uma string HTML pura."""

    styles = """
    <style>
        @media print { body { -webkit-print-color-adjust: exact; } }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji"; color: #333; }
        .report-header { text-align: center; border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 20px; }
        .inspection-item { border: 1px solid #ccc; border-radius: 8px; padding: 15px; margin-bottom: 20px; page-break-inside: avoid; }
        .item-header { font-size: 1.2em; font-weight: bold; }
        .status-ok { color: #28a745; }
        .status-fail { color: #dc3545; }
        .details-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin: 15px 0; }
        .metric { background-color: #f0f2f6; padding: 10px; border-radius: 5px; text-align: center; }
        .metric-label { font-size: 0.9em; color: #555; display: block; }
        .metric-value { font-size: 1.1em; font-weight: bold; }
        .subsection-header { font-weight: bold; font-size: 1.1em; margin-top: 15px; border-top: 1px dashed #ddd; padding-top: 10px; }
        .evidence-img { max-width: 300px; height: auto; border: 1px solid #ddd; border-radius: 4px; display: block; margin-top: 10px; }
        a { color: #0068c9; text-decoration: none; }
        .pending { color: #ffc107; font-style: italic; }
        .success-text { color: #28a745; font-weight: bold; }
    </style>
    """

    html = f"<html><head><title>Relatório {month:02d}/{year}</title>{styles}</head><body>"
    html += f"<div class='report-header'><h1>Relatório de Inspeções de Extintores</h1><h2>Período: {month:02d}/{year}</h2></div>"

    if df_inspections_month.empty:
        html += "<p>Nenhum registro de inspeção de extintor encontrado para o período.</p>"
    else:
        if not df_action_log.empty:
            df_action_log['data_correcao_dt'] = pd.to_datetime(
                df_action_log['data_correcao'], errors='coerce')
        if not df_locais.empty:
            df_locais['id'] = df_locais['id'].astype(str)

        for _, inspection in df_inspections_month.iterrows():
            ext_id = inspection['numero_identificacao']

            # Busca o local do equipamento
            local_info = "Local não definido"
            if not df_locais.empty:
                local_row = df_locais[df_locais['id'] == str(ext_id)]
                if not local_row.empty:
                    local_info = local_row.iloc[0].get('local', local_info)

            is_ok = inspection.get('aprovado_inspecao') == "Sim"
            status_class = "status-ok" if is_ok else "status-fail"
            status_text = "Conforme" if is_ok else "Não Conforme"
            icon = "✅" if is_ok else "❌"
            obs = inspection.get('observacoes_gerais', '')
            photo_nc_link = inspection.get('link_foto_nao_conformidade')
            inspection_date = pd.to_datetime(inspection['data_servico'])

            html += f"""
            <div class='inspection-item'>
                <div class='item-header {status_class}'>{icon} Equipamento ID: {ext_id}</div>
                <div class='details-grid'>
                    <div class='metric'><div class='metric-label'>Data da Inspeção</div><div class='metric-value'>{inspection_date.strftime('%d/%m/%Y')}</div></div>
                    <div class='metric'><div class='metric-label'>Status</div><div class='metric-value'>{status_text}</div></div>
                    <div class='metric'><div class='metric-label'>Local</div><div class='metric-value'>{local_info}</div></div>
                </div>
                <p><b>Observações:</b> {obs}</p>
            """

            if not is_ok:
                html += "<div class='subsection-header'>Evidência da Não Conformidade</div>"
                if pd.notna(photo_nc_link):
                    base64_image = get_image_as_base64(photo_nc_link)
                    if base64_image:
                        html += f"<img src='{base64_image}' class='evidence-img' alt='Foto da Não Conformidade'>"
                    else:
                        html += f"<p>Falha ao carregar imagem. <a href='{photo_nc_link}' target='_blank'>Abrir link da foto</a></p>"
                else:
                    html += "<p>Nenhuma foto de não conformidade foi anexada.</p>"

                html += "<div class='subsection-header'>Ação Corretiva</div>"
                action_info = "<p class='pending'>Ação Corretiva Pendente.</p>"
                if not df_action_log.empty:
                    action = df_action_log[(df_action_log['id_equipamento'].astype(str) == str(ext_id)) & (
                        df_action_log['data_correcao_dt'] >= inspection_date)].sort_values(by='data_correcao_dt')
                    if not action.empty:
                        action_taken = action.iloc[0]
                        action_photo_link = action_taken.get(
                            'link_foto_evidencia')
                        action_info = "<p class='success-text'>Ação Corretiva Registrada:</p>"
                        action_info += f"""
                        <p><b>Ação Realizada:</b> {action_taken.get('acao_realizada', 'N/A')}</p>
                        <p><b>Responsável:</b> {action_taken.get('responsavel_acao', 'N/A')}</p>
                        <p><b>Data da Correção:</b> {pd.to_datetime(action_taken['data_correcao_dt']).strftime('%d/%m/%Y')}</p>
                        """
                        if pd.notna(action_photo_link):
                            base64_action_image = get_image_as_base64(
                                action_photo_link)
                            if base64_action_image:
                                action_info += f"<img src='{base64_action_image}' class='evidence-img' alt='Foto da Ação Corretiva'>"
                            else:
                                action_info += f"<p>Falha ao carregar imagem. <a href='{action_photo_link}' target='_blank'>Abrir link da evidência</a></p>"
                        else:
                            action_info += "<p>Nenhuma foto da ação corretiva anexada.</p>"
                html += action_info

            html += "</div>"

    html += "</body></html>"
    return html


def show_monthly_report_interface():
    st.title("📄 Emissão de Relatórios Mensais")

    today = datetime.now()
    col1, col2 = st.columns(2)
    with col1:
        st.selectbox("Selecione o Ano:", range(
            today.year, today.year - 5, -1), key="report_year")
    with col2:
        months = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                  "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
        default_month_index = today.month - 2 if today.day < 5 else today.month - 1
        st.selectbox(
            "Selecione o Mês:", months, index=default_month_index, key="report_month_name")

    if st.button("Gerar e Imprimir Relatório", type="primary", key="generate_report_btn"):
        year = st.session_state.report_year
        month_name = st.session_state.report_month_name
        month = months.index(month_name) + 1

        with st.spinner(f"Gerando relatório para {month:02d}/{year}..."):
            df_inspections = load_sheet_data("extintores")
            df_action_log = load_sheet_data("log_acoes")
            df_locais = load_sheet_data("locais")  # Carrega os dados de locais

            if not df_inspections.empty:
                df_inspections['data_servico'] = pd.to_datetime(
                    df_inspections['data_servico'], errors='coerce')
                mask = (df_inspections['data_servico'].dt.year == year) & \
                       (df_inspections['data_servico'].dt.month == month) & \
                       (df_inspections['tipo_servico'] == 'Inspeção')
                df_inspections_month = df_inspections[mask].sort_values(
                    by='data_servico')
            else:
                df_inspections_month = pd.DataFrame()

            report_html = generate_report_html(
                df_inspections_month, df_action_log, df_locais, month, year)

            js_code = f"""
                const reportHtml = {json.dumps(report_html)};
                const printWindow = window.open('', '_blank');
                if (printWindow) {{
                    printWindow.document.write(reportHtml);
                    printWindow.document.close();
                    printWindow.focus();
                    setTimeout(() => {{ 
                        printWindow.print();
                        printWindow.close();
                    }}, 500);
                }} else {{
                    alert('Por favor, desabilite o bloqueador de pop-ups para este site para poder imprimir o relatório.');
                }}
            """

            streamlit_js_eval(js_expressions=js_code, key="print_report_js")
            st.success(
                "Relatório enviado para impressão. Verifique a nova aba ou janela que foi aberta.")
