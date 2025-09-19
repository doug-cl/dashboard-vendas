import streamlit as st
import pandas as pd
import calendar
import altair as alt
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import json
import duckdb
import os

# ===== CONFIGURAÇÃO DA PÁGINA =====
st.set_page_config(
    page_title="📊 Dashboard de Análise de Vendas",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===== CSS CUSTOMIZADO =====
st.markdown("""
<style>
    /* Importar fonte Google */
    @import url("https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap");
    /* Estilo geral */
    .main {
        font-family: 'Inter', sans-serif;
    }
    
    /* Header principal */
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .main-header h1 {
        margin: 0;
        font-weight: 700;
        font-size: 2.5rem;
    }
    
    .st-emotion-cache-121p54r {
        text-align: center;
        width: 100%;
    }
    
    .st-emotion-cache-1y4q738{
        text-align: center;
    }
    
    /* Botões personalizados */
    .stButton > button {
        background-color: #764ba2;
        color: white;
        border-radius: 5px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 600;
    }
    .stButton > button:hover {
        background-color: #667eea;
    }
    
    /* Métricas */
    .metric-box {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        text-align: center;
    }
    
    /* Gráficos */
    .block-container {
        padding-top: 2rem;
    }
    
</style>
""", unsafe_allow_html=True)


# ===== CONEXÃO COM O BANCO DE DADOS DUCKDB =====
@st.cache_resource
def get_duckdb_con():
    """Conecta ao banco de dados DuckDB."""
    return duckdb.connect("dashboard_dados.duckdb")

def load_data_from_duckdb():
    """Carrega os dados da tabela 'vendas' do DuckDB, se ela existir."""
    con = get_duckdb_con()
    table_exists = con.execute("SELECT count(*) FROM information_schema.tables WHERE table_name = 'vendas'").fetchone()[0]
    if table_exists > 0:
        return con.execute("SELECT * FROM vendas").df()
    return None

def save_data_to_duckdb(df):
    """Salva um DataFrame no banco de dados DuckDB, sobrescrevendo a tabela 'vendas'."""
    con = get_duckdb_con()
    con.execute("CREATE OR REPLACE TABLE vendas AS SELECT * FROM df")

# Tenta carregar os dados persistidos do DuckDB
df = load_data_from_duckdb()

# ===== INTERFACE E LÓGICA DO APLICATIVO =====
st.markdown("""
<div class="main-header">
    <h1>📊 Dashboard de Análise de Vendas</h1>
    <p>Visualize métricas, tendências e informações de vendas em tempo real.</p>
</div>
""", unsafe_allow_html=True)

if df is None:
    uploaded_file = st.file_uploader(
        "Faça o upload do seu arquivo de vendas (CSV ou Excel)",
        type=["csv", "xls", "xlsx"],
    )
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file, sep=";")
            else:
                df = pd.read_excel(uploaded_file)
            
            # Remove linhas e colunas vazias
            df.dropna(how='all', axis=0, inplace=True)
            df.dropna(how='all', axis=1, inplace=True)
            
            # Salva o DataFrame no DuckDB
            save_data_to_duckdb(df)
            st.success("✅ Arquivo processado e dados salvos com sucesso!")
            st.info("🔄 Recarregando o aplicativo...")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Ocorreu um erro ao processar o arquivo: {e}")
