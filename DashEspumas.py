# ================================================================
# Dashboard Profissional – Estilo Corporativo Azul – BonSono
# COM CONSUMO DE PRODUTOS QUÍMICOS + CORREÇÃO DE TIPOS DE ESPUMA
# ================================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import os

# ================================================================
# CONFIGURAÇÃO DA PÁGINA
# ================================================================
st.set_page_config(
    page_title="Histórico de Produção de Espumas",
    page_icon="📊",
    layout="wide"
)

# ================================================================
# ESTILO GLOBAL – PALETA AZUL PREMIUM
# ================================================================
st.markdown("""
<style>
:root {
    --azul1: #003b73;
    --azul2: #0056b3;
    --azul3: #007bff;
    --azul-claro: #e7f1ff;
    --cinza-texto: #2c3e50;
    --cinza-claro: #f5f7fa;
}
.stApp {
    background-color: white !important;
}
section[data-testid="stSidebar"] {
    background-color: var(--cinza-claro);
    border-right: 1px solid #d0d7e2;
}
section[data-testid="stSidebar"] h3 {
    color: var(--azul2);
}
h1, h2, h3 {
    color: var(--azul1) !important;
    font-weight: 700;
}
.card {
    background: var(--azul-claro);
    padding: 22px;
    border-radius: 14px;
    border-left: 6px solid var(--azul2);
    box-shadow: 0 3px 8px rgba(0,0,0,0.07);
    text-align: center;
}
.card h2 {
    font-size: 2.2rem;
    color: var(--azul2);
    margin-bottom: 4px;
}
.card p {
    color: var(--cinza-texto);
    margin: 0;
}
.dataframe tbody tr:hover {
    background-color:#f0f7ff;
}
.stSelectbox > div {
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# ================================================================
# BANCO DE DADOS - CAMINHO CORRETO PARA STREAMLIT CLOUD
# ================================================================
# O banco está NA MESMA PASTA do script (DASHBOARD_PLATAFORMA)
DB_PATH = "producao.db"  # ✅ CAMINHO RELATIVO CORRETO

# Validação visual para debug
st.sidebar.info(f"🔍 Banco carregado de: `{DB_PATH}`")
if not os.path.exists(DB_PATH):
    st.error("❌ Banco de dados não encontrado!")
    st.code(f"Verifique se o arquivo existe em:\n{os.path.abspath(DB_PATH)}", language="bash")
    st.stop()

# ================================================================
# FUNÇÃO PRINCIPAL DE CARREGAMENTO DE DADOS
# ================================================================
@st.cache_data(ttl=60)
def load_producoes_com_consumo():
    """
    Carrega dados de produção com consumo de produtos químicos.
    🔧 CORREÇÃO 2: Remove mapeamento de tipo_espuma (sistema usa texto direto)
    """
    conn = sqlite3.connect(DB_PATH)
    
    # Query simplificada - tipo_espuma já vem como texto do banco
    query = """
    SELECT 
        p.id AS producao_id_interno,
        p.producao_id AS bloco,
        p.data_producao,
        p.tipo_espuma,  -- Já é texto, não precisa de mapeamento
        p.cor,
        p.altura,
        p.conformidade,
        p.observacoes,
        c.nome AS componente,
        cp.quantidade_usada
    FROM producao p
    LEFT JOIN componenteproducao cp ON p.id = cp.producao_id
    LEFT JOIN componente c ON cp.componente_id = c.id
    ORDER BY p.data_producao DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    # 🔧 CORREÇÃO 3: Conversão de tipos
    df["data_producao"] = pd.to_datetime(df["data_producao"],errors="coerce")
    df["quantidade_usada"] = pd.to_numeric(df["quantidade_usada"], errors="coerce")
    df["cor"] = df["cor"].astype(str)
    df["altura"] = pd.to_numeric(df["altura"], errors="coerce")
    df["tipo_espuma"] = df["tipo_espuma"].astype(str)  # Já é texto, mantém como está
    
    return df

# ================================================================
# TOPO – LOGO + TÍTULO
# ================================================================
col_logo, col_title = st.columns([1, 4])

with col_logo:
    logo_path = "static/imagens/logo-bonsono.png"
    if os.path.exists(logo_path):
        st.image(logo_path, width=180)
    else:
        st.write(" ")

with col_title:
    st.markdown("""
        <h1 style='margin-bottom:-10px;'>📊 Dashboard de Produção de Espumas</h1>
        <p style='color:#5d6d7e;'>Colchões BonSono • Análise dinâmica da produção e consumo químico</p>
    """, unsafe_allow_html=True)

# ================================================================
# CARREGAR DADOS COM CONSUMO
# ================================================================
df_completo = load_producoes_com_consumo()

# 🔧 REMOVIDO: Debug temporário (descomente se precisar debugar)
# st.write("Valores únicos em tipo_espuma:", df_completo["tipo_espuma"].unique().tolist())

if df_completo.empty:
    st.warning("Nenhum registro encontrado.")
    st.stop()

# Dados para tabela principal (sem duplicar blocos)
df_producao = df_completo.drop_duplicates(subset=["bloco"]).copy()

# ================================================================
# SIDEBAR – FILTROS
# ================================================================
with st.sidebar:
    st.markdown("### 🔍 Filtros")

    tipos = ["Todos"] + sorted(df_producao["tipo_espuma"].dropna().unique().tolist())
    tipo_selecionado = st.selectbox("Tipo de Espuma", tipos)

    data_min = df_producao["data_producao"].min().date()
    data_max = df_producao["data_producao"].max().date()

    periodo = st.date_input(
        "Selecione o período",
        [data_min, data_max],
        min_value=data_min,
        max_value=data_max
    )

# ================================================================
# APLICAÇÃO DOS FILTROS
# ================================================================
if isinstance(periodo, str):
    periodo = (periodo, periodo)
elif len(periodo) == 1:
    periodo = (periodo[0], periodo[0])

data_inicio = pd.to_datetime(periodo[0])
data_fim = pd.to_datetime(periodo[1]) + pd.Timedelta(days=1)

df_filtrado = df_producao[
    df_producao["data_producao"].between(data_inicio, data_fim)
].copy()

if tipo_selecionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado["tipo_espuma"] == tipo_selecionado]

