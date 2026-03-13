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

response = supabase.table("vw_fcontas_geral_py").select("*").execute()
df = pd.DataFrame(response.data)

if "filial" in df.columns:
    df = df.rename(columns={"filial": "filial"})

# 🚫 Ocultar empresa 7
df = df[df["id_empresa"] != 7]

# ==============================
# TRATAR VALORES NULOS
# ==============================

df["razao"] = df.get("razao","Não informado")
df["filial"] = df["filial"].fillna("Não informado")
df["pcontas"] = df["pcontas"].fillna("Não informado")
df["status"] = df["status"].fillna("Não informado")

df['dt_vencimento'] = pd.to_datetime(df['dt_vencimento'], errors='coerce')
df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
df = df.dropna(subset=['dt_vencimento','valor'])
df['movimento'] = df['movimento'].str.strip().str.capitalize()


meses = {1:"Janeiro",2:"Fevereiro",3:"Março",4:"Abril",5:"Maio",6:"Junho",
         7:"Julho",8:"Agosto",9:"Setembro",10:"Outubro",11:"Novembro",12:"Dezembro"}

df['ano'] = df['dt_vencimento'].dt.year
df['mes'] = df['dt_vencimento'].dt.month
df['nome_mes'] = df['mes'].map(meses)
df['mes_ano'] = df['dt_vencimento'].dt.to_period('M').astype(str)

ordem_meses = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho",
               "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]

# ==============================
# FILTROS
# ==============================
# ==============================
# FILTROS CORPORATIVOS EM CASCATA
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

# ==============================
# FILIAL (DEPENDENTE DA RAZÃO)
# ==============================

df_filial = df_base.copy()

if razao_sel:
    df_filial = df_filial[df_filial["razao"].isin(razao_sel)]

filial_options = sorted(df_filial["filial"].dropna().unique())

filial_sel = col_f2.multiselect(
    "Filial",
    options=filial_options,
    key="filial"
)

# ==============================
# DEMAIS FILTROS
# ==============================

movimento_sel = col_f3.multiselect(
    "Movimento",
    sorted(df_filial["movimento"].dropna().unique()),
    key="movimento"
)

status_sel = col_f4.multiselect(
    "Status",
    sorted(df_filial["status"].dropna().unique()),
    key="status"
)
pcontas_sel = col_f5.multiselect(
    "PContas",
    sorted(df_filial["pcontas"].dropna().unique()),
    key="pcontas"
)

# ==============================
# APLICAR FILTROS
# ==============================

df_filtrado = df.copy()
for key, sel, col in zip(
    ["ano","mes","razao","filial","movimento","status","pcontas"],
    [ano_sel,mes_sel,razao_sel,filial_sel,movimento_sel,status_sel,pcontas_sel],
    ["ano","nome_mes","razao","filial","movimento","status","pcontas"]
):
    if sel:
        df_filtrado = df_filtrado[df_filtrado[col].isin(sel)]

# ==============================
# CARDS
# ==============================

totais_filtrados = df_filtrado.groupby('movimento')['valor'].sum()
receita_filtrada = totais_filtrados.get('Receita',0)
despesa_filtrada = totais_filtrados.get('Despesa',0)
resultado_filtrado = receita_filtrada - despesa_filtrada

col1,col2,col3 = st.columns(3)

col1.markdown(f"""<div class="card"><div class="card-title">💰 Receita (Filtro)</div><div class="card-value" style="color:#16a34a;">{formatar_real(receita_filtrada)}</div></div>""", unsafe_allow_html=True)

col2.markdown(f"""<div class="card"><div class="card-title">💸 Despesa (Filtro)</div><div class="card-value" style="color:#dc2626;">{formatar_real(despesa_filtrada)}</div></div>""", unsafe_allow_html=True)

cor_res = "#16a34a" if resultado_filtrado>=0 else "#dc2626"
col3.markdown(f"""<div class="card"><div class="card-title">📊 Resultado</div><div class="card-value" style="color:{cor_res};">{formatar_real(resultado_filtrado)}</div></div>""", unsafe_allow_html=True)

# ==============================
# TABS
# ==============================

tab1, tab2, tab3,tab4,tab5 = st.tabs(["📊 Dashboard Principal","📈 Média de Despesas","📊 DRE Mensal","📊 Matriz de Despesas (Grupo + Razão + Pcontas + Filial)","💰 Meta de Faturamento"])

with tab1:
    with st.expander("📅 Valores por Mês/Ano"):
        df_mes_ano = df_filtrado.groupby(['mes_ano', 'movimento'])['valor'].sum().unstack(fill_value=0)
        df_mes_ano['Receita'] = df_mes_ano.get('Receita', 0)
        df_mes_ano['Despesa'] = df_mes_ano.get('Despesa', 0)
        df_mes_ano['Resultado'] = df_mes_ano['Receita'] - df_mes_ano['Despesa']


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
            ['razao', 'filial', 'status','ano', 'nome_mes', 'pcontas', 'movimento'],
            dropna=False
        )['valor'].sum().unstack(fill_value=0).reset_index()

        # Garantir que as colunas existam
        for col in ["Receita", "Despesa"]:
            if col not in df_detalhe.columns:
                df_detalhe[col] = 0

        # Criar Resultado (opcional, mas recomendo manter padrão)
        df_detalhe["Resultado"] = df_detalhe["Receita"] - df_detalhe["Despesa"]


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
    df["dt_vencimento"].dt.year.astype(str)
    + "-S"
    + df["dt_vencimento"].dt.isocalendar().week.astype(str).str.zfill(2)
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
        ['razao','filial','status','pcontas']
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
        [razao_sel, filial_sel, movimento_sel, pcontas_sel],
        ["razao","filial","movimento","status","pcontas"]
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
            ['razao','filial','status','movimento','pcontas']
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
            on=['razao','filial','status','pcontas'],
            how="outer"
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
        index=["razao", "filial", "status", "movimento"],
        columns=["ano", "nome_mes"],
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

    anos_existentes = sorted(df_filtrado["ano"].dropna().unique())

    colunas_ordenadas = []

    for ano in anos_existentes:
        for mes in ordem_meses:
            if (ano, mes) in df_pivot.columns:
                colunas_ordenadas.append((ano, mes))

    df_pivot = df_pivot[colunas_ordenadas]

    # criar nome das colunas
    df_pivot.columns = [f"{ano}_{mes}" for ano, mes in df_pivot.columns]

    meses_existentes = df_pivot.columns.tolist()

    linhas = []
    # ==============================
    # HIERARQUIA
    # ==============================

    for razao, df_razao in df_pivot.groupby(level="razao"):

        receita_razao = df_razao[df_razao.index.get_level_values("movimento") == "Receita"].sum()
        resultado_razao = receita_razao

        row_razao = {mes: float(resultado_razao.get(mes, 0)) for mes in meses_existentes}
        row_razao["TOTAL"] = float(resultado_razao.sum())
        row_razao["path"] = [razao]
        linhas.append(row_razao)

        # ----------------------------
        # FILIAL
        # ----------------------------

        for filial, df_filial in df_razao.groupby(level="filial"):

            receita = df_filial[df_filial.index.get_level_values("movimento") == "Receita"].sum()
            resultado = receita

            row_filial = {mes: float(resultado.get(mes, 0)) for mes in meses_existentes}
            row_filial["TOTAL"] = float(resultado.sum())
            row_filial["path"] = [razao, filial]
            linhas.append(row_filial)

            # ----------------------------
            # MOVIMENTO
            # ----------------------------

            for movimento, df_mov in df_filial.groupby(level="movimento"):

                row_det = {mes: float(df_mov[mes].sum()) for mes in meses_existentes}
                row_det["TOTAL"] = float(df_mov.sum().sum())
                row_det["path"] = [razao, filial, movimento]
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

    st.subheader("📊 Matriz de Despesas (Pcontas ➝ Razão ➝ Filial)")

    mes_ano_tab4 = st.multiselect(
        "Selecione os Mês/Ano para cálculo da média",
        sorted(df["mes_ano"].dropna().unique()),
        key="mes_ano_media_tab4"
    )

    # ==============================
    # BASE META (IGNORA FILTRO DE MÊS)
    # ==============================

    df_meta_base = df.copy()

    if razao_sel:
        df_meta_base = df_meta_base[df_meta_base["razao"].isin(razao_sel)]

    if filial_sel:
        df_meta_base = df_meta_base[df_meta_base["filial"].isin(filial_sel)]

    if status_sel:
        df_meta_base = df_meta_base[df_meta_base["status"].isin(status_sel)]

    if pcontas_sel:
        df_meta_base = df_meta_base[df_meta_base["pcontas"].isin(pcontas_sel)]

    df_meta_base = df_meta_base[df_meta_base["movimento"] == "Despesa"]

    # ==============================
    # FILTRO MESES MÉDIA
    # ==============================

    if mes_ano_tab4:
        df_meta_base = df_meta_base[
            df_meta_base["mes_ano"].isin(mes_ano_tab4)
        ]

    # ==============================
    # CALCULO META
    # ==============================

    df_meta = (
        df_meta_base
        .groupby(["pcontas","razao","filial"])
        .agg(
            Total_Despesa=("valor","sum"),
            Meses=("mes_ano","nunique")
        )
        .reset_index()
    )

    df_meta["Meta_Despesa"] = (
        df_meta["Total_Despesa"] / df_meta["Meses"]
    )

    # ==============================
    # DESPESA ATUAL
    # ==============================

    df_atual = df_filtrado.copy()

    df_atual = df_atual[
        df_atual["movimento"] == "Despesa"
    ]

    df_atual = (
        df_atual
        .groupby(["pcontas", "razao", "filial"], as_index=False)
        ["valor"]
        .sum()
    )

    df_atual.rename(
        columns={"valor": "Despesa_Atual"},
        inplace=True
    )

    # ==============================
    # STATUS DA DESPESA
    # ==============================

    df_status = (
        df_filtrado[df_filtrado["movimento"] == "Despesa"]
        .groupby(["pcontas","razao","filial"])["status"]
        .first()
        .reset_index()
    )

    # ==============================
    # MERGE
    # ==============================

    df_final = df_meta.merge(
        df_atual,
        on=["pcontas","razao","filial"],
        how="outer"
    )

    df_final = df_final.merge(
        df_status,
        on=["pcontas","razao","filial"],
        how="left"
    )

    df_final["Despesa_Atual"] = df_final["Despesa_Atual"].fillna(0)
    df_final["Meta_Despesa"] = df_final["Meta_Despesa"].fillna(0)

    # ==============================
    # DIFERENÇA
    # ==============================

    df_final["Diferenca_R$"] = (
        df_final["Despesa_Atual"] - df_final["Meta_Despesa"]
    )

    df_final["Variação_%"] = df_final.apply(
        lambda row:
        ((row["Despesa_Atual"] - row["Meta_Despesa"]) / row["Meta_Despesa"] * 100)
        if row["Meta_Despesa"] != 0 else 0,
        axis=1
    )

    # ==============================
    # RESUMO
    # ==============================

    total_meta = df_final["Meta_Despesa"].sum()
    total_atual = df_final["Despesa_Atual"].sum()
    total_dif = df_final["Diferenca_R$"].sum()

    variacao_total = (
        ((total_atual-total_meta)/total_meta)*100
        if total_meta != 0 else 0
    )

    st.markdown("### 📌 Resumo Geral")

    c1,c2,c3 = st.columns(3)

    c1.metric("💰 Meta Total", formatar_real(total_meta))
    c2.metric("💳 Despesa Atual", formatar_real(total_atual))
    c3.metric(
        "📊 Diferença",
        formatar_real(total_dif),
        f"{variacao_total:.2f}%"
    )

    # ==============================
    # MATRIZ HIERÁRQUICA
    # ==============================

    linhas = []

    for pcontas, df_pc in df_final.groupby("pcontas"):

        linhas.append({
            "Status":"",
            "Meta_Despesa": df_pc["Meta_Despesa"].sum(),
            "Despesa_Atual": df_pc["Despesa_Atual"].sum(),
            "Diferenca_R$": df_pc["Diferenca_R$"].sum(),
            "Variação_%": df_pc["Variação_%"].mean(),
            "path":[pcontas]
        })

        for razao, df_r in df_pc.groupby("razao"):

            linhas.append({
                "Status":"",
                "Meta_Despesa": df_r["Meta_Despesa"].sum(),
                "Despesa_Atual": df_r["Despesa_Atual"].sum(),
                "Diferenca_R$": df_r["Diferenca_R$"].sum(),
                "Variação_%": df_r["Variação_%"].mean(),
                "path":[pcontas,razao]
            })

            for filial, df_f in df_r.groupby("filial"):

                linhas.append({
                    "Status": df_f["status"].iloc[0] if not df_f.empty else "",
                    "Meta_Despesa": df_f["Meta_Despesa"].sum(),
                    "Despesa_Atual": df_f["Despesa_Atual"].sum(),
                    "Diferenca_R$": df_f["Diferenca_R$"].sum(),
                    "Variação_%": df_f["Variação_%"].mean(),
                    "path":[pcontas,razao,filial]
                })

    matriz_df = pd.DataFrame(linhas)

    # ==============================
    # AGGRID
    # ==============================

    cell_style = JsCode("""
    function(params) {
        if (params.value > 0) {
            return {color: '#dc2626', fontWeight:'bold'};
        }
        if (params.value < 0) {
            return {color: '#16a34a', fontWeight:'bold'};
        }
        return {};
    }
    """)

    status_style = JsCode("""
    function(params) {

        if (params.value == 'Pago') {
            return {
                'backgroundColor': '#16a34a',
                'color': 'white',
                'fontWeight': 'bold',
                'textAlign': 'center'
            }
        }

        if (params.value == 'Vencido') {
            return {
                'backgroundColor': '#dc2626',
                'color': 'white',
                'fontWeight': 'bold',
                'textAlign': 'center'
            }
        }

        if (params.value == 'Em aberto') {
            return {
                'backgroundColor': '#fb923c',
                'color': 'black',
                'fontWeight': 'bold',
                'textAlign': 'center'
            }
        }

        return {}
    }
    """)

    gb = GridOptionsBuilder.from_dataframe(matriz_df)

    gb.configure_column("path", hide=True)

    gb.configure_column(
        "Status",
        header_name="Status",
        width=120,
        cellStyle=status_style
    )

    for col in ["Meta_Despesa","Despesa_Atual","Diferenca_R$","Variação_%"]:

        gb.configure_column(
            col,
            type=["numericColumn"],
            valueFormatter=(
                "x.toLocaleString('pt-BR',{style:'currency',currency:'BRL'})"
                if col!="Variação_%"
                else "x.toFixed(2)+'%'"
            ),
            cellStyle=cell_style
        )

    gb.configure_grid_options(
        treeData=True,
        animateRows=True,
        groupDefaultExpanded=0,
        getDataPath=JsCode("function(data){return data.path;}")
    )

    AgGrid(
        matriz_df,
        gridOptions=gb.build(),
        enable_enterprise_modules=True,
        fit_columns_on_grid_load=True,
        theme="streamlit",
        allow_unsafe_jscode=True,
        height=650
    )


with tab5:

    st.subheader("💰 Matriz de Faturamento (Grupo ➝ Pcontas ➝ Filial)")

    mes_ano_tab5 = st.multiselect(
        "Selecione os Mês/Ano para cálculo da média de faturamento",
        sorted(df["mes_ano"].dropna().unique()),
        key="mes_ano_media_tab5"
    )

    # ==============================
    # FATURAMENTO ATUAL
    # ==============================

    df_receita_atual = df_filtrado[
        df_filtrado["movimento"] == "Receita"
    ].copy()

    faturamento_atual_group = df_receita_atual.groupby(
        ['pcontas','filial']
    )['valor'].sum().reset_index()

    faturamento_atual_group.rename(
        columns={"valor": "Faturamento_Atual"},
        inplace=True
    )

    # ==============================
    # BASE PARA MÉDIA
    # ==============================

    df_base_media = df.copy()

    for sel, col in zip(
        [pcontas_sel, filial_sel],
        ["pcontas","filial"]
    ):
        if sel:
            df_base_media = df_base_media[df_base_media[col].isin(sel)]

    df_media_receita = df_base_media[
        df_base_media["movimento"] == "Receita"
    ].copy()

    if mes_ano_tab5:
        df_media_receita = df_media_receita[
            df_media_receita["mes_ano"].isin(mes_ano_tab5)
        ]

    if not df_media_receita.empty:

        agrupado = df_media_receita.groupby(
            ['pcontas','filial']
        )

        df_media = agrupado.agg(
            Total_Receita=('valor','sum'),
            Qtd_Meses=('mes_ano','nunique')
        ).reset_index()

        df_media["Meta_Faturamento"] = (
            df_media["Total_Receita"] / df_media["Qtd_Meses"]
        )

        # ==============================
        # MERGE
        # ==============================

        df_final = df_media.merge(
            faturamento_atual_group,
            on=['pcontas','filial'],
            how="outer"
        )

        df_final["Faturamento_Atual"] = df_final["Faturamento_Atual"].fillna(0)
        df_final["Meta_Faturamento"] = df_final["Meta_Faturamento"].fillna(0)
        df_final["Faturamento_Atual"] = df_final["Faturamento_Atual"].fillna(0)

        # ==============================
        # DIFERENÇA
        # ==============================

        df_final["Diferenca_R$"] = (
            df_final["Faturamento_Atual"] - df_final["Meta_Faturamento"]
        )

        # ==============================
        # VARIAÇÃO %
        # ==============================

        df_final["Variação_%"] = df_final.apply(
            lambda row: (
                ((row["Faturamento_Atual"] - row["Meta_Faturamento"]) / row["Meta_Faturamento"]) * 100
                if row["Meta_Faturamento"] != 0 else 0
            ),
            axis=1
        )

        # ==============================
        # ATINGIMENTO DA META
        # ==============================

        df_final["Atingimento_%"] = df_final.apply(
            lambda row: (
                (row["Faturamento_Atual"] / row["Meta_Faturamento"]) * 100
                if row["Meta_Faturamento"] != 0 else 0
            ),
            axis=1
        )

        # ==============================
        # RESUMO EXECUTIVO
        # ==============================

        total_meta = df_final["Meta_Faturamento"].sum()
        total_atual = df_final["Faturamento_Atual"].sum()
        total_diferenca = df_final["Diferenca_R$"].sum()

        total_variacao = (
            ((total_atual - total_meta) / total_meta) * 100
            if total_meta != 0 else 0
        )

        st.markdown("### 📌 Resumo Geral")

        col1, col2, col3 = st.columns(3)

        col1.metric("💰 Meta Total", formatar_real(total_meta))
        col2.metric("📈 Faturamento Atual", formatar_real(total_atual))
        col3.metric(
            "📊 Diferença",
            formatar_real(total_diferenca),
            f"{total_variacao:.2f}%"
        )

        # ==============================
        # MATRIZ HIERÁRQUICA
        # ==============================

        linhas = []

        for pcontas, df_pc in df_final.groupby("pcontas"):

                meta_pc = df_pc["Meta_Faturamento"].sum()
                atual_pc = df_pc["Faturamento_Atual"].sum()
                dif_pc = df_pc["Diferenca_R$"].sum()
                var_pc = ((atual_pc - meta_pc) / meta_pc * 100) if meta_pc != 0 else 0

                linhas.append({
                    "Meta_Faturamento": meta_pc,
                    "Faturamento_Atual": atual_pc,
                    "Diferenca_R$": dif_pc,
                    "Variação_%": var_pc,
                    "path": [pcontas]
                })

                for filial, df_filial in df_pc.groupby("filial"):

                    meta_filial = df_filial["Meta_Faturamento"].sum()
                    atual_filial = df_filial["Faturamento_Atual"].sum()
                    dif_filial = df_filial["Diferenca_R$"].sum()
                    var_filial = ((atual_filial - meta_filial) / meta_filial * 100) if meta_filial != 0 else 0

                    linhas.append({
                        "Meta_Faturamento": meta_filial,
                        "Faturamento_Atual": atual_filial,
                        "Diferenca_R$": dif_filial,
                        "Variação_%": var_filial,
                        "path": [pcontas, filial]
                    })

        matriz_df = pd.DataFrame(linhas)

        # ==============================
        # AGGRID
        # ==============================

        cell_style = JsCode("""
        function(params) {

            if (params.value > 0) {
                return { color: "#16a34a", fontWeight: "bold" };
            }

            if (params.value < 0) {
                return { color: "#dc2626", fontWeight: "bold" };
            }

            return {};
        }
        """)

        gb = GridOptionsBuilder.from_dataframe(matriz_df)

        gb.configure_column("path", hide=True)

        for col in ["Meta_Faturamento", "Faturamento_Atual", "Diferenca_R$", "Variação_%"]:
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
        st.warning("Nenhuma receita encontrada para os filtros selecionados.")