else:
    # --- PRÉ-PROCESSAMENTO DO DATAFRAME ---
    # Convertendo colunas para o tipo correto (se necessário)
    df.columns = df.columns.str.strip()
    
    # Tentando encontrar a coluna de data
    date_column = None
    for col in df.columns:
        # Lógica para detectar colunas de data
        if 'data' in col.lower() or 'date' in col.lower():
            try:
                # Tenta converter para o formato de data. Se falhar, não é uma coluna de data
                df[col] = pd.to_datetime(df[col], errors='coerce', dayfirst=True)
                # Remove linhas onde a conversão falhou (valores inválidos)
                df.dropna(subset=[col], inplace=True)
                date_column = col
                break
            except Exception:
                pass
    
    if date_column:
        df['Ano'] = df[date_column].dt.year
        df['Mês'] = df[date_column].dt.month
        df['Dia da Semana'] = df[date_column].dt.day_name(locale='pt_BR')
        
        # Mapeando os dias da semana para português
        dias_semana = {
            'Monday': 'Segunda-feira',
            'Tuesday': 'Terça-feira',
            'Wednesday': 'Quarta-feira',
            'Thursday': 'Quinta-feira',
            'Friday': 'Sexta-feira',
            'Saturday': 'Sábado',
            'Sunday': 'Domingo'
        }
        df['Dia da Semana'] = df['Dia da Semana'].map(dias_semana)

    # --- SIDEBAR E FILTROS ---
    st.sidebar.markdown("## ⚙️ Configurações e Filtros")
    st.sidebar.markdown("---")
    
    colunas_numericas = df.select_dtypes(include=['number']).columns.tolist()
    colunas_categoricas = df.select_dtypes(include=['object']).columns.tolist()
    
    # Seletor de colunas
    colunas_visuais = st.sidebar.multiselect(
        "Selecione as colunas para a análise visual:",
        options=df.columns.tolist(),
        default=df.columns.tolist()
    )
    
    df_filtrado = df[colunas_visuais]

    # --- ANÁLISE GERAL ---
    st.header("Análise Geral")
    
    if not df_filtrado.empty:
        # Visão Geral das Métricas
        with st.container():
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown('<div class="metric-box">', unsafe_allow_html=True)
                st.metric("Total de Linhas", len(df_filtrado))
                st.markdown('</div>', unsafe_allow_html=True)
            with col2:
                if colunas_numericas:
                    st.markdown('<div class="metric-box">', unsafe_allow_html=True)
                    col_soma = st.selectbox("Somar qual coluna?", options=colunas_numericas)
                    total = df_filtrado[col_soma].sum() if col_soma else "N/A"
                    st.metric(f"Total de {col_soma}", f"{total:,.2f}")
                    st.markdown('</div>', unsafe_allow_html=True)
            with col3:
                if colunas_categoricas:
                    st.markdown('<div class="metric-box">', unsafe_allow_html=True)
                    col_contagem = st.selectbox("Contar valores de qual coluna?", options=colunas_categoricas)
                    contagem = df_filtrado[col_contagem].nunique() if col_contagem else "N/A"
                    st.metric(f"Total de {col_contagem}", contagem)
                    st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # --- GRÁFICOS INTERATIVOS ---
        st.header("Gráficos de Análise")
        tab1, tab2, tab3 = st.tabs(["Distribuição de Dados", "Análise de Tendência", "Outros Gráficos"])
        
        with tab1:
            st.subheader("Distribuição de Dados")
            if colunas_numericas and colunas_categoricas:
                col_x_dist = st.selectbox("Eixo X", options=colunas_categoricas, key="x_dist")
                col_y_dist = st.selectbox("Eixo Y", options=colunas_numericas, key="y_dist")
                
                if col_x_dist and col_y_dist:
                    fig_bar = px.bar(df_filtrado, x=col_x_dist, y=col_y_dist, 
                                     title=f"Soma de {col_y_dist} por {col_x_dist}")
                    st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.warning("⚠️ Dados numéricos e categóricos são necessários para este gráfico.")
        
        with tab2:
            st.subheader("Análise de Tendência ao Longo do Tempo")
            if date_column and colunas_numericas:
                col_y_tendencia = st.selectbox("Selecione a coluna para a tendência:", options=colunas_numericas)
                
                if col_y_tendencia:
                    df_tendencia = df_filtrado.set_index(date_column).resample('M')[col_y_tendencia].sum().reset_index()
                    df_tendencia.columns = ['Data', 'Soma']
                    
                    fig_line = px.line(df_tendencia, x='Data', y='Soma', title=f"Tendência de {col_y_tendencia} por Mês")
                    st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.warning("⚠️ Uma coluna de data e colunas numéricas são necessárias para este gráfico.")
        
        with tab3:
            st.subheader("Gráficos Adicionais")
            if colunas_numericas and colunas_categoricas:
                col_x_pizza = st.selectbox("Colunas Categóricas", options=colunas_categoricas, key="x_pizza")
                col_y_pizza = st.selectbox("Colunas Numéricas", options=colunas_numericas, key="y_pizza")
                
                if col_x_pizza and col_y_pizza:
                    fig_pie = px.pie(df_filtrado, names=col_x_pizza, values=col_y_pizza, title=f"Distribuição de {col_y_pizza} por {col_x_pizza}")
                    st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.warning("⚠️ Dados numéricos e categóricos são necessários para este gráfico.")

        # Exibir o DataFrame
        st.markdown("---")
        st.header("Tabela de Dados")
        st.markdown("Visualize a tabela completa dos dados processados.")
        st.dataframe(
            df_filtrado,
            hide_index=True,
            use_container_width=True
        )
    else:
        st.warning("⚠️ Por favor, selecione pelo menos uma coluna para visualizar.")
else:
    # Mensagem quando não há arquivo carregado
    st.markdown("""
    <div style="text-align: center; padding: 3rem; color: #666;">
        <h3>👆 Faça o upload de um arquivo para começar a análise</h3>
        <p>Suportamos arquivos CSV e Excel com dados de vendas</p>
        <p>Os dados serão consolidados e persistidos para futuras análises.</p>
    </div>
    """, unsafe_allow_html=True)

# ===== FOOTER =====
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>📊 Dashboard de Análise de Vendas | Desenvolvido com Streamlit</p>
    <p><small>Versão 2.1 - Com Persistência de Dados</small></p>
</div>
""", unsafe_allow_html=True)

# ===== GERENCIAMENTO DE DADOS (SIDEBAR) =====
st.sidebar.markdown("---")
st.sidebar.markdown("## 🗑️ Gerenciamento de Dados")

if st.sidebar.button("Limpar Todos os Dados Consolidados"):
    try:
        os.remove("dashboard_dados.duckdb")
        st.sidebar.success("✅ Dados consolidados limpos com sucesso!")
        st.rerun()
    except FileNotFoundError:
        st.sidebar.info("Nenhum dado consolidado para limpar.")
