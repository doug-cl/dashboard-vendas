import streamlit as st
import pandas as pd
import calendar
import altair as alt
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap' );
    
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
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .main-header p {
        font-size: 1.1rem;
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
    }
    
    /* Cards de métricas */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        border-left: 4px solid #667eea;
        margin-bottom: 1rem;
        transition: transform 0.2s ease;
    }
    
    .metric-card h3 {
        color: #333333; /* Um cinza escuro para melhor contraste */
        font-size: 1rem;
        margin-top: 0;
        margin-bottom: 0.5rem;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
    }
    
    /* Seções */
    .section-header {
        background: linear-gradient(90deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        margin: 2rem 0 1rem 0;
        font-weight: 600;
        font-size: 1.2rem;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background-color: #f8f9fa;
    }
    
    /* Upload area */
    .upload-section {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        border: 2px dashed #667eea;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* Tabelas */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    /* Alertas customizados */
    .success-alert {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .warning-alert {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    /* Estatísticas rápidas */
    .stats-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ===== CONSTANTES E CONFIGURAÇÕES =====
DATA_FILE = "dados_consolidados.csv"

# ===== FUNÇÕES AUXILIARES =====

def carregar_dados_existentes():
    """
    Carrega o DataFrame consolidado de um arquivo CSV, se existir.
    """
    if os.path.exists(DATA_FILE):
        try:
            df_existente = pd.read_csv(DATA_FILE, decimal=",", encoding="utf-8")
            st.sidebar.success(f"✅ Dados existentes ({df_existente.shape[0]} linhas) carregados de {DATA_FILE}.")
            return df_existente
        except Exception as e:
            st.sidebar.error(f"❌ Erro ao carregar dados existentes: {str(e)}")
            return pd.DataFrame()
    return pd.DataFrame()

def salvar_dados(df):
    """
    Salva o DataFrame consolidado em um arquivo CSV.
    """
    try:
        df.to_csv(DATA_FILE, index=False, decimal=",", encoding="utf-8")
        st.sidebar.success(f"💾 Dados salvos com sucesso em {DATA_FILE}.")
    except Exception as e:
        st.sidebar.error(f"❌ Erro ao salvar dados: {str(e)}")

def processar_arquivo(uploaded_file):
    """
    Função para ler o arquivo e criar um DataFrame do Pandas.
    Suporta .csv, .xlsx e .xls com tratamento de erros aprimorado.
    """
    try:
        file_extension = uploaded_file.name.split(".")[-1].lower()
        
        progress_bar = st.progress(0)
        progress_bar.progress(25)
        
        if file_extension == "csv":
            df = pd.read_csv(uploaded_file, decimal=",", encoding="utf-8")
        elif file_extension in ["xlsx", "xls"]:
            df = pd.read_excel(uploaded_file, engine='openpyxl')
        else:
            st.error("❌ Formato de arquivo não suportado. Por favor, envie um arquivo .csv, .xlsx ou .xls.")
            return None
        
        progress_bar.progress(75)
        
        df.columns = df.columns.str.strip().str.lower()
        
        progress_bar.progress(100)
        progress_bar.empty()
        
        st.success(f"✅ Arquivo processado com sucesso! {df.shape[0]} linhas e {df.shape[1]} colunas carregadas.")
        
        return df

    except Exception as e:
        st.error(f"❌ Ocorreu um erro ao processar o arquivo: {str(e)}")
        return None

def formatar_numero(valor):
    """
    Função para formatar números no padrão brasileiro.
    """
    if pd.isna(valor) or not isinstance(valor, (int, float)):
        return str(valor)
    
    valor_str = f"{valor:,.2f}"
    valor_str = valor_str.replace(".", "TEMP").replace(",", ".").replace("TEMP", ",")
    return valor_str

def criar_grafico_pizza(df, coluna, titulo):
    """
    Cria um gráfico de pizza usando Plotly.
    """
    if coluna not in df.columns:
        return None
    
    dados = df[coluna].value_counts().head(10)
    
    fig = px.pie(
        values=dados.values,
        names=dados.index,
        title=titulo,
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(
        font=dict(size=12),
        showlegend=True,
        height=400
    )
    
    return fig

def criar_grafico_barras(df, x_col, y_col, titulo):
    """
    Cria um gráfico de barras usando Plotly.
    """
    if x_col not in df.columns or y_col not in df.columns:
        return None
    
    dados = df.groupby(x_col)[y_col].sum().reset_index()
    
    fig = px.bar(
        dados,
        x=x_col,
        y=y_col,
        title=titulo,
        color=y_col,
        color_continuous_scale=\'Viridis\'
    )
    
    fig.update_layout(
        xaxis_title=x_col.title(),
        yaxis_title=y_col.title(),
        font=dict(size=12),
        height=400
    )
    
    return fig

# ===== INTERFACE PRINCIPAL =====

# Header principal
st.markdown("""
<div class="main-header">
    <h1>📊 Dashboard de Análise de Vendas</h1>
    <p>Transforme seus dados em insights poderosos com visualizações interativas</p>
</div>
""", unsafe_allow_html=True)

# ===== UPLOAD DO ARQUIVO =====
st.markdown("""
<div class="section-header">📁 Upload do Arquivo de Dados</div>
""", unsafe_allow_html=True)

col_upload1, col_upload2, col_upload3 = st.columns([1, 2, 1])

with col_upload2:
    st.markdown("""
    <div class="upload-section">
        <h3>📤 Faça o upload do seu arquivo</h3>
        <p>Suportamos arquivos CSV, Excel (.xlsx) e Excel antigo (.xls)</p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Escolha um arquivo",
        type=["csv", "xlsx", "xls"],
        help="Arraste e solte seu arquivo aqui ou clique para selecionar",
        key="file_uploader_key"
    )

    if st.button("Limpar Upload Atual"):
        st.session_state["file_uploader_key"] = ""
        st.session_state.last_uploaded_file_hash = None # Limpa o hash para permitir novo upload
        st.rerun()

# Carregar dados existentes ou inicializar DataFrame na session_state
if "df_consolidado" not in st.session_state:
    st.session_state.df_consolidado = carregar_dados_existentes()

# Processar o arquivo carregado apenas se houver um e ele ainda não foi processado
if uploaded_file is not None:
    # Usar um hash do arquivo para verificar se já foi processado nesta sessão
    file_hash = hash(uploaded_file.getvalue())
    if "last_uploaded_file_hash" not in st.session_state or st.session_state.last_uploaded_file_hash != file_hash:
        novo_df = processar_arquivo(uploaded_file)
        
        if novo_df is not None:
            # Concatenar com dados existentes
            if not st.session_state.df_consolidado.empty:
                common_cols = list(set(st.session_state.df_consolidado.columns) & set(novo_df.columns))
                if common_cols:
                    st.session_state.df_consolidado = pd.concat([st.session_state.df_consolidado[common_cols], novo_df[common_cols]], ignore_index=True)
                else:
                    st.sidebar.warning("⚠️ As colunas do novo arquivo não são compatíveis com os dados existentes. O novo arquivo não foi adicionado.")
            else:
                st.session_state.df_consolidado = novo_df
            
            salvar_dados(st.session_state.df_consolidado)
            st.session_state.last_uploaded_file_hash = file_hash # Armazena o hash do arquivo processado
            st.success("✅ Arquivo carregado e dados consolidados com sucesso! Atualizando dashboard...")
            st.rerun()
    else:
        # Se uploaded_file é None e last_uploaded_file_hash existe, significa que o widget foi limpo
        # ou a página foi recarregada sem um novo upload. Resetar o hash para permitir novo upload.
        if "last_uploaded_file_hash" in st.session_state:
            del st.session_state.last_uploaded_file_hash

# O DataFrame \'df\' usado no restante do script deve sempre refletir o estado atual de df_consolidado
df = st.session_state.df_consolidado


if not df.empty:
    # ===== DEFINIÇÃO DAS COLUNAS =====
    COLUMN_DATA = \'data\'
    COLUMN_VALOR_TOTAL = \'valor total\'
    COLUMN_QUANTIDADE = \'quantidade\'
    COLUMN_TAXA = \'taxa\'
    COLUMN_RENDA_ESTIMADA = \'renda estimada\'
    COLUMN_SUBTOTAL_PRODUTO = \'subtotal do produto\'
    COLUMN_TAMANHO = \'tamanho\'
    COLUMN_PRODUTO = \'produto\'
    COLUMN_TIPO = \'tipo\'
    COLUMN_STATUS = \'status\'
    COLUMN_DEVOLUCAO = \'quantidade devolução\'
    COLUMN_UF = \'uf\'
    
    # ===== PROCESSAMENTO DOS DADOS =====
    
    # Conversão de colunas numéricas
    colunas_numericas = [COLUMN_VALOR_TOTAL, COLUMN_RENDA_ESTIMADA, COLUMN_SUBTOTAL_PRODUTO, COLUMN_TAXA, COLUMN_DEVOLUCAO]
    for col in colunas_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors=\'coerce\')
    
    # Processamento de datas
    if COLUMN_DATA in df.columns:
        try:
            df[COLUMN_DATA] = pd.to_datetime(df[COLUMN_DATA], format=\'%d/%m/%Y\', errors=\'coerce\')
            df.dropna(subset=[COLUMN_DATA], inplace=True)
            df[\'mês\'] = df[COLUMN_DATA].dt.month.apply(lambda x: calendar.month_name[x].capitalize())
            df[\'ano\'] = df[COLUMN_DATA].dt.year
        except Exception as e:
            st.warning(f"⚠️ Não foi possível converter a coluna \'{COLUMN_DATA}\' para o formato de data.")
    
    # ===== INFORMAÇÕES GERAIS =====
    st.markdown("""
    <div class="section-header">📋 Informações Gerais do Dataset</div>
    """, unsafe_allow_html=True)
    
    col_info1, col_info2, col_info3, col_info4 = st.columns(4)
    
    with col_info1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>📊 Total de Registros</h3>
            <h2 style="color: #667eea;">{df.shape[0]:,}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col_info2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>📈 Total de Colunas</h3>
            <h2 style="color: #667eea;">{df.shape[1]}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col_info3:
        if COLUMN_DATA in df.columns and not df[COLUMN_DATA].empty and not pd.isna(df[COLUMN_DATA].min()):
            min_date = df[COLUMN_DATA].min().strftime(\'%m/%Y\')
            max_date = df[COLUMN_DATA].max().strftime(\'%m/%Y\')
            st.markdown(f"""
            <div class="metric-card">
                <h3>📅 Período</h3>
                <h2 style="color: #667eea;">
                    {min_date} - {max_date}
                </h2>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="metric-card">
                <h3>📅 Período</h3>
                <h2 style="color: #667eea;">N/A</h2>
            </div>
            """, unsafe_allow_html=True)

    with col_info4:
        if os.path.exists(DATA_FILE):
            file_size_bytes = os.path.getsize(DATA_FILE)
            file_size_kb = file_size_bytes / 1024
        else:
            file_size_kb = 0

        st.markdown(f"""
        <div class="metric-card">
            <h3>💾 Tamanho do Arquivo</h3>
            <h2 style="color: #667eea;">{file_size_kb:.1f} KB</h2>
        </div>
        """, unsafe_allow_html=True)
    
    # ===== SIDEBAR DE FILTROS =====
    st.sidebar.markdown("## 🔍 Filtros Avançados")
    st.sidebar.markdown("---")
    
    # Filtro de mês
    if \'mês\' in df.columns:
        meses_en = [\'January\', \'February\', \'March\', \'April\', \'May\', \'June\', 
                   \'July\', \'August\', \'September\', \'October\', \'November\', \'December\']
        all_meses = sorted(df[\'mês\'].unique(), key=lambda x: meses_en.index(x))
        selected_mes = st.sidebar.selectbox("📅 Selecione o Mês:", ["Todos"] + all_meses)
    else:
        selected_mes = "Todos"
    
    # Filtro de tamanho
    if COLUMN_TAMANHO in df.columns:
        df[COLUMN_TAMANHO] = pd.to_numeric(df[COLUMN_TAMANHO], errors=\'coerce\').astype(\'Int64\')
        df[COLUMN_TAMANHO] = df[COLUMN_TAMANHO].astype(str).str.replace(\'<NA>\', \'NaN\')
        all_tamanhos = sorted(df[COLUMN_TAMANHO].unique())
        selected_tamanhos = st.sidebar.multiselect("📏 Selecione os Tamanhos:", all_tamanhos, default=all_tamanhos)
    else:
        selected_tamanhos = []
    
    # Filtro de produto
    if COLUMN_PRODUTO in df.columns:
        df[COLUMN_PRODUTO] = df[COLUMN_PRODUTO].astype(str)
        all_produtos = sorted(df[COLUMN_PRODUTO].unique())
        selected_produtos = st.sidebar.multiselect("🛍️ Selecione os Produtos:", all_produtos, default=all_produtos)
    else:
        selected_produtos = []
    
    # Filtro de status
    if COLUMN_STATUS in df.columns:
        df[COLUMN_STATUS] = df[COLUMN_STATUS].astype(str)
        all_status = sorted(df[COLUMN_STATUS].unique())
        selected_status = st.sidebar.multiselect("📊 Selecione o Status:", all_status, default=all_status)
    else:
        selected_status = []
    
    # Aplicar filtros
    df_filtrado = df.copy()
    if selected_mes != "Todos":
        df_filtrado = df_filtrado[df_filtrado[\'mês\'] == selected_mes]
    if selected_tamanhos:
        df_filtrado = df_filtrado[df_filtrado[COLUMN_TAMANHO].isin(selected_tamanhos)]
    if selected_produtos:
        df_filtrado = df_filtrado[df_filtrado[COLUMN_PRODUTO].isin(selected_produtos)]
    if selected_status:
        df_filtrado = df_filtrado[df_filtrado[COLUMN_STATUS].isin(selected_status)]
    
    # Estatísticas dos filtros
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"""
    <div class="stats-container">
        <h4>📊 Dados Filtrados</h4>
        <p><strong>Registros:</strong> {df_filtrado.shape[0]:,}</p>
        <p><strong>% do Total:</strong> {((df_filtrado.shape[0]/df.shape[0]*100) if df.shape[0] > 0 else 0.0):.1f}%</p>
    </div>
    """, unsafe_allow_html=True)
    
    # ===== PAINEL DE KPIs =====
    st.markdown("""
    <div class="section-header">💰 Indicadores Principais (KPIs)</div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if COLUMN_VALOR_TOTAL in df_filtrado.columns:
            valor_total = df_filtrado[COLUMN_VALOR_TOTAL].sum()
            st.metric(
                "💵 Valor Total",
                f"R$ {formatar_numero(valor_total)}",
                delta=f"{(valor_total/df[COLUMN_VALOR_TOTAL].sum()*100) if df[COLUMN_VALOR_TOTAL].sum() > 0 else 0.0:.1f}% do total"
            )
    
    with col2:
        if COLUMN_QUANTIDADE in df_filtrado.columns:
            qtd_total = int(df_filtrado[COLUMN_QUANTIDADE].sum())
            st.metric(
                "📦 Quantidade Total",
                f"{qtd_total:,}",
                delta=f"{(qtd_total/df[COLUMN_QUANTIDADE].sum()*100) if df[COLUMN_QUANTIDADE].sum() > 0 else 0.0:.1f}% do total"
            )
    
    with col3:
        if COLUMN_TAXA in df_filtrado.columns:
            taxa_total = df_filtrado[COLUMN_TAXA].sum()
            st.metric(
                "💳 Soma da Taxa",
                formatar_numero(taxa_total),
                delta=f"{(taxa_total/df[COLUMN_TAXA].sum()*100) if df[COLUMN_TAXA].sum() > 0 else 0.0:.1f}% do total"
            )
    
    with col4:
        if COLUMN_RENDA_ESTIMADA in df_filtrado.columns:
            renda_total = df_filtrado[COLUMN_RENDA_ESTIMADA].sum()
            st.metric(
                "💰 Renda Estimada",
                f"R$ {formatar_numero(renda_total)}",
                delta=f"{(renda_total/df[COLUMN_RENDA_ESTIMADA].sum()*100) if df[COLUMN_RENDA_ESTIMADA].sum() > 0 else 0.0:.1f}% do total"
            )
    
    with col5:
        if COLUMN_SUBTOTAL_PRODUTO in df_filtrado.columns:
            subtotal = df_filtrado[COLUMN_SUBTOTAL_PRODUTO].sum()
            st.metric(
                "🛒 Subtotal do Produto",
                f"R$ {formatar_numero(subtotal)}",
                delta=f"{(subtotal/df[COLUMN_SUBTOTAL_PRODUTO].sum()*100) if df[COLUMN_SUBTOTAL_PRODUTO].sum() > 0 else 0.0:.1f}% do total"
            )
    
    # ===== ANÁLISES VISUAIS =====
    st.markdown("""
    <div class="section-header">📊 Análises Visuais Interativas</div>
    """, unsafe_allow_html=True)
    
    # Gráficos em duas colunas
    col_graf1, col_graf2 = st.columns(2)
    
    with col_graf1:
        st.subheader("📈 Vendas por Mês")
        if \'mês\' in df_filtrado.columns and COLUMN_VALOR_TOTAL in df_filtrado.columns:
            fig_mes = criar_grafico_barras(df_filtrado, \'mês\', COLUMN_VALOR_TOTAL, "Vendas por Mês")
            if fig_mes:
                st.plotly_chart(fig_mes, use_container_width=True)
    
    with col_graf2:
        st.subheader("🥧 Distribuição por Status")
        if COLUMN_STATUS in df_filtrado.columns:
            fig_status = criar_grafico_pizza(df_filtrado, COLUMN_STATUS, "Distribuição por Status")
            if fig_status:
                st.plotly_chart(fig_status, use_container_width=True)
    
    # Gráfico de devolução
    st.subheader("📉 Análise de Devoluções por Tamanho")
    if COLUMN_TAMANHO in df_filtrado.columns and COLUMN_DEVOLUCAO in df_filtrado.columns:
        fig_devolucao = criar_grafico_barras(df_filtrado, COLUMN_TAMANHO, COLUMN_DEVOLUCAO, "Devoluções por Tamanho")
        if fig_devolucao:
            st.plotly_chart(fig_devolucao, use_container_width=True)
    
    # ===== TABELAS ANALÍTICAS =====
    st.markdown("""
    <div class="section-header">📋 Tabelas Analíticas Detalhadas</div>
    """, unsafe_allow_html=True)
    
    # Abas para organizar as tabelas
    tab1, tab2, tab3, tab4 = st.tabs(["📦 Por Tamanho", "🗓️ Por Mês", "🌍 Por UF", "📊 Resumo Geral"])
    
    with tab1:
        col_tab1_1, col_tab1_2 = st.columns(2)
        
        with col_tab1_1:
            st.subheader("Quantidade por Tamanho")
            if COLUMN_TAMANHO in df_filtrado.columns and COLUMN_QUANTIDADE in df_filtrado.columns:
                tabela_tamanho = df_filtrado.groupby(COLUMN_TAMANHO)[COLUMN_QUANTIDADE].sum().reset_index()
                tabela_tamanho = tabela_tamanho.sort_values(COLUMN_QUANTIDADE, ascending=False)
                st.dataframe(tabela_tamanho, hide_index=True, use_container_width=True)
        
        with col_tab1_2:
            st.subheader("Valor Total por Tamanho")
            if COLUMN_TAMANHO in df_filtrado.columns and COLUMN_VALOR_TOTAL in df_filtrado.columns:
                tabela_tamanho_valor = df_filtrado.groupby(COLUMN_TAMANHO)[COLUMN_VALOR_TOTAL].sum().reset_index()
                tabela_tamanho_valor = tabela_tamanho_valor.sort_values(COLUMN_VALOR_TOTAL, ascending=False)
                st.dataframe(tabela_tamanho_valor, hide_index=True, use_container_width=True)
    
    with tab2:
        st.subheader("Análise Temporal - Quantidade por Mês e Tamanho")
        if \'mês\' in df_filtrado.columns and COLUMN_TAMANHO in df_filtrado.columns and COLUMN_QUANTIDADE in df_filtrado.columns:
            tabela_mes_tamanho = df_filtrado.groupby([\'mês\', COLUMN_TAMANHO])[COLUMN_QUANTIDADE].sum().reset_index()
            tabela_pivot = tabela_mes_tamanho.pivot(index=\'mês\', columns=COLUMN_TAMANHO, values=COLUMN_QUANTIDADE).fillna(0)
            st.dataframe(tabela_pivot, use_container_width=True)
    
    with tab3:
        st.subheader("Distribuição Geográfica - Produtos por UF")
        if COLUMN_UF in df_filtrado.columns and COLUMN_PRODUTO in df_filtrado.columns and COLUMN_QUANTIDADE in df_filtrado.columns:
            tabela_uf_produto = df_filtrado.groupby([COLUMN_UF, COLUMN_PRODUTO])[COLUMN_QUANTIDADE].sum().reset_index()
            tabela_uf_produto = tabela_uf_produto.sort_values(COLUMN_QUANTIDADE, ascending=False)
            st.dataframe(tabela_uf_produto, hide_index=True, use_container_width=True)
    
    with tab4:
        st.subheader("Resumo Estatístico")
        colunas_numericas_existentes = [col for col in colunas_numericas if col in df_filtrado.columns]
        if colunas_numericas_existentes:
            resumo_stats = df_filtrado[colunas_numericas_existentes].describe()
            st.dataframe(resumo_stats, use_container_width=True)
    
    # ===== VISUALIZAÇÃO PERSONALIZADA =====
    st.markdown("""
    <div class="section-header">🔍 Exploração Personalizada dos Dados</div>
    """, unsafe_allow_html=True)
    
    col_custom1, col_custom2 = st.columns([2, 1])
    
    with col_custom2:
        st.subheader("Configurações de Visualização")
        all_columns = df.columns.tolist()
        selected_columns = st.multiselect(
            "Escolha as colunas para exibir:",
            all_columns,
            default=all_columns[:10] if len(all_columns) > 10 else all_columns
        )
        
        num_rows = st.slider("Número de linhas para exibir:", 5, 100, 20)
        
        # Opção de download
        if st.button("📥 Preparar Download dos Dados Filtrados"):
            csv = df_filtrado.to_csv(index=False)
            st.download_button(
                label="⬇️ Baixar CSV",
                data=csv,
                file_name=f"dados_filtrados_{pd.Timestamp.now().strftime(\'%Y%m%d_%H%M%S\')}.csv",
                mime="text/csv"
            )
    
    with col_custom1:
        st.subheader("Dados Selecionados")
        if selected_columns:
            st.dataframe(
                df_filtrado[selected_columns].head(num_rows),
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
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
        st.sidebar.success("✅ Dados consolidados limpos com sucesso!")
        st.session_state.df_consolidado = pd.DataFrame() # Limpa o DataFrame na sessão
        st.rerun()
    else:
        st.sidebar.info("ℹ️ Nenhum dado consolidado para limpar.")
