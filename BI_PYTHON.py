import streamlit as st
import pandas as pd
from supabase import create_client
from PIL import Image
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
from datetime import datetime
from st_aggrid.shared import JsCode


# ==============================
# INICIO TITULO DA PAGINA
# ==============================

st.set_page_config(
    page_title="BI Financeiro",
    page_icon="📊",
    layout="wide"
)

data_atual = datetime.now().strftime("%d/%m/%Y")

# 🔹 CSS + Barra Fixa
st.markdown(f"""
<style>

/* Remove menu padrão */
#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}
header {{visibility: hidden;}}

/* Fundo geral */
.main {{
    background-color: #f5f7fa;
}}

/* Barra superior fixa */
.topbar {{
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 70px;
    background-color: white;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 40px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    z-index: 9999;
}}

/* Espaço para compensar barra fixa */
.block-container {{
    padding-top: 90px;
}}

.title {{
    font-size: 20px;
    font-weight: 600;
}}

.date {{
    font-size: 14px;
    color: gray;
}}

</style>

<div class="topbar">
    <div style="display:flex; align-items:center; gap:15px;">
        <img src="https://raw.githubusercontent.com/dataflowb2b-glitch/BI_PYTHON/main/LOGO%20NOVA%20DAS%20NOVAS.jpeg" width="140">
        <div class="title">📊GESTÃO DE RESULTADO FINANCEIRO</div>
    </div>
    <div class="date">Atualizado em {data_atual}</div>
</div>

""", unsafe_allow_html=True)


# ==============================
#FIM TITULO DA PAGINA
# ==============================


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

# 🔹 Filtros de data primeiro
col_data1, col_data2 = st.columns(2)

ano_sel = col_data1.multiselect(
    "Ano",
    sorted(df["ano"].dropna().unique()),
    key="ano"
)

mes_sel = col_data2.multiselect(
    "Mês",
    sorted(df["nome_mes"].dropna().unique(), key=lambda x: ordem_meses.index(x)),
    key="mes"
)

# ------------------------------
# BASE COM FILTRO DE DATA
# ------------------------------

df_base = df.copy()

if ano_sel:
    df_base = df_base[df_base["ano"].isin(ano_sel)]

if mes_sel:
    df_base = df_base[df_base["nome_mes"].isin(mes_sel)]

# ==============================
# RAZÃO
# ==============================

col_f1, col_f2, col_f3, col_f4, col_f5, col_f6 = st.columns(6)

razao_options = sorted(df_base["razao"].dropna().unique())

razao_sel = col_f1.multiselect(
    "Razão",
    options=razao_options,
    key="razao"
)

# 🔄 Se mudou Razão → limpar dependentes
if "razao_old" not in st.session_state:
    st.session_state.razao_old = []

if st.session_state.razao_old != razao_sel:
    st.session_state.grupo = []
    st.session_state.filial = []
    st.session_state.razao_old = razao_sel

# ==============================
# GRUPO (DEPENDENTE)
# ==============================

df_grupo = df_base.copy()

if razao_sel:
    df_grupo = df_grupo[df_grupo["razao"].isin(razao_sel)]

grupo_options = sorted(df_grupo["grupo"].dropna().unique())

grupo_sel = col_f2.multiselect(
    "Grupo",
    options=grupo_options,
    key="grupo"
)

# 🔄 Se mudou Grupo → limpar filial
if "grupo_old" not in st.session_state:
    st.session_state.grupo_old = []

if st.session_state.grupo_old != grupo_sel:
    st.session_state.filial = []
    st.session_state.grupo_old = grupo_sel

# ==============================
# FILIAL (DEPENDENTE)
# ==============================

df_filial = df_grupo.copy()

if grupo_sel:
    df_filial = df_filial[df_filial["grupo"].isin(grupo_sel)]

filial_options = sorted(df_filial["filial"].dropna().unique())

filial_sel = col_f3.multiselect(
    "Filial",
    options=filial_options,
    key="filial"
)

# ==============================
# DEMAIS FILTROS
# ==============================

movimento_sel = col_f4.multiselect(
    "Movimento",
    sorted(df_filial["movimento"].dropna().unique()),
    key="movimento"
)

tipo_conta_sel = col_f5.multiselect(
    "Tipo Conta",
    sorted(df_filial["tipo_conta"].dropna().unique()),
    key="tipo_conta"
)

pcontas_sel = col_f6.multiselect(
    "PContas",
    sorted(df_filial["pcontas"].dropna().unique()),
    key="pcontas"
)




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

tab1, tab2, tab3,tab4 = st.tabs(["📊 Dashboard Principal","📈 Média de Despesas","📊 DRE Mensal","📊 Matriz de Despesas (Grupo + Razão + Pcontas + Filial)"])

with tab1:
    with st.expander("📅 Valores por Mês/Ano"):
        df_mes_ano = df_filtrado.groupby(['mes_ano', 'movimento'])['valor'].sum().unstack(fill_value=0)
        df_mes_ano['Receita'] = df_mes_ano.get('Receita', 0)
        df_mes_ano['Despesa'] = df_mes_ano.get('Despesa', 0)
        df_mes_ano['Resultado'] = df_mes_ano['Receita'] + df_mes_ano['Despesa']


        def colorir_valores(val, coluna):
            if coluna == "Receita":
                return "color: green" if val > 0 else "color: black"
            elif coluna == "Despesa":
                return "color: red" if val < 0 else "color: black"
            elif coluna == "Resultado":
                return "color: green" if val > 0 else "color: red"
            return ""


        df_estilizado = df_mes_ano.style

        for col in df_mes_ano.columns:
            df_estilizado = df_estilizado.map(
                lambda v, c=col: colorir_valores(v, c),
                subset=[col]
            )

        # Formatar para Real
        df_estilizado = df_estilizado.format(formatar_real)

        st.dataframe(df_estilizado, use_container_width=True)

    with st.expander("📂 Visão Detalhada"):
        df_detalhe = df_filtrado.groupby(
            ['razao', 'grupo', 'filial', 'ano', 'nome_mes', 'tipo_conta', 'pcontas', 'movimento'],
            dropna=False
        )['valor'].sum().unstack(fill_value=0).reset_index()

        # Garantir que as colunas existam
        for col in ["Receita", "Despesa"]:
            if col not in df_detalhe.columns:
                df_detalhe[col] = 0

        # Criar Resultado (opcional, mas recomendo manter padrão)
        df_detalhe["Resultado"] = df_detalhe["Receita"] + df_detalhe["Despesa"]


        def cor_texto(valor, coluna):
            if coluna == "Receita":
                return "color: green;" if valor > 0 else ""
            elif coluna == "Despesa":
                return "color: red;" if valor < 0 else ""
            elif coluna == "Resultado":
                if valor > 0:
                    return "color: green; font-weight: bold;"
                elif valor < 0:
                    return "color: red; font-weight: bold;"
            return ""


        styled = df_detalhe.style

        for col in ["Receita", "Despesa", "Resultado"]:
            styled = styled.map(
                lambda v, c=col: cor_texto(v, c),
                subset=[col]
            )

        styled = styled.format({
            "Receita": formatar_real,
            "Despesa": formatar_real,
            "Resultado": formatar_real
        })

        st.dataframe(styled, use_container_width=True)


# ==============================
# COLUNA ANO_SEMANA
# ==============================

df["ano_semana"] = (
    df["dt_lancamento"].dt.year.astype(str)
    + "-S"
    + df["dt_lancamento"].dt.isocalendar().week.astype(str).str.zfill(2)
)

with tab2:

    st.subheader("📊 Meta de Despesas + Comparativo Atual")

    mes_ano_tab2 = st.multiselect(
        "Selecione os Mês/Ano para cálculo da média",
        sorted(df["mes_ano"].dropna().unique()),
        key="mes_ano_media"
    )

    # ==============================
    # DESPESA ATUAL
    # ==============================

    df_despesa_topo = df_filtrado[
        df_filtrado["movimento"] == "Despesa"
    ].copy()

    despesa_atual_group = df_despesa_topo.groupby(
        ['razao','grupo','filial','tipo_conta','pcontas']
    )['valor'].sum().reset_index()

    despesa_atual_group.rename(
        columns={"valor": "Despesa_Atual"},
        inplace=True
    )

    # ==============================
    # BASE MÉDIA
    # ==============================

    df_base_media = df.copy()

    for sel, col in zip(
        [razao_sel, grupo_sel, filial_sel, movimento_sel, tipo_conta_sel, pcontas_sel],
        ["razao","grupo","filial","movimento","tipo_conta","pcontas"]
    ):
        if sel:
            df_base_media = df_base_media[df_base_media[col].isin(sel)]

    df_media_despesas = df_base_media[
        df_base_media["movimento"] == "Despesa"
    ].copy()

    if mes_ano_tab2:
        df_media_despesas = df_media_despesas[
            df_media_despesas["mes_ano"].isin(mes_ano_tab2)
        ]

    if not df_media_despesas.empty:

        agrupado = df_media_despesas.groupby(
            ['razao','grupo','filial','tipo_conta','pcontas']
        )

        df_media = agrupado.agg(
            Total_Despesa=('valor','sum'),
            Qtd_Meses=('mes_ano','nunique')
        ).reset_index()

        df_media["Meta_Despesa"] = (
            df_media["Total_Despesa"] / df_media["Qtd_Meses"]
        )

        # ==============================
        # MERGE
        # ==============================

        df_final = df_media.merge(
            despesa_atual_group,
            on=['razao','grupo','filial','tipo_conta','pcontas'],
            how="left"
        )

        df_final["Despesa_Atual"] = df_final["Despesa_Atual"].fillna(0)

        # ==============================
        # DIFERENÇA E VARIAÇÃO
        # ==============================

        df_final["Diferenca_R$"] = (
            df_final["Despesa_Atual"] - df_final["Meta_Despesa"]
        )

        df_final["Variação_%"] = df_final.apply(
            lambda row: (
                ((row["Despesa_Atual"] - row["Meta_Despesa"]) / row["Meta_Despesa"]) * 100
                if row["Meta_Despesa"] != 0 else 0
            ),
            axis=1
        )

        df_exibir = df_final.drop(columns=["Total_Despesa", "Qtd_Meses"])

        # ==============================
        # LINHA TOTAL
        # ==============================

        total_meta = df_exibir["Meta_Despesa"].sum()
        total_atual = df_exibir["Despesa_Atual"].sum()
        total_diferenca = df_exibir["Diferenca_R$"].sum()

        total_variacao = (
            ((total_atual - total_meta) / total_meta) * 100
            if total_meta != 0 else 0
        )

        # ==============================
        # ESTILIZAÇÃO
        # ==============================

        def cor_variacao(v):
            if v > 0:
                return "color: #dc2626; font-weight: bold;"
            elif v < 0:
                return "color: #16a34a; font-weight: bold;"
            elif v == 0:
                return "color: #e8a507; font-weight: bold;"
            return ""

        def cor_diferenca(v):
            if v > 0:
                return "color: #dc2626; font-weight: bold;"
            elif v < 0:
                return "color: #16a34a; font-weight: bold;"
            elif v == 0:
                return "color: #e8a507; font-weight: bold;"
            return ""

        def destacar_total(row):
            if row["razao"] == "TOTAL GERAL":
                return ["font-weight: bold; background-color: #f3f4f6"] * len(row)
            return [""] * len(row)

        styled = df_exibir.style.map(
            cor_variacao,
            subset=["Variação_%"]
        ).map(
            cor_diferenca,
            subset=["Diferenca_R$"]
        ).format({
            "Meta_Despesa": formatar_real,
            "Despesa_Atual": formatar_real,
            "Diferenca_R$": formatar_real,
            "Variação_%": "{:.2f}%"
        }).apply(
            destacar_total,
            axis=1
        )

        # ==========================================
        # 🔹 RESUMO GERAL ACIMA DA TABELA
        # ==========================================

        st.markdown("### 📌 Resumo Geral")

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "💰 Meta Total",
            formatar_real(total_meta)
        )

        col2.metric(
            "💳 Despesa Atual Total",
            formatar_real(total_atual)
        )

        col3.metric(
            "📊 Diferença Total",
            formatar_real(total_diferenca),
            f"{total_variacao:.2f}%"
        )
        # ==========================================

        st.dataframe(styled, width="stretch")

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


with tab4:

    st.subheader("📊 Matriz de Despesas (Grupo ➝ Razão ➝ Pcontas ➝ Filial)")

    mes_ano_tab4 = st.multiselect(
        "Selecione os Mês/Ano para cálculo da média",
        sorted(df["mes_ano"].dropna().unique()),
        key="mes_ano_media_tab4"
    )

    # ==============================
    # DESPESA ATUAL
    # ==============================

    df_despesa_topo = df_filtrado[
        df_filtrado["movimento"] == "Despesa"
    ].copy()

    despesa_atual_group = df_despesa_topo.groupby(
        ['grupo','razao','pcontas','filial']
    )['valor'].sum().reset_index()

    despesa_atual_group.rename(
        columns={"valor": "Despesa_Atual"},
        inplace=True
    )

    # ==============================
    # BASE PARA MÉDIA
    # ==============================

    df_base_media = df.copy()

    for sel, col in zip(
        [grupo_sel, razao_sel, pcontas_sel, filial_sel],
        ["grupo","razao","pcontas","filial"]
    ):
        if sel:
            df_base_media = df_base_media[df_base_media[col].isin(sel)]

    df_media_despesas = df_base_media[
        df_base_media["movimento"] == "Despesa"
    ].copy()

    if mes_ano_tab4:
        df_media_despesas = df_media_despesas[
            df_media_despesas["mes_ano"].isin(mes_ano_tab4)
        ]

    if not df_media_despesas.empty:

        agrupado = df_media_despesas.groupby(
            ['grupo','razao','pcontas','filial']
        )

        df_media = agrupado.agg(
            Total_Despesa=('valor','sum'),
            Qtd_Meses=('mes_ano','nunique')
        ).reset_index()

        df_media["Meta_Despesa"] = (
            df_media["Total_Despesa"] / df_media["Qtd_Meses"]
        )

        # ==============================
        # MERGE
        # ==============================

        df_final = df_media.merge(
            despesa_atual_group,
            on=['grupo','razao','pcontas','filial'],
            how="left"
        )

        df_final["Despesa_Atual"] = df_final["Despesa_Atual"].fillna(0)

        # ==============================
        # DIFERENÇA E VARIAÇÃO
        # ==============================

        df_final["Diferenca_R$"] = (
            df_final["Despesa_Atual"] - df_final["Meta_Despesa"]
        )

        df_final["Variação_%"] = df_final.apply(
            lambda row: (
                ((row["Despesa_Atual"] - row["Meta_Despesa"]) / row["Meta_Despesa"]) * 100
                if row["Meta_Despesa"] != 0 else 0
            ),
            axis=1
        )

        # ==============================
        # RESUMO EXECUTIVO (RESPEITA FILTROS)
        # ==============================

        df_resumo = df_final.copy()

        # aplica filtros de cima
        if grupo_sel:
            df_resumo = df_resumo[df_resumo["grupo"].isin(grupo_sel)]

        if razao_sel:
            df_resumo = df_resumo[df_resumo["razao"].isin(razao_sel)]

        if filial_sel:
            df_resumo = df_resumo[df_resumo["filial"].isin(filial_sel)]

        if pcontas_sel:
            df_resumo = df_resumo[df_resumo["pcontas"].isin(pcontas_sel)]

        if movimento_sel:
            df_resumo = df_resumo[df_resumo["movimento"].isin(movimento_sel)]

        if tipo_conta_sel:
            df_resumo = df_resumo[df_resumo["tipo_conta"].isin(tipo_conta_sel)]

        # ==============================
        # CÁLCULOS
        # ==============================

        total_meta = df_resumo["Meta_Despesa"].sum()
        total_atual = df_resumo["Despesa_Atual"].sum()
        total_diferenca = df_resumo["Diferenca_R$"].sum()

        total_variacao = (
            ((total_atual - total_meta) / total_meta) * 100
            if total_meta != 0 else 0
        )

        # ==============================
        # EXIBIÇÃO
        # ==============================

        st.markdown("### 📌 Resumo Geral")

        col1, col2, col3 = st.columns(3)

        col1.metric("💰 Meta Total", formatar_real(total_meta))
        col2.metric("💳 Despesa Atual Total", formatar_real(total_atual))
        col3.metric(
            "📊 Diferença Total",
            formatar_real(total_diferenca),
            f"{total_variacao:.2f}%"
        )

        # ==============================
        # MATRIZ HIERÁRQUICA
        # ==============================

        linhas = []

        for grupo, df_grupo in df_final.groupby("grupo"):

            meta_grupo = df_grupo["Meta_Despesa"].sum()
            atual_grupo = df_grupo["Despesa_Atual"].sum()
            dif_grupo = df_grupo["Diferenca_R$"].sum()
            var_grupo = ((atual_grupo - meta_grupo) / meta_grupo * 100) if meta_grupo != 0 else 0

            linhas.append({
                "Meta_Despesa": meta_grupo,
                "Despesa_Atual": atual_grupo,
                "Diferenca_R$": dif_grupo,
                "Variação_%": var_grupo,
                "path": [grupo]
            })

            for pcontas, df_pc in df_grupo.groupby("pcontas"):

                    meta_pc = df_pc["Meta_Despesa"].sum()
                    atual_pc = df_pc["Despesa_Atual"].sum()
                    dif_pc = df_pc["Diferenca_R$"].sum()
                    var_pc = ((atual_pc - meta_pc) / meta_pc * 100) if meta_pc != 0 else 0

                    linhas.append({
                        "Meta_Despesa": meta_pc,
                        "Despesa_Atual": atual_pc,
                        "Diferenca_R$": dif_pc,
                        "Variação_%": var_pc,
                        "path": [grupo, pcontas]
                    })

                    for filial, df_filial in df_pc.groupby("filial"):

                        meta_filial = df_filial["Meta_Despesa"].sum()
                        atual_filial = df_filial["Despesa_Atual"].sum()
                        dif_filial = df_filial["Diferenca_R$"].sum()
                        var_filial = ((atual_filial - meta_filial) / meta_filial * 100) if meta_filial != 0 else 0

                        linhas.append({
                            "Meta_Despesa": meta_filial,
                            "Despesa_Atual": atual_filial,
                            "Diferenca_R$": dif_filial,
                            "Variação_%": var_filial,
                            "path": [grupo, pcontas, filial]
                        })

        matriz_df = pd.DataFrame(linhas)

        # ==============================
        # AGGRID CONFIG
        # ==============================

        cell_style = JsCode("""
        function(params) {
            if (params.value > 0) {
                return { color: "#dc2626", fontWeight: "bold" };
            }
            if (params.value < 0) {
                return { color: "#16a34a", fontWeight: "bold" };
            }
            return {};
        }
        """)

        gb = GridOptionsBuilder.from_dataframe(matriz_df)

        gb.configure_column("path", hide=True)

        for col in ["Meta_Despesa", "Despesa_Atual", "Diferenca_R$", "Variação_%"]:
            gb.configure_column(
                col,
                type=["numericColumn"],
                valueFormatter=(
                    "x.toLocaleString('pt-BR', {style:'currency', currency:'BRL'})"
                    if col != "Variação_%"
                    else "x.toFixed(2) + '%'"
                ),
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
            matriz_df,
            gridOptions=gridOptions,
            enable_enterprise_modules=True,
            fit_columns_on_grid_load=True,
            theme="streamlit",
            allow_unsafe_jscode=True,
            height=650
        )

    else:
        st.warning("Nenhuma despesa encontrada para os filtros selecionados.")
