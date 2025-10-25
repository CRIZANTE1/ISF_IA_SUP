from supabase_local import get_supabase_client
import pandas as pd
import streamlit as st

@st.cache_data(ttl=300)
def load_sheet_data(table_name: str) -> pd.DataFrame:
    """
    Carrega dados de uma tabela do Supabase e retorna como DataFrame.
    
    Args:
        table_name: Nome da tabela no Supabase
        
    Returns:
        DataFrame com os dados da tabela
    """
    try:
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"🔄 Carregando dados da tabela '{table_name}'...")
        db_client = get_supabase_client()
        data = db_client.get_data(table_name)
        
        if data is not None and not data.empty:
            logger.info(f"✅ Dados carregados: {len(data)} registros da tabela '{table_name}'")
            return pd.DataFrame(data)
        else:
            logger.warning(f"⚠️ Tabela '{table_name}' retornou dados vazios")
            return pd.DataFrame()
            
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"❌ Erro ao carregar dados da tabela '{table_name}': {e}")
        st.error(f"Erro ao carregar dados da tabela '{table_name}': {e}")
        return pd.DataFrame()


def find_last_record(df: pd.DataFrame, equipment_id: str, id_column: str) -> dict:
    """
    Encontra o último registro de um equipamento específico.
    
    Args:
        df: DataFrame com os dados
        equipment_id: ID do equipamento a buscar
        id_column: Nome da coluna que contém o ID
        
    Returns:
        Dicionário com os dados do último registro ou None
    """
    if df.empty:
        return None
    
    # Filtra pelo ID do equipamento
    equipment_df = df[df[id_column] == equipment_id]
    
    if equipment_df.empty:
        return None
    
    # Ordena por data (assumindo que existe uma coluna de data)
    date_columns = [col for col in equipment_df.columns if 'data' in col.lower()]
    
    if date_columns:
        equipment_df = equipment_df.sort_values(by=date_columns[0], ascending=False)
    
    # Retorna o último registro como dicionário
    return equipment_df.iloc[0].to_dict()