# Filtrar dados de consumo
df_consumo = df_completo.dropna(subset=["quantidade_usada", "componente"])
df_consumo_filtrado = df_consumo[
    df_consumo["data_producao"].between(data_inicio, data_fim)
].copy()

if tipo_selecionado != "Todos":
    df_consumo_filtrado = df_consumo_filtrado[df_consumo_filtrado["tipo_espuma"] == tipo_selecionado]

# ================================================================
# KPIs EM CARDS
# ================================================================
st.markdown("### 📈 Métricas Gerais")

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"""
        <div class="card">
            <h2>{len(df_filtrado)}</h2>
            <p>Total de Blocos</p>
        </div>
    """, unsafe_allow_html=True)

with col2:
    conformes = df_filtrado[df_filtrado["conformidade"] == "Conforme"]
    st.markdown(f"""
        <div class="card">
            <h2>{len(conformes)}</h2>
            <p>Blocos Conformes</p>
        </div>
    """, unsafe_allow_html=True)

# ================================================================
# GRÁFICO – PRODUÇÃO POR TIPO
# ================================================================
if tipo_selecionado == "Todos":
    st.markdown("### 📊 Produção por Tipo de Espuma")
    df_tipo = df_filtrado["tipo_espuma"].value_counts().reset_index()
    df_tipo.columns = ["Tipo", "Quantidade"]
    fig = px.bar(
        df_tipo,
        x="Tipo",
        y="Quantidade",
        text="Quantidade",
        color="Tipo",
        color_discrete_sequence=["#0056b3", "#1976d2", "#42a5f5", "#64b5f6"],
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        showlegend=False,
        paper_bgcolor="white",
        plot_bgcolor="white",
        font_color="#2c3e50"
    )
    st.plotly_chart(fig, use_container_width=True)

# ================================================================
# CONSUMO DE PRODUTOS QUÍMICOS
# ================================================================
st.markdown("### 🧪 Consumo de Produtos Químicos")

if not df_consumo_filtrado.empty:
    # Total por componente
    consumo_total = df_consumo_filtrado.groupby("componente")["quantidade_usada"].sum().reset_index()
    consumo_total = consumo_total.sort_values("quantidade_usada", ascending=False)

    # Gráfico
    fig_consumo = px.bar(
        consumo_total,
        x="componente",
        y="quantidade_usada",
        text="quantidade_usada",
        color="componente",
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig_consumo.update_traces(texttemplate='%{text:.1f} kg', textposition='outside')
    fig_consumo.update_layout(
        xaxis_title="Produto Químico",
        yaxis_title="Consumo Total (kg)",
        paper_bgcolor="white",
        plot_bgcolor="white",
        font_color="#2c3e50",
        showlegend=False
    )
    st.plotly_chart(fig_consumo, use_container_width=True)

    # Tabela detalhada
    with st.expander("📋 Detalhes do consumo por bloco"):
        df_exibicao = df_consumo_filtrado[[
            "bloco", "data_producao", "tipo_espuma", "componente", "quantidade_usada"
        ]].copy()
        df_exibicao["data_producao"] = df_exibicao["data_producao"].dt.strftime("%d/%m/%Y")
        df_exibicao = df_exibicao.rename(columns={
            "bloco": "Bloco",
            "data_producao": "Data",
            "tipo_espuma": "Tipo de Espuma",
            "componente": "Produto Químico",
            "quantidade_usada": "Consumo (kg)"
        })
        st.dataframe(df_exibicao, use_container_width=True)
else:
    st.info("Nenhum dado de consumo encontrado para o período selecionado.")

# ================================================================
# TENDÊNCIA DE CONSUMO AO LONGO DO TEMPO
# ================================================================
if not df_consumo_filtrado.empty:
    st.markdown("### 📈 Tendência de Consumo ao Longo do Tempo")
    
    # Opção: agrupar por dia, semana ou mês
    periodo_agreg = st.radio(
        "Agrupar por:",
        ("Dia", "Semana", "Mês"),
        horizontal=True,
        key="agreg_consumo"
    )
    
    # Criar cópia e adicionar coluna de período formatado como string
    df_tempo = df_consumo_filtrado.copy()
    
    if periodo_agreg == "Dia":
        df_tempo["periodo_str"] = df_tempo["data_producao"].dt.strftime("%d/%m/%Y")
    elif periodo_agreg == "Semana":
        df_tempo["periodo_str"] = df_tempo["data_producao"].dt.to_period("W").apply(lambda r: r.start_time.strftime("%d/%m/%Y"))
    else:  # Mês
        df_tempo["periodo_str"] = df_tempo["data_producao"].dt.to_period("M").apply(lambda r: r.start_time.strftime("%d/%m/%Y"))
    
    # Agregar consumo por período (string)
    consumo_tempo_total = df_tempo.groupby("periodo_str")["quantidade_usada"].sum().reset_index()
    
    # Gráfico 1: Consumo total ao longo do tempo
    fig_tendencia = px.line(
        consumo_tempo_total,
        x="periodo_str",
        y="quantidade_usada",
        markers=True,
        title="Consumo Total de Produtos Químicos"
    )
    fig_tendencia.update_traces(line=dict(color="#0056b3", width=3), marker=dict(size=6))
    fig_tendencia.update_layout(
        xaxis_title="Data",
        yaxis_title="Consumo Total (kg)",
        paper_bgcolor="white",
        plot_bgcolor="white",
        font_color="#2c3e50",
        xaxis=dict(tickangle=-45)
    )
    st.plotly_chart(fig_tendencia, use_container_width=True)
    
    # Gráfico 2: Consumo por produto químico ao longo do tempo (empilhado)
    st.markdown("#### Consumo por Produto Químico")
    consumo_tempo_det = df_tempo.groupby(["periodo_str", "componente"])["quantidade_usada"].sum().reset_index()
    
    if len(consumo_tempo_det["periodo_str"].unique()) > 1:
        fig_tendencia_det = px.area(
            consumo_tempo_det,
            x="periodo_str",
            y="quantidade_usada",
            color="componente",
            title="Consumo por Produto Químico ao Longo do Tempo",
            line_group="componente"
        )
        fig_tendencia_det.update_layout(
            xaxis_title="Data",
            yaxis_title="Consumo (kg)",
            paper_bgcolor="white",
            plot_bgcolor="white",
            font_color="#2c3e50",
            legend_title="Produto Químico",
            xaxis=dict(tickangle=-45)
        )
        st.plotly_chart(fig_tendencia_det, use_container_width=True)
    else:
        st.info("Selecione um período maior para visualizar a tendência por produto.")

# ================================================================
# TABELA PRINCIPAL DE PRODUÇÃO
# ================================================================
st.markdown("### 📋 Detalhes das Produções")

df_tabela = df_filtrado.copy()
df_tabela["data_producao"] = df_tabela["data_producao"].dt.strftime("%m/%d/%Y")
df_tabela = df_tabela.rename(columns={
    "bloco": "Bloco",
    "data_producao": "Data",
    "tipo_espuma": "Tipo",
    "cor": "Cor",
    "altura": "Altura (cm)",
    "conformidade": "Conformidade",
    "observacoes": "Observações"
})

# Selecionar colunas relevantes (sem id interno)
colunas_exibicao = ["Bloco", "Data", "Tipo", "Cor", "Altura (cm)", "Conformidade", "Observações"]
st.dataframe(df_tabela[colunas_exibicao], use_container_width=True, height=420)

# ================================================================
# DOWNLOAD
# ================================================================
csv = df_tabela[colunas_exibicao].to_csv(index=False).encode("utf-8")
st.download_button(
    "📥 Baixar CSV",
    data=csv,
    file_name="historico_producao_espumas.csv",
    mime="text/csv"
)