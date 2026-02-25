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
.card { background-color: white; padding: 20px; border-radius: 14px; box-shadow: 0px 4px 10px rgba(0,0,0,0.08);}
.card-title { font-size:16px; color:gray; margin-bottom:8px; }
.card-value { font-size:42px; font-weight:700; }
</style>
""", unsafe_allow_html=True)

st.image("https://github.com/dataflowb2b-glitch/BI_PYTHON/blob/main/LOGO%20NOVA%20DAS%20NOVAS.jpeg", caption="Imagem da URL")
st.title("📊 Dashboard Financeiro - CBR")

# ==============================
# BUSCAR DADOS
# ==============================

response = supabase.table("vw_contas_movimento").select("*").execute()
df = pd.DataFrame(response.data)

if "fornecedor" in df.columns:
    df = df.rename(columns={"fornecedor": "filial"})

# ==============================
# TRATAR VALORES NULOS
# ==============================

df["razao"] = df.get("razao","Não informado")
df["grupo"] = df["grupo"].fillna("Não informado")
df["filial"] = df["filial"].fillna("Não informado")
df["pcontas"] = df["pcontas"].fillna("Não informado")
df["tipo_conta"] = df["tipo_conta"].fillna("Não informado")

df['dt_lancamento'] = pd.to_datetime(df['dt_lancamento'], errors='coerce')
df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
df = df.dropna(subset=['dt_lancamento','valor'])
df['movimento'] = df['movimento'].str.strip().str.capitalize()

meses = {1:"Janeiro",2:"Fevereiro",3:"Março",4:"Abril",5:"Maio",6:"Junho",
         7:"Julho",8:"Agosto",9:"Setembro",10:"Outubro",11:"Novembro",12:"Dezembro"}
df['ano'] = df['dt_lancamento'].dt.year
df['mes'] = df['dt_lancamento'].dt.month
df['nome_mes'] = df['mes'].map(meses)
df['mes_ano'] = df['dt_lancamento'].dt.to_period('M').astype(str)

ordem_meses = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho",
               "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]

# ==============================
# FILTROS INTERATIVOS ACIMA DOS CARDS
# ==============================

st.subheader("📋 Filtros")
col_data1,col_data2 = st.columns(2)
ano_sel = col_data1.multiselect("Ano", sorted(df["ano"].dropna().unique()), key="ano")
mes_sel = col_data2.multiselect("Mês", sorted(df["nome_mes"].dropna().unique(), key=lambda x: ordem_meses.index(x)), key="mes")

col_f1,col_f2,col_f3,col_f4,col_f5,col_f6 = st.columns(6)
razao_sel = col_f1.multiselect("Razão", sorted(df["razao"].dropna().unique()), key="razao")
grupo_sel = col_f2.multiselect("Grupo", sorted(df["grupo"].dropna().unique()), key="grupo")
filial_sel = col_f3.multiselect("Filial", sorted(df["filial"].dropna().unique()), key="filial")
movimento_sel = col_f4.multiselect("Movimento", sorted(df["movimento"].dropna().unique()), key="movimento")
tipo_conta_sel = col_f5.multiselect("Tipo Conta", sorted(df["tipo_conta"].dropna().unique()), key="tipo_conta")
pcontas_sel = col_f6.multiselect("PContas", sorted(df["pcontas"].dropna().unique()), key="pcontas")

def limpar_filtros():
    st.session_state.ano=[]
    st.session_state.mes=[]
    st.session_state.razao=[]
    st.session_state.grupo=[]
    st.session_state.filial=[]
    st.session_state.tipo_conta=[]
    st.session_state.pcontas=[]
st.button("🔄 Limpar filtros", on_click=limpar_filtros)

# ==============================
# APLICAR FILTROS
# ==============================

df_filtrado = df.copy()
for key, sel, col in zip(
    ["ano","mes","razao","grupo","filial","movimento","tipo_conta","pcontas"],
    [ano_sel,mes_sel,razao_sel,grupo_sel,filial_sel,movimento_sel,tipo_conta_sel,pcontas_sel],
    ["ano","nome_mes","razao","grupo","filial","movimento","tipo_conta","pcontas"]
):
    if sel:
        df_filtrado = df_filtrado[df_filtrado[col].isin(sel)]

# ==============================
# CARDS DINÂMICOS
# ==============================

totais_filtrados = df_filtrado.groupby('movimento')['valor'].sum()
receita_filtrada = totais_filtrados.get('Receita',0)
despesa_filtrada = totais_filtrados.get('Despesa',0)
resultado_filtrado = receita_filtrada + despesa_filtrada

col1,col2,col3 = st.columns(3)
col1.markdown(f"""<div class="card"><div class="card-title">💰 Receita (Filtro)</div><div class="card-value" style="color:#16a34a;">{formatar_real(receita_filtrada)}</div></div>""", unsafe_allow_html=True)
col2.markdown(f"""<div class="card"><div class="card-title">💸 Despesa (Filtro)</div><div class="card-value" style="color:#dc2626;">{formatar_real(despesa_filtrada)}</div></div>""", unsafe_allow_html=True)
cor_res = "#16a34a" if resultado_filtrado>=0 else "#dc2626"
col3.markdown(f"""<div class="card"><div class="card-title">📊 Resultado</div><div class="card-value" style="color:{cor_res};">{formatar_real(resultado_filtrado)}</div></div>""", unsafe_allow_html=True)

# ==============================
# TABS
# ==============================

tab1, tab2, tab3 = st.tabs(["📊 Dashboard Principal","📈 Média de Despesas","📊 DRE Mensal"])

with tab1:
    with st.expander("📅 Valores por Mês/Ano"):
        df_mes_ano = df_filtrado.groupby(['mes_ano','movimento'])['valor'].sum().unstack(fill_value=0)
        df_mes_ano['Receita'] = df_mes_ano.get('Receita',0)
        df_mes_ano['Despesa'] = df_mes_ano.get('Despesa',0)
        df_mes_ano['Resultado'] = df_mes_ano['Receita'] + df_mes_ano['Despesa']
        st.dataframe(df_mes_ano.style.format(formatar_real).applymap(colorir_valor), use_container_width=True)

    with st.expander("📂 Visão Detalhada"):
        df_detalhe = df_filtrado.groupby(['razao','grupo','filial','ano','nome_mes','tipo_conta','pcontas','movimento'], dropna=False)['valor'].sum().unstack(fill_value=0).reset_index()
        for col in ["Receita","Despesa"]:
            if col not in df_detalhe.columns: df_detalhe[col]=0
        st.dataframe(df_detalhe.style.format({"Receita":formatar_real,"Despesa":formatar_real}).applymap(colorir_valor, subset=["Receita","Despesa"]), use_container_width=True)

    with st.expander("📂 Despesas Mês a Mês"):
        df_despesas = df_filtrado[df_filtrado["movimento"]=="Despesa"].copy()
        df_despesas_pivot = pd.pivot_table(df_despesas,index=['razao','grupo','filial','tipo_conta','pcontas'],columns='nome_mes',values='valor',aggfunc='sum',fill_value=0)
        meses_existentes = [m for m in ordem_meses if m in df_despesas_pivot.columns]
        df_despesas_pivot = df_despesas_pivot[meses_existentes].reset_index()
        st.dataframe(df_despesas_pivot.style.format({mes:formatar_real for mes in meses_existentes}).applymap(colorir_valor, subset=meses_existentes), use_container_width=True)

with tab2:
    st.subheader("📊 Média de Despesas (Filtrada)")
    df_media_despesas = df_filtrado[df_filtrado["movimento"]=="Despesa"].copy()
    if not df_media_despesas.empty:
        df_media = df_media_despesas.groupby(['razao','grupo','filial','tipo_conta','pcontas'])['valor'].mean().reset_index()
        df_media.rename(columns={"valor":"Média Despesa"}, inplace=True)
        st.dataframe(df_media.style.format({"Média Despesa":formatar_real}).applymap(colorir_valor, subset=["Média Despesa"]), use_container_width=True)
    else:
        st.warning("Nenhuma despesa encontrada para os filtros selecionados.")

with tab3:
    st.subheader("📊 DRE Mensal (Receita x Despesa x Resultado)")
    df_dre = pd.pivot_table(df_filtrado, index='movimento', columns='nome_mes', values='valor', aggfunc='sum', fill_value=0)
    # Adicionar Resultado = Receita - Despesa
    if "Receita" in df_dre.index and "Despesa" in df_dre.index:
        df_dre.loc["Resultado"] = df_dre.loc["Receita"] + df_dre.loc["Despesa"]
    meses_existentes = [m for m in ordem_meses if m in df_dre.columns]
    df_dre = df_dre[meses_existentes].reset_index()
    st.dataframe(df_dre.style.format({m:formatar_real for m in meses_existentes}).applymap(colorir_valor, subset=meses_existentes), use_container_width=True)
    st.line_chart(df_dre.set_index('movimento')[meses_existentes].T)
