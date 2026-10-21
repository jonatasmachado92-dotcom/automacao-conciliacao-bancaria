from __future__ import annotations

import hashlib
from collections import deque
from decimal import Decimal, InvalidOperation
from typing import Any

import pandas as pd


def assinatura_conteudo(conteudo: bytes) -> str:
    return hashlib.sha256(conteudo).hexdigest()


def categorizar_lancamentos(frame: pd.DataFrame, coluna_descricao: str = "Descricao") -> pd.Series:
    if coluna_descricao not in frame.columns:
        return pd.Series("Sem categoria", index=frame.index)

    descricao = frame[coluna_descricao].fillna("").astype(str).str.upper()
    regras = {
        "Despesa Bancária": [
            "TARIFA",
            "IOF",
            "CUSTODIA",
            "JUROS",
            "MULTA",
            "TAXA",
            "BANCO",
            "ESTORNO",
        ],
        "Despesa Operacional": [
            "ENERGIA",
            "ÁGUA",
            "TELEFONE",
            "INTERNET",
            "ALUGUEL",
            "SALARIO",
            "FORNECEDOR",
            "DESPESA",
        ],
    }

    categoria = pd.Series("Sem categoria", index=frame.index, dtype="object")
    for nome, palavras in regras.items():
        padrao = "|".join(palavras)
        categoria.loc[descricao.str.contains(padrao, na=False)] = nome
    return categoria


def parse_valor(value: Any) -> Decimal | None:
    if pd.isna(value):
        return None

    if isinstance(value, (int, float, Decimal)):
        try:
            return Decimal(str(value)).quantize(Decimal("0.01"))
        except InvalidOperation:
            return None

    text = str(value).strip().replace("R$", "").replace(" ", "")
    if not text:
        return None

    if "," in text:
        text = text.replace(".", "").replace(",", ".")

    try:
        return Decimal(text).quantize(Decimal("0.01"))
    except InvalidOperation:
        return None


def preparar_lancamentos(
    frame: pd.DataFrame,
    coluna_data: str,
    coluna_valor: str,
    coluna_descricao: str | None = None,
    coluna_debito: str | None = None,
    coluna_credito: str | None = None,
) -> pd.DataFrame:
    prepared = pd.DataFrame(index=frame.index)
    prepared["Linha"] = range(2, len(frame) + 2)
    raw_dates = frame[coluna_data].astype("string").str.strip()
    iso_dates = raw_dates.str.match(r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}", na=False)
    parsed_dates = pd.Series(pd.NaT, index=frame.index, dtype="datetime64[ns]")
    parsed_dates.loc[iso_dates] = pd.to_datetime(
        raw_dates.loc[iso_dates], dayfirst=False, errors="coerce"
    )
    parsed_dates.loc[~iso_dates] = pd.to_datetime(
        raw_dates.loc[~iso_dates], dayfirst=True, errors="coerce"
    )
    prepared["Data"] = parsed_dates

    if coluna_debito and coluna_credito:
        debitos = frame[coluna_debito].map(parse_valor).fillna(Decimal("0.00"))
        creditos = frame[coluna_credito].map(parse_valor).fillna(Decimal("0.00"))
        prepared["Valor"] = [credito - debito for debito, credito in zip(debitos, creditos)]
    else:
        prepared["Valor"] = frame[coluna_valor].map(parse_valor)

    if coluna_descricao:
        prepared["Descricao"] = frame[coluna_descricao].fillna("").astype(str)
    else:
        prepared["Descricao"] = ""

    prepared["Categoria"] = categorizar_lancamentos(prepared[["Descricao"]], "Descricao")
    prepared["Problema"] = ""
    prepared.loc[prepared["Data"].isna(), "Problema"] = "Data inválida"
    missing_value = prepared["Valor"].isna()
    prepared.loc[missing_value, "Problema"] = prepared.loc[missing_value, "Problema"].map(
        lambda problem: f"{problem}; valor inválido" if problem else "Valor inválido"
    )
    return prepared.reset_index(drop=True)


