import streamlit as st
import pandas as pd
from decimal import Decimal
from io import BytesIO
from pathlib import Path

from conciliacao import conciliar, preparar_lancamentos


PASTA_PROJETO = Path(__file__).resolve().parent
PASTA_ENTRADA = PASTA_PROJETO / "dados_entrada"

st.set_page_config(page_title="Conciliação bancária", page_icon="↔", layout="wide")

st.markdown(
    """
    <style>
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1500px;
        }
        body {
            background: #020817;
        }
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(180, 136, 75, 0.14), transparent 28%),
                radial-gradient(circle at top right, rgba(37, 99, 235, 0.16), transparent 30%),
                linear-gradient(180deg, #020817 0%, #0f172a 100%);
            color: #e2e8f0;
            font-family: "Segoe UI", "Inter", "Helvetica Neue", Arial, sans-serif;
        }
        div[data-testid="stHeader"] {
            background: rgba(15, 23, 42, 0.3);
            box-shadow: none;
        }
        .stMarkdown, .stCaption, .stSelectbox label, .stNumberInput label, .stCheckbox label, .stRadio label,
        .stFileUploader label, .stDataFrame, .stMetric label, .stMetric [data-testid="stMetricValue"] {
            font-family: "Segoe UI", "Inter", "Helvetica Neue", Arial, sans-serif;
        }
        .app-header {
            background: linear-gradient(135deg, #0b1220 0%, #12233d 30%, #1d4ed8 52%, #0f172a 100%);
            border: 1px solid rgba(148, 163, 184, 0.25);
            border-radius: 24px;
            padding: 1.8rem 1.9rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 20px 44px rgba(15, 23, 42, 0.45);
            position: relative;
            overflow: hidden;
        }
        .app-header::before {
            content: "";
            position: absolute;
            inset: 0 auto 0 0;
            width: 5px;
            background: linear-gradient(180deg, rgba(191,219,254,0.9), rgba(147,197,253,0));
        }
        .app-header::after {
            content: "";
            position: absolute;
            inset: 0;
            background: linear-gradient(120deg, rgba(255,255,255,0.08), transparent 40%, rgba(255,255,255,0.04));
            pointer-events: none;
        }
        .eyebrow {
            display: inline-block;
            font-size: 0.76rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: rgba(191, 219, 254, 0.95);
            font-weight: 700;
            margin-bottom: 0.55rem;
            font-family: "Segoe UI", "Inter", "Helvetica Neue", Arial, sans-serif;
        }
        .app-header h1 {
            color: #f8fafc !important;
            margin: 0;
            font-size: 2.5rem;
            font-weight: 800;
            letter-spacing: -0.05em;
            font-family: "Segoe UI", "Inter", "Helvetica Neue", Arial, sans-serif;
        }
        .app-header p {
            color: rgba(226, 232, 240, 0.9) !important;
            margin-top: 0.6rem;
            margin-bottom: 0;
            font-size: 1.05rem;
            line-height: 1.55;
            font-family: "Segoe UI", "Inter", "Helvetica Neue", Arial, sans-serif;
        }
        .status-badge {
            display: inline-block;
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.18), rgba(59, 130, 246, 0.12));
            border: 1px solid rgba(110, 231, 183, 0.45);
            color: #dcfce7;
            border-radius: 999px;
            padding: 0.55rem 0.9rem;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            box-shadow: 0 0 18px rgba(16, 185, 129, 0.18);
            font-family: "Segoe UI", "Inter", "Helvetica Neue", Arial, sans-serif;
        }
        .summary-chip {
            background: rgba(15, 23, 42, 0.75);
            border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 999px;
            padding: 0.55rem 0.8rem;
            color: #dbeafe;
            font-size: 0.77rem;
            font-weight: 600;
            letter-spacing: 0.03em;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.03);
            font-family: "Segoe UI", "Inter", "Helvetica Neue", Arial, sans-serif;
        }
        .summary-strip {
            display: flex;
            gap: 0.75rem;
            flex-wrap: wrap;
            margin: 1rem 0 1.5rem 0;
        }
        .summary-chip {
            background: rgba(15, 23, 42, 0.7);
            border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 999px;
            padding: 0.5rem 0.8rem;
            color: #dbeafe;
            font-size: 0.77rem;
            font-weight: 600;
            letter-spacing: 0.03em;
            font-family: "Segoe UI", "Inter", "Helvetica Neue", Arial, sans-serif;
        }
        .section-panel {
            background: linear-gradient(180deg, rgba(15, 23, 42, 0.96), rgba(17, 24, 39, 0.97));
            border: 1px solid rgba(148, 163, 184, 0.17);
            border-radius: 18px;
            padding: 1.15rem 1.25rem;
            margin-bottom: 1.25rem;
            box-shadow: 0 14px 30px rgba(2, 6, 23, 0.35);
            border-left: 3px solid rgba(96, 165, 250, 0.9);
        }
        .section-panel h3 {
            margin-top: 0;
            margin-bottom: 0.8rem;
            color: #f8fafc;
            font-size: 1.1rem;
            font-weight: 700;
            font-family: "Segoe UI", "Inter", "Helvetica Neue", Arial, sans-serif;
        }
        .stSelectbox > div, .stRadio > div, .stFileUploader, .stNumberInput > div {
            background: rgba(15, 23, 42, 0.92);
            border-radius: 12px;
            border: 1px solid rgba(148, 163, 184, 0.22);
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.04);
        }
        .stSelectbox [data-baseweb="select"] input,
        .stNumberInput input,
        .stTextInput input,
        .stTextArea textarea,
        .stSelectbox [data-baseweb="select"] div,
        .stSelectbox [data-baseweb="select"] span,
        .stSelectbox [data-baseweb="select"] label,
        .stSelectbox [data-baseweb="select"] button,
        .stSelectbox [data-baseweb="select"] [role="button"],
        .stSelectbox [data-baseweb="select"] [aria-expanded] {
            color: #111827 !important;
            background: rgba(255, 255, 255, 0.96) !important;
        }
        .stSelectbox [data-baseweb="select"] {
            background: rgba(255, 255, 255, 0.96) !important;
            border-radius: 12px;
        }
        .stSelectbox [data-baseweb="select"]:hover input,
        .stSelectbox [data-baseweb="select"]:hover div,
        .stSelectbox [data-baseweb="select"]:hover span,
        .stSelectbox [data-baseweb="select"]:hover label,
        .stSelectbox [data-baseweb="select"]:hover button,
        .stSelectbox [data-baseweb="select"]:hover [role="button"],
        .stSelectbox [data-baseweb="select"]:hover [aria-expanded],
        .stNumberInput input:hover,
        .stTextInput input:hover,
        .stTextArea textarea:hover {
            color: #f8fafc !important;
            background: rgba(15, 23, 42, 0.9) !important;
        }
        [data-testid="stFileUploaderDropzone"] {
            border: 1px dashed rgba(96, 165, 250, 0.7);
            border-radius: 12px;
            background: rgba(15, 23, 42, 0.7);
            transition: border-color 0.2s ease, transform 0.2s ease;
        }
        [data-testid="stFileUploaderDropzone:hover"] {
            border-color: rgba(147, 197, 253, 1);
            transform: translateY(-1px);
        }
        .stButton > button {
            border-radius: 12px;
            font-weight: 700;
            height: 2.9rem;
            background: linear-gradient(135deg, #2563eb, #60a5fa);
            color: white;
            border: none;
            box-shadow: 0 12px 24px rgba(37, 99, 235, 0.32);
            font-family: "Segoe UI", "Inter", "Helvetica Neue", Arial, sans-serif;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .stButton > button:hover {
            background: linear-gradient(135deg, #1d4ed8, #3b82f6);
            transform: translateY(-1px);
            box-shadow: 0 14px 26px rgba(37, 99, 235, 0.35);
        }
        .stDownloadButton > button {
            border-radius: 12px;
            background: rgba(15, 23, 42, 0.9);
            color: #e2e8f0;
            border: 1px solid rgba(148, 163, 184, 0.25);
            transition: border-color 0.2s ease, transform 0.2s ease;
        }
        .stDownloadButton > button:hover {
            border-color: rgba(96, 165, 250, 0.8);
            transform: translateY(-1px);
        }
        .stDataFrame {
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid rgba(148, 163, 184, 0.2);
        }
        [data-testid="stSidebar"] {
            background: rgba(2, 8, 23, 0.98);
        }
        [data-testid="stSidebar"] > div {
            background: rgba(2, 8, 23, 0.98);
            border-right: 1px solid rgba(148, 163, 184, 0.18);
        }
        body, .stApp, .stApp [data-testid="stAppViewContainer"], .stApp [data-testid="stVerticalBlock"] {
            color: #e2e8f0;
        }
        .stApp p, .stApp label, .stApp h1, .stApp h2, .stApp h3,
        .stApp h4, .stApp li, .stApp a, .stApp .stMarkdown, .stApp .stCaption {
            color: #f8fafc !important;
        }
        .stApp button, .stApp [role="button"], .stApp [data-testid="baseButton-secondary"],
        .stApp [data-testid="baseButton-primary"], .stApp [data-testid="baseButton-tertiary"] {
            color: #ffffff !important;
        }
        [data-testid="stSidebar"] * {
            color: #f8fafc !important;
        }
        [data-testid="stSidebar"] .stRadio > div, [data-testid="stSidebar"] .stCheckbox > div,
        [data-testid="stSidebar"] .stSelectbox > div, [data-testid="stSidebar"] .stNumberInput > div,
        [data-testid="stSidebar"] .stFileUploader > div {
            color: #f8fafc !important;
            background: rgba(15, 23, 42, 0.9) !important;
        }
        [data-testid="stSidebar"] .stRadio label, [data-testid="stSidebar"] .stCheckbox label,
        [data-testid="stSidebar"] .stSelectbox label, [data-testid="stSidebar"] .stNumberInput label,
        [data-testid="stSidebar"] .stFileUploader label {
            color: #f8fafc !important;
            opacity: 1 !important;
        }
        [data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] input,
        [data-testid="stSidebar"] .stNumberInput input,
        [data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] div,
        [data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] span,
        [data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] label {
            color: #111827 !important;
            background: rgba(255, 255, 255, 0.96) !important;
        }
        [data-testid="stSidebar"] .stSelectbox [data-baseweb="select"]:hover input,
        [data-testid="stSidebar"] .stSelectbox [data-baseweb="select"]:hover div,
        [data-testid="stSidebar"] .stSelectbox [data-baseweb="select"]:hover span,
        [data-testid="stSidebar"] .stSelectbox [data-baseweb="select"]:hover label {
            color: #f8fafc !important;
            background: rgba(15, 23, 42, 0.9) !important;
        }
        .stMetric {
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 14px;
            padding: 0.8rem 0.95rem;
        }
        .stMetric label {
            color: #cbd5e1 !important;
            font-size: 0.8rem;
            font-family: "Segoe UI", "Inter", "Helvetica Neue", Arial, sans-serif;
        }
        .stMetric [data-testid="stMetricValue"] {
            color: #f8fafc !important;
            font-family: "Segoe UI", "Inter", "Helvetica Neue", Arial, sans-serif;
        }
        div[data-testid="stVerticalBlockBorderWrapper"],
        div[data-testid="stVerticalBlock"] > div {
            background: transparent;
            border: none;
            box-shadow: none;
        }
        .stMarkdown, .stCaption, .stSelectbox label, .stNumberInput label, .stCheckbox label {
            color: #e2e8f0 !important;
        }
        [data-testid="stFileUploaderDropzone"] {
            border: 1px dashed rgba(96, 165, 250, 0.7);
            border-radius: 12px;
            background: rgba(15, 23, 42, 0.7);
        }
        .stAlert {
            border-radius: 12px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


st.markdown(
    """
    <div class="app-header">
        <div style="display:flex; justify-content:space-between; align-items:center; gap:1rem; flex-wrap:wrap; position:relative; z-index:1;">
            <div>
                <div class="eyebrow">Dashboard executivo</div>
                <h1>Conciliação bancária</h1>
                <p>Compare lançamentos do extrato e do relatório financeiro com revisão automatizada de discrepâncias.</p>
            </div>
            <div class="status-badge">Operação em dia</div>
        </div>
    </div>
    <div class="summary-strip">
        <div class="summary-chip">📊 Revisão automatizada</div>
        <div class="summary-chip">🧾 Fluxo de dados em tempo real</div>
        <div class="summary-chip">✅ Alinhamento de valores e datas</div>
    </div>
    """,
    unsafe_allow_html=True,
)


def ler_arquivo(arquivo) -> pd.DataFrame:
    extensao = Path(arquivo.name).suffix.lower()
    if extensao == ".xlsx":
        return pd.read_excel(arquivo)
    if extensao == ".csv":
        try:
            return pd.read_csv(arquivo, sep=None, engine="python", encoding="utf-8-sig")
        except UnicodeDecodeError:
            arquivo.seek(0)
            return pd.read_csv(arquivo, sep=None, engine="python", encoding="cp1252")
    raise ValueError("Formato não suportado. Envie um arquivo CSV ou Excel (.xlsx).")


def coluna_inicial(colunas, sugestoes):
    for coluna in colunas:
        if str(coluna).strip().lower() in sugestoes:
            return coluna
    return colunas[0]


def configurar_lado(titulo, dados, chave):
    st.markdown(f"<div class='section-panel'><h3 style='margin-top:0; margin-bottom:0.7rem;'>{titulo}</h3></div>", unsafe_allow_html=True)
    colunas = list(dados.columns)
    if not colunas:
        st.error(f"O arquivo de {titulo.lower()} não contém colunas.")
        return None

    coluna_data = st.selectbox(
        "Coluna de data",
        colunas,
        index=colunas.index(coluna_inicial(colunas, {"data", "date", "dt"})),
        key=f"{chave}_data",
    )
    coluna_valor = st.selectbox(
        "Coluna de valor",
        colunas,
        index=colunas.index(coluna_inicial(colunas, {"valor", "value", "amount", "valor_liquido"})),
        key=f"{chave}_valor",
    )
    coluna_descricao = st.selectbox(
        "Coluna de histórico (opcional)",
        ["(sem histórico)", *colunas],
        index=(colunas.index(coluna_inicial(colunas, {"historico", "descrição", "descricao", "description", "memo"})) + 1)
        if any(str(coluna).strip().lower() in {"historico", "descrição", "descricao", "description", "memo"} for coluna in colunas)
        else 0,
        key=f"{chave}_descricao",
    )
    usa_debito_credito = st.checkbox(
        "Valores em colunas separadas de débito e crédito",
        key=f"{chave}_separados",
    )
    coluna_debito = coluna_credito = None
    if usa_debito_credito:
        debito, credito = st.columns(2)
        coluna_debito = debito.selectbox("Débito", colunas, key=f"{chave}_debito")
        coluna_credito = credito.selectbox("Crédito", colunas, key=f"{chave}_credito")

    preparados = preparar_lancamentos(
        dados,
        coluna_data,
        coluna_valor,
        None if coluna_descricao == "(sem histórico)" else coluna_descricao,
        coluna_debito,
        coluna_credito,
    )
    configuracao = (coluna_data, coluna_valor, coluna_descricao, coluna_debito, coluna_credito)
    return preparados, configuracao


with st.sidebar:
    st.markdown("<h2 style='margin-top: 0; margin-bottom: 0.5rem; color: #f8fafc; font-family: Segoe UI, Inter, Arial, sans-serif;'>Configuração</h2>", unsafe_allow_html=True)
    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    origem = st.radio("Dados de entrada", ["Usar demonstração", "Enviar arquivos"])

if origem == "Usar demonstração":
    banco_raw = pd.read_csv(PASTA_ENTRADA / "extrato_bancario.csv")
    financeiro_raw = pd.read_csv(PASTA_ENTRADA / "relatorio_financeiro.csv")
else:
    arquivo_banco, arquivo_financeiro = st.columns(2)
    with arquivo_banco:
        upload_banco = st.file_uploader("Extrato bancário", type=["csv", "xlsx", "xls"])
    with arquivo_financeiro:
        upload_financeiro = st.file_uploader("Relatório financeiro", type=["csv", "xlsx", "xls"])
    if not upload_banco or not upload_financeiro:
        st.info("Envie os dois arquivos para configurar a conciliação.")
        st.stop()
    try:
        banco_raw = ler_arquivo(upload_banco)
        financeiro_raw = ler_arquivo(upload_financeiro)
    except (ValueError, ImportError) as erro:
        st.error(str(erro))
        st.stop()

st.markdown("<div class='section-panel'>", unsafe_allow_html=True)
esquerda, direita = st.columns(2)
with esquerda:
    configuracao_banco = configurar_lado("Extrato bancário", banco_raw, "banco")
with direita:
    configuracao_financeiro = configurar_lado("Relatório financeiro", financeiro_raw, "financeiro")
st.markdown("</div>", unsafe_allow_html=True)

banco, assinatura_banco = configuracao_banco if configuracao_banco else (None, ())
financeiro, assinatura_financeiro = configuracao_financeiro if configuracao_financeiro else (None, ())

st.markdown("<div class='section-panel'>", unsafe_allow_html=True)
coluna_tolerancia, coluna_valor = st.columns(2)
tolerancia_dias = coluna_tolerancia.number_input(
    "Tolerância de data (dias)", min_value=0, max_value=30, value=3, step=1
)
tolerancia_valor_centavos = coluna_valor.number_input(
    "Tolerância de valor", min_value=0.0, value=0.0, step=0.01, format="%.2f"
)
st.caption("Débitos são tratados como saídas negativas e créditos como entradas positivas. Confirme que ambos os arquivos seguem a mesma convenção.")
st.markdown("</div>", unsafe_allow_html=True)

if st.button("Conciliar", type="primary", disabled=banco is None or financeiro is None):
    st.session_state["resultado_conciliacao"] = conciliar(
        banco,
        financeiro,
        tolerancia_dias=int(tolerancia_dias),
        tolerancia_valor=Decimal(str(tolerancia_valor_centavos)),
    )
    st.session_state["parametros_conciliacao"] = (
        origem,
        int(tolerancia_dias),
        float(tolerancia_valor_centavos),
        assinatura_banco,
        assinatura_financeiro,
    )

resultado = st.session_state.get("resultado_conciliacao")
parametros = st.session_state.get("parametros_conciliacao")
parametros_atuais = (
    origem,
    int(tolerancia_dias),
    float(tolerancia_valor_centavos),
    assinatura_banco,
    assinatura_financeiro,
)
if resultado is not None and parametros == parametros_atuais:
    totais = resultado["Status"].value_counts()
    contadores = {
        "Conciliados": int(totais.get("Conciliado", 0)),
        "Só no banco": int(totais.get("Apenas no banco", 0)),
        "Só no financeiro": int(totais.get("Apenas no financeiro", 0)),
        "Inválidos": int(totais.get("Inválido", 0)),
    }

    st.markdown("<div class='section-panel'>", unsafe_allow_html=True)
    metricas = st.columns(4)
    metricas[0].metric("Conciliados", contadores["Conciliados"])
    metricas[1].metric("Só no banco", contadores["Só no banco"])
    metricas[2].metric("Só no financeiro", contadores["Só no financeiro"])
    metricas[3].metric("Inválidos", contadores["Inválidos"])
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='section-panel'>", unsafe_allow_html=True)
    status_filtro = st.selectbox(
        "Filtrar resultado",
        ["Todos", "Conciliado", "Apenas no banco", "Apenas no financeiro", "Inválido"],
    )
    exibicao = resultado if status_filtro == "Todos" else resultado[resultado["Status"] == status_filtro]
    st.dataframe(exibicao, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)

    csv = resultado.to_csv(index=False).encode("utf-8-sig")
    arquivo_excel = BytesIO()
    with pd.ExcelWriter(arquivo_excel, engine="openpyxl") as escritor:
        resultado.to_excel(escritor, index=False, sheet_name="Conciliacao")
    download_csv, download_excel = st.columns(2)
    download_csv.download_button(
        "Baixar CSV", csv, "resultado_conciliacao.csv", "text/csv"
    )
    download_excel.download_button(
        "Baixar Excel", arquivo_excel.getvalue(), "resultado_conciliacao.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
elif resultado is not None:
    st.info("Os parâmetros foram alterados. Execute a conciliação novamente para atualizar o resultado.")
