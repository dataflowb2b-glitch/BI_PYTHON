import streamlit as st
import pandas as pd
from supabase import create_client
from PIL import Image
from st_aggrid import JsCode

# ==============================
# FUNÇÕES
# ==============================

def formatar_real(valor):
    if pd.isna(valor):
        return ""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

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
# FILTROS
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
# CARDS
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

        df_exibicao = df_mes_ano.copy()
        for col in df_exibicao.columns:
            df_exibicao[col] = df_exibicao[col].apply(formatar_real)

        st.data_editor(df_exibicao, use_container_width=True, disabled=True)

    with st.expander("📂 Visão Detalhada"):
        df_detalhe = df_filtrado.groupby(
            ['razao','grupo','filial','ano','nome_mes','tipo_conta','pcontas','movimento'],
            dropna=False
        )['valor'].sum().unstack(fill_value=0).reset_index()

        for col in ["Receita","Despesa"]:
            if col not in df_detalhe.columns:
                df_detalhe[col] = 0

        df_detalhe["Receita"] = df_detalhe["Receita"].apply(formatar_real)
        df_detalhe["Despesa"] = df_detalhe["Despesa"].apply(formatar_real)

        st.data_editor(df_detalhe, use_container_width=True, disabled=True)

    with st.expander("📂 Despesas Mês a Mês"):
        df_despesas = df_filtrado[df_filtrado["movimento"]=="Despesa"].copy()

        df_despesas_pivot = pd.pivot_table(
            df_despesas,
            index=['razao','grupo','filial','tipo_conta','pcontas'],
            columns='nome_mes',
            values='valor',
            aggfunc='sum',
            fill_value=0
        )

        meses_existentes = [m for m in ordem_meses if m in df_despesas_pivot.columns]
        df_despesas_pivot = df_despesas_pivot[meses_existentes].reset_index()

        for mes in meses_existentes:
            df_despesas_pivot[mes] = df_despesas_pivot[mes].apply(formatar_real)

        st.data_editor(df_despesas_pivot, use_container_width=True, disabled=True)

with tab2:

    st.subheader("📊 Média de Despesas (Filtrada)")
    df_media_despesas = df_filtrado[df_filtrado["movimento"]=="Despesa"].copy()

    if not df_media_despesas.empty:
        df_media = df_media_despesas.groupby(
            ['razao','grupo','filial','tipo_conta','pcontas']
        )['valor'].mean().reset_index()

        df_media.rename(columns={"valor":"Média Despesa"}, inplace=True)
        df_media["Média Despesa"] = df_media["Média Despesa"].apply(formatar_real)

        st.data_editor(df_media, use_container_width=True, disabled=True)
    else:
        st.warning("Nenhuma despesa encontrada para os filtros selecionados.")



with tab3:

    st.subheader("📊 DRE Hierárquica (Razão ➝ Grupo ➝ Filial)")

    # ==============================
    # GARANTIR PADRONIZAÇÃO
    # ==============================

    df_filtrado["movimento"] = df_filtrado["movimento"].str.strip().str.title()

    # ==============================
    # PIVOT BASE
    # ==============================

    df_pivot = pd.pivot_table(
        df_filtrado,
        index=["razao", "grupo", "filial", "movimento"],
        columns="nome_mes",
        values="valor",
        aggfunc="sum",
        fill_value=0
    )

    if df_pivot.empty:
        st.warning("Sem dados para os filtros selecionados.")
        st.stop()

    meses_existentes = sorted(df_pivot.columns)
    df_pivot = df_pivot[meses_existentes]

    linhas = []

    # ==============================
    # ORDEM CORRETA DOS MESES
    # ==============================

    ordem_meses = [
        "Janeiro", "Fevereiro", "Março", "Abril",
        "Maio", "Junho", "Julho", "Agosto",
        "Setembro", "Outubro", "Novembro", "Dezembro"
    ]

    meses_existentes = [m for m in ordem_meses if m in df_pivot.columns]

    df_pivot = df_pivot[meses_existentes]

    linhas = []

    # ==============================
    # HIERARQUIA
    # ==============================

    for razao, df_razao in df_pivot.groupby(level="razao"):

        receita_razao = df_razao[df_razao.index.get_level_values("movimento") == "Receita"].sum()
        despesa_razao = df_razao[df_razao.index.get_level_values("movimento") == "Despesa"].sum()
        resultado_razao = receita_razao + despesa_razao

        row_razao = {mes: float(resultado_razao.get(mes, 0)) for mes in meses_existentes}
        row_razao["TOTAL"] = float(resultado_razao.sum())
        row_razao["path"] = [razao]
        linhas.append(row_razao)

        # ----------------------------

        for grupo, df_grupo in df_razao.groupby(level="grupo"):

            receita_grupo = df_grupo[df_grupo.index.get_level_values("movimento") == "Receita"].sum()
            despesa_grupo = df_grupo[df_grupo.index.get_level_values("movimento") == "Despesa"].sum()
            resultado_grupo = receita_grupo + despesa_grupo

            row_grupo = {mes: float(resultado_grupo.get(mes, 0)) for mes in meses_existentes}
            row_grupo["TOTAL"] = float(resultado_grupo.sum())
            row_grupo["path"] = [razao, grupo]
            linhas.append(row_grupo)

            # ----------------------------

            for filial, df_filial in df_grupo.groupby(level="filial"):

                receita = df_filial[df_filial.index.get_level_values("movimento") == "Receita"].sum()
                despesa = df_filial[df_filial.index.get_level_values("movimento") == "Despesa"].sum()
                resultado = receita + despesa

                row_filial = {mes: float(resultado.get(mes, 0)) for mes in meses_existentes}
                row_filial["TOTAL"] = float(resultado.sum())
                row_filial["path"] = [razao, grupo, filial]
                linhas.append(row_filial)

                # ----------------------------
                # DETALHAMENTO
                # ----------------------------

                for movimento, df_mov in df_filial.groupby(level="movimento"):

                    row_det = {mes: float(df_mov[mes].sum()) for mes in meses_existentes}
                    row_det["TOTAL"] = float(df_mov.sum().sum())
                    row_det["path"] = [razao, grupo, filial, movimento]
                    linhas.append(row_det)

    dre_df = pd.DataFrame(linhas)

    # ==============================
    # ESTILO DE COR
    # ==============================

    cell_style = JsCode("""
        function(params) {

            if (params.value == null) return {};

            if (params.value > 0) {
                return { color: "#16a34a", fontWeight: "bold" };
            }

            if (params.value < 0) {
                return { color: "#dc2626", fontWeight: "bold" };
            }

            return {};
        }
    """)

    # ==============================
    # CONFIGURAÇÃO GRID
    # ==============================

    gb = GridOptionsBuilder.from_dataframe(dre_df)

    gb.configure_column("path", hide=True)

    for col in meses_existentes + ["TOTAL"]:
        gb.configure_column(
            col,
            type=["numericColumn"],
            valueFormatter="x.toLocaleString('pt-BR', {style:'currency', currency:'BRL'})",
            cellStyle=cell_style
        )

    gb.configure_grid_options(
        treeData=True,
        animateRows=True,
        groupDefaultExpanded=0,
        getDataPath=JsCode("function(data) { return data.path; }")
    )

    gridOptions = gb.build()

    AgGrid(
        dre_df,
        gridOptions=gridOptions,
        enable_enterprise_modules=True,
        fit_columns_on_grid_load=True,
        theme="streamlit",
        allow_unsafe_jscode=True,
        height=650
    )