def conciliar(
    banco: pd.DataFrame,
    financeiro: pd.DataFrame,
    tolerancia_dias: int = 3,
    tolerancia_valor: Decimal = Decimal("0.01"),
) -> pd.DataFrame:
    valid_book = {
        index
        for index, row in financeiro.iterrows()
        if not row["Problema"]
    }

    candidatos_por_banco: dict[Any, list[tuple[Decimal, int, Any]]] = {}
    ordered_bank = sorted(
        banco.index,
        key=lambda index: (
            banco.at[index, "Data"] is pd.NaT,
            banco.at[index, "Data"] if pd.notna(banco.at[index, "Data"]) else pd.Timestamp.max,
            index,
        ),
    )

    for bank_index in ordered_bank:
        bank_row = banco.loc[bank_index]
        if bank_row["Problema"]:
            continue

        candidates = []
        for book_index in valid_book:
            book_row = financeiro.loc[book_index]
            amount_difference = abs(bank_row["Valor"] - book_row["Valor"])
            day_difference = abs((bank_row["Data"] - book_row["Data"]).days)
            if amount_difference <= tolerancia_valor and day_difference <= tolerancia_dias:
                candidates.append((amount_difference, day_difference, book_index))
        candidatos_por_banco[bank_index] = sorted(candidates)

    matches: dict[Any, Any] = {}
    banco_por_livro: dict[Any, Any] = {}
    for banco_inicial in candidatos_por_banco:
        fila = deque([banco_inicial])
        bancos_visitados = {banco_inicial}
        livros_visitados = set()
        banco_anterior: dict[Any, Any] = {}
        livro_anterior: dict[Any, Any] = {}
        caminho_aumentante = None

        while fila and caminho_aumentante is None:
            banco_atual = fila.popleft()
            for _, _, livro_index in candidatos_por_banco[banco_atual]:
                if livro_index in livros_visitados:
                    continue
                livros_visitados.add(livro_index)
                banco_correspondente = banco_por_livro.get(livro_index)
                if banco_correspondente is None:
                    caminho_aumentante = (banco_atual, livro_index)
                    break
                if banco_correspondente not in bancos_visitados:
                    bancos_visitados.add(banco_correspondente)
                    banco_anterior[banco_correspondente] = banco_atual
                    livro_anterior[banco_correspondente] = livro_index
                    fila.append(banco_correspondente)

        if caminho_aumentante is not None:
            banco_atual, livro_livre = caminho_aumentante
            while True:
                matches[banco_atual] = livro_livre
                banco_por_livro[livro_livre] = banco_atual
                if banco_atual == banco_inicial:
                    break
                livro_livre = livro_anterior[banco_atual]
                banco_atual = banco_anterior[banco_atual]

    results = []
    matched_book = set(matches.values())
    for bank_index, bank_row in banco.iterrows():
        book_index = matches.get(bank_index)
        book_row = financeiro.loc[book_index] if book_index is not None else None
        if bank_row["Problema"]:
            status = "Inválido"
        elif book_row is not None:
            amount_difference = abs(bank_row["Valor"] - book_row["Valor"])
            if amount_difference > Decimal("0.00"):
                status = "Conciliado com diferença"
            else:
                status = "Conciliado"
        else:
            status = "Apenas no banco"
        results.append(_resultado(bank_row, book_row, status, "Banco"))

    for book_index, book_row in financeiro.iterrows():
        if book_index in matched_book:
            continue
        status = "Inválido" if book_row["Problema"] else "Apenas no financeiro"
        results.append(_resultado(None, book_row, status, "Financeiro"))

    return pd.DataFrame(results)


def _resultado(
    bank_row: pd.Series | None,
    book_row: pd.Series | None,
    status: str,
    origem: str,
) -> dict[str, Any]:
    bank_amount = bank_row["Valor"] if bank_row is not None else None
    book_amount = book_row["Valor"] if book_row is not None else None
    bank_date = bank_row["Data"] if bank_row is not None else pd.NaT
    book_date = book_row["Data"] if book_row is not None else pd.NaT
    amount_difference = (
        abs(bank_amount - book_amount)
        if bank_amount is not None and book_amount is not None
        else None
    )
    day_difference = (
        abs((bank_date - book_date).days)
        if pd.notna(bank_date) and pd.notna(book_date)
        else None
    )

    return {
        "Status": status,
        "Linha banco": bank_row["Linha"] if bank_row is not None else None,
        "Data banco": bank_date,
        "Descrição banco": bank_row["Descricao"] if bank_row is not None else "",
        "Valor banco": bank_amount,
        "Linha financeiro": book_row["Linha"] if book_row is not None else None,
        "Data financeiro": book_date,
        "Descrição financeiro": book_row["Descricao"] if book_row is not None else "",
        "Valor financeiro": book_amount,
        "Diferença valor": amount_difference,
        "Diferença dias": day_difference,
        "Categoria banco": bank_row.get("Categoria", "") if bank_row is not None else "",
        "Categoria financeiro": book_row.get("Categoria", "") if book_row is not None else "",
        "Juros/Multas": (
            amount_difference
            if status == "Conciliado com diferença" and amount_difference is not None
            else Decimal("0.00")
        ),
        "Problema": (
            bank_row["Problema"] if origem == "Banco" else book_row["Problema"]
        ),
    }


def relatorio_pendencias(resultado: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    if resultado.empty:
        return resultado.copy(), resultado.copy()

    fechadas = resultado[resultado["Status"].isin(["Conciliado", "Conciliado com diferença"])].copy()
    pendencias = resultado[~resultado["Status"].isin(["Conciliado", "Conciliado com diferença"])].copy()
    return fechadas, pendencias


def resumo_gerencial(resultado: pd.DataFrame) -> pd.DataFrame:
    if resultado.empty:
        return pd.DataFrame(columns=["Status", "Quantidade", "Percentual"])

    tabela = (
        resultado.assign(Quantidade=1)
        .pivot_table(index="Status", values="Quantidade", aggfunc="sum")
        .reset_index()
    )
    tabela["Percentual"] = (tabela["Quantidade"] / len(resultado) * 100).round(2)
    return tabela[["Status", "Quantidade", "Percentual"]]