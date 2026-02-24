import streamlit as st
import pandas as pd
from supabase import create_client

from PIL import Image

# ==============================
# FUNÇÕES
# ==============================

def formatar_real(valor):
    if pd.isna(valor):
        return ""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def colorir_valor(val):
    if val > 0:
        return "color: green; font-weight: bold"
    elif val < 0:
        return "color: red; font-weight: bold"
    return ""

# ==============================
# CONFIGURAÇÃO
# ==============================

url = "https://sbpgrmsxdmunnzsckqrh.supabase.co"
key = "sb_publishable_TmQzWQo_ceBPYD91ME9Sjw_azJWpNkR"
supabase = create_client(url, key)

st.set_page_config(layout="wide")

st.markdown("""
<style>
.stApp { background-color: #f5f7fa; }
.card {
    background-color: white;
    padding: 20px;
    border-radius: 14px;
    box-shadow: 0px 4px 10px rgba(0,0,0,0.08);
}
.card-title {
    font-size:16px;
    color:gray;
    margin-bottom:8px;
}
.card-value {
    font-size:42px;
    font-weight:700;
}
</style>
""", unsafe_allow_html=True)

st.image("https://github.com/dataflowb2b-glitch/BI_PYTHON/blob/main/LOGO%20NOVA%20DAS%20NOVAS.jpeg", caption="Imagem da URL")
st.title("📊 Dashboard Financeiro - CBR")

# ==============================
# BUSCAR DADOS
# ==============================

response = supabase.table("vw_contas_movimento").select("*").execute()
data = response.data
df = pd.DataFrame(data)

# 🔹 Renomear fornecedor para filial
if "fornecedor" in df.columns:
    df = df.rename(columns={"fornecedor": "filial"})

# ==============================
# TRATAR VALORES NULOS
# ==============================

df["grupo"] = df["grupo"].fillna("Não informado")
df["filial"] = df["filial"].fillna("Não informado")
df["pcontas"] = df["pcontas"].fillna("Não informado")
df["tipo_conta"] = df["tipo_conta"].fillna("Não informado")

df['dt_lancamento'] = pd.to_datetime(df['dt_lancamento'], errors='coerce')
df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
df = df.dropna(subset=['dt_lancamento', 'valor'])
df['movimento'] = df['movimento'].str.strip().str.capitalize()

# 🔹 Criar colunas de Ano e Mês
meses = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março",
    4: "Abril", 5: "Maio", 6: "Junho",
    7: "Julho", 8: "Agosto", 9: "Setembro",
    10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

df['ano'] = df['dt_lancamento'].dt.year
df['mes'] = df['dt_lancamento'].dt.month
df['nome_mes'] = df['mes'].map(meses)

if not data:
    st.warning("Nenhum dado encontrado.")
    st.stop()

# ==============================
# CARDS DE TOTAL GERAL (RESTAURADOS)
# ==============================

totais = df.groupby('movimento')['valor'].sum()
receita_total = totais.get('Receita', 0)
despesa_total = totais.get('Despesa', 0)
resultado_total = receita_total + despesa_total

col1, col2, col3 = st.columns(3)
col1.markdown(f"""
<div class="card">
    <div class="card-title">💰 Receita Total</div>
    <div class="card-value" style="color:#16a34a;">
        {formatar_real(receita_total)}
    </div>
</div>
""", unsafe_allow_html=True)
col2.markdown(f"""
<div class="card">
    <div class="card-title">💸 Despesa Total</div>
    <div class="card-value" style="color:#dc2626;">
        {formatar_real(despesa_total)}
    </div>
</div>
""", unsafe_allow_html=True)
cor_resultado = "#16a34a" if resultado_total >= 0 else "#dc2626"
icone = "📈" if resultado_total >= 0 else "📉"
col3.markdown(f"""
<div class="card">
    <div class="card-title">{icone} Resultado Total</div>
    <div class="card-value" style="color:{cor_resultado};">
        {formatar_real(resultado_total)}
    </div>
</div>
""", unsafe_allow_html=True)

# ==============================
# AGRUPAMENTO MÊS/ANO
# ==============================

df['mes_ano'] = df['dt_lancamento'].dt.to_period('M').astype(str)
grouped_mensal = (
    df.groupby(['mes_ano', 'movimento'])['valor']
    .sum()
    .unstack(fill_value=0)
    .sort_index()
)
if 'Receita' not in grouped_mensal.columns:
    grouped_mensal['Receita'] = 0
if 'Despesa' not in grouped_mensal.columns:
    grouped_mensal['Despesa'] = 0
grouped_mensal['Resultado'] = grouped_mensal['Receita'] + grouped_mensal['Despesa']

st.subheader("📅 Valores por Mês/Ano")
styled = grouped_mensal.style.format(formatar_real).applymap(colorir_valor)
st.dataframe(styled, use_container_width=True)

# ==============================
# FILTROS INTERATIVOS
# ==============================

st.subheader("📋 Detalhamento das Movimentações")
col_data1, col_data2 = st.columns(2)
ano_sel = col_data1.multiselect("Ano", options=sorted(df["ano"].dropna().unique()), key="ano")
ordem_meses = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho","Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]
mes_sel = col_data2.multiselect("Mês", options=sorted(df["nome_mes"].dropna().unique(), key=lambda x: ordem_meses.index(x)), key="mes")

col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns(5)
grupo_sel = col_f1.multiselect("Grupo", options=sorted(df["grupo"].dropna().unique()), key="grupo")
filial_sel = col_f2.multiselect("Filial", options=sorted(df["filial"].dropna().unique()), key="filial")
movimento_sel = col_f3.multiselect("Movimento", options=sorted(df["movimento"].dropna().unique()), key="movimento")
tipo_conta_sel = col_f4.multiselect("Tipo Conta", options=sorted(df["tipo_conta"].dropna().unique()), key="tipo_conta")
pcontas_sel = col_f5.multiselect("PContas", options=sorted(df["pcontas"].dropna().unique()), key="pcontas")

# Botão Limpar Filtros
def limpar_filtros():
    st.session_state.ano = []
    st.session_state.mes = []
    st.session_state.grupo = []
    st.session_state.filial = []
    st.session_state.tipo_conta = []
    st.session_state.pcontas = []

st.button("🔄 Limpar filtros", on_click=limpar_filtros)

# ==============================
# APLICAR FILTROS
# ==============================

df_filtrado = df.copy()
if ano_sel:
    df_filtrado = df_filtrado[df_filtrado["ano"].isin(ano_sel)]
if mes_sel:
    df_filtrado = df_filtrado[df_filtrado["nome_mes"].isin(mes_sel)]
if grupo_sel:
    df_filtrado = df_filtrado[df_filtrado["grupo"].isin(grupo_sel)]
if filial_sel:
    df_filtrado = df_filtrado[df_filtrado["filial"].isin(filial_sel)]
if movimento_sel:
    df_filtrado = df_filtrado[df_filtrado["movimento"].isin(movimento_sel)]
if tipo_conta_sel:
    df_filtrado = df_filtrado[df_filtrado["tipo_conta"].isin(tipo_conta_sel)]
if pcontas_sel:
    df_filtrado = df_filtrado[df_filtrado["pcontas"].isin(pcontas_sel)]

# ==============================
# TOTAL DINÂMICO (FILTRADO)
# ==============================

receita_filtrada = df_filtrado.loc[df_filtrado["movimento"]=="Receita","valor"].sum()
despesa_filtrada = df_filtrado.loc[df_filtrado["movimento"]=="Despesa","valor"].sum()
resultado_filtrado = receita_filtrada + despesa_filtrada

col_t1, col_t2, col_t3 = st.columns(3)
col_t1.markdown(f"""<div style="background:white;padding:15px;border-radius:10px;box-shadow:0px 2px 6px rgba(0,0,0,0.08);">
<div style="font-size:16px; color:gray;">💰 Receita (Filtro)</div>
<div style="font-size:28px; font-weight:700; color:#16a34a;">{formatar_real(receita_filtrada)}</div></div>""", unsafe_allow_html=True)
col_t2.markdown(f"""<div style="background:white;padding:15px;border-radius:10px;box-shadow:0px 2px 6px rgba(0,0,0,0.08);">
<div style="font-size:16px; color:gray;">💸 Despesa (Filtro)</div>
<div style="font-size:28px; font-weight:700; color:#dc2626;">{formatar_real(despesa_filtrada)}</div></div>""", unsafe_allow_html=True)
cor_res = "#16a34a" if resultado_filtrado >=0 else "#dc2626"
col_t3.markdown(f"""<div style="background:white;padding:15px;border-radius:10px;box-shadow:0px 2px 6px rgba(0,0,0,0.08);">
<div style="font-size:16px; color:gray;">📊 Resultado</div>
<div style="font-size:28px; font-weight:700; color:{cor_res};">{formatar_real(resultado_filtrado)}</div></div>""", unsafe_allow_html=True)

# ==============================
# TABELA DETALHADA DE MOVIMENTAÇÕES
# ==============================

df_detalhe = df_filtrado.groupby(['grupo','filial','ano','nome_mes','tipo_conta','pcontas','movimento'], dropna=False)['valor'].sum().unstack(fill_value=0).reset_index()
if "Receita" not in df_detalhe.columns:
    df_detalhe["Receita"] = 0
if "Despesa" not in df_detalhe.columns:
    df_detalhe["Despesa"] = 0

styled_detalhe = df_detalhe.style.format({"Receita":formatar_real,"Despesa":formatar_real}).applymap(colorir_valor, subset=["Receita","Despesa"])
st.subheader("📂 Visão Detalhada por Grupo, Filial, Ano, Mês, Tipo Conta e PContas")
st.dataframe(styled_detalhe,use_container_width=True)

# ==============================
# TABELA HIERÁRQUICA DE DESPESAS (FILTRADA POR ANO, GRUPO, FILIAL E PCONTAS, NÃO MÊS)
# ==============================

df_despesas = df[df["movimento"]=="Despesa"].copy()
if ano_sel:
    df_despesas = df_despesas[df_despesas["ano"].isin(ano_sel)]
if grupo_sel:
    df_despesas = df_despesas[df_despesas["grupo"].isin(grupo_sel)]
if filial_sel:
    df_despesas = df_despesas[df_despesas["filial"].isin(filial_sel)]
if pcontas_sel:
    df_despesas = df_despesas[df_despesas["pcontas"].isin(pcontas_sel)]

df_despesas_pivot = pd.pivot_table(
    df_despesas,
    index=['grupo','filial','tipo_conta','pcontas'],
    columns='nome_mes',
    values='valor',
    aggfunc='sum',
    fill_value=0
)

# Ordenar colunas existentes
meses_existentes = [m for m in ordem_meses if m in df_despesas_pivot.columns]
df_despesas_pivot = df_despesas_pivot[meses_existentes].reset_index()

styled_despesas = df_despesas_pivot.style.format({mes:formatar_real for mes in meses_existentes}).applymap(colorir_valor, subset=meses_existentes)
st.subheader("📂 Despesas Mês a Mês por Grupo, Filial, Tipo Conta e PContas (Filtro por Ano, Grupo, Filial e PContas)")
st.dataframe(styled_despesas,use_container_width=True)
