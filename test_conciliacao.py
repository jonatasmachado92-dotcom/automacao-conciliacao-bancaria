import unittest
from decimal import Decimal

import pandas as pd

from conciliacao import (
    assinatura_conteudo,
    categorizar_lancamentos,
    conciliar,
    parse_valor,
    preparar_lancamentos,
    relatorio_pendencias,
    resumo_gerencial,
)


class ConciliacaoTests(unittest.TestCase):
    def test_parse_valor_brasileiro(self):
        self.assertEqual(parse_valor("R$ 1.234,56"), Decimal("1234.56"))

    def test_assinaturas_diferenciam_conteudos(self):
        self.assertNotEqual(
            assinatura_conteudo(b"arquivo antigo"),
            assinatura_conteudo(b"arquivo novo"),
        )

    def test_datas_iso_e_brasileira(self):
        source = pd.DataFrame({"data": ["2025-03-02", "02/03/2025"], "valor": [1, 2]})

        prepared = preparar_lancamentos(source, "data", "valor")

        self.assertEqual(prepared["Data"].tolist(), [
            pd.Timestamp("2025-03-02"),
            pd.Timestamp("2025-03-02"),
        ])

    def test_match_unico_por_valor_e_data_mais_proxima(self):
        banco = pd.DataFrame(
            [
                {"Linha": 2, "Data": pd.Timestamp("2026-01-10"), "Valor": Decimal("100.00"), "Descricao": "PIX", "Problema": ""},
                {"Linha": 3, "Data": pd.Timestamp("2026-01-11"), "Valor": Decimal("100.00"), "Descricao": "PIX", "Problema": ""},
            ]
        )
        financeiro = pd.DataFrame(
            [
                {"Linha": 2, "Data": pd.Timestamp("2026-01-10"), "Valor": Decimal("100.00"), "Descricao": "A", "Problema": ""},
                {"Linha": 3, "Data": pd.Timestamp("2026-01-13"), "Valor": Decimal("100.00"), "Descricao": "B", "Problema": ""},
                {"Linha": 4, "Data": pd.Timestamp("2026-01-20"), "Valor": Decimal("50.00"), "Descricao": "C", "Problema": ""},
            ]
        )

        result = conciliar(banco, financeiro, tolerancia_dias=2)

        self.assertEqual(result["Status"].value_counts().to_dict(), {
            "Conciliado": 2,
            "Apenas no financeiro": 1,
        })
        self.assertEqual(result.loc[result["Status"] == "Conciliado", "Linha financeiro"].tolist(), [2, 3])

    def test_tolerancia_de_valor_zero_nao_aceita_diferenca(self):
        banco = pd.DataFrame([
            {"Linha": 2, "Data": pd.Timestamp("2026-01-10"), "Valor": Decimal("100.00"), "Descricao": "", "Problema": ""},
        ])
        financeiro = pd.DataFrame([
            {"Linha": 2, "Data": pd.Timestamp("2026-01-10"), "Valor": Decimal("104.00"), "Descricao": "", "Problema": ""},
        ])

        result = conciliar(
            banco,
            financeiro,
            tolerancia_dias=0,
            tolerancia_valor=Decimal("0.00"),
        )

        self.assertEqual(result["Status"].tolist(), ["Apenas no banco", "Apenas no financeiro"])

    def test_diferenca_maior_que_cinco_e_sinalizada(self):
        banco = pd.DataFrame([
            {"Linha": 2, "Data": pd.Timestamp("2026-01-10"), "Valor": Decimal("100.00"), "Descricao": "", "Problema": ""},
        ])
        financeiro = pd.DataFrame([
            {"Linha": 2, "Data": pd.Timestamp("2026-01-10"), "Valor": Decimal("106.00"), "Descricao": "", "Problema": ""},
        ])

        result = conciliar(
            banco,
            financeiro,
            tolerancia_dias=0,
            tolerancia_valor=Decimal("10.00"),
        )

        self.assertEqual(result["Status"].tolist(), ["Conciliado com diferença"])

    def test_pareamento_maximiza_lancamentos_conciliados(self):
        banco = pd.DataFrame([
            {"Linha": 2, "Data": pd.Timestamp("2026-01-10"), "Valor": Decimal("100.00"), "Descricao": "", "Problema": ""},
            {"Linha": 3, "Data": pd.Timestamp("2026-01-10"), "Valor": Decimal("104.00"), "Descricao": "", "Problema": ""},
        ])
        financeiro = pd.DataFrame([
            {"Linha": 2, "Data": pd.Timestamp("2026-01-10"), "Valor": Decimal("101.00"), "Descricao": "", "Problema": ""},
            {"Linha": 3, "Data": pd.Timestamp("2026-01-10"), "Valor": Decimal("96.00"), "Descricao": "", "Problema": ""},
        ])

        result = conciliar(
            banco,
            financeiro,
            tolerancia_dias=0,
            tolerancia_valor=Decimal("5.00"),
        )

        self.assertEqual(result["Status"].tolist(), [
            "Conciliado com diferença",
            "Conciliado com diferença",
        ])

    def test_lancamento_invalido_e_preservado(self):
        source = pd.DataFrame({"data": ["data ruim"], "valor": ["n/a"]})
        prepared = preparar_lancamentos(source, "data", "valor")
        result = conciliar(prepared, prepared)

        self.assertEqual(len(result), 2)
        self.assertTrue((result["Status"] == "Inválido").all())

    def test_categorizacao_automatica(self):
        source = pd.DataFrame({
            "descricao": ["TARIFA DE CUSTODIA", "ENERGIA ELETRICA", "PIX RECEBIDO"]
        })

        categories = categorizar_lancamentos(source, "descricao")

        self.assertEqual(categories.tolist(), [
            "Despesa Bancária",
            "Despesa Operacional",
            "Sem categoria",
        ])

    def test_conciliado_com_diferenca_e_relatorio_pendencias(self):
        banco = pd.DataFrame([
            {"Linha": 2, "Data": pd.Timestamp("2026-01-10"), "Valor": Decimal("100.00"), "Descricao": "TARIFA DE CUSTODIA", "Problema": "", "Categoria": "Despesa Bancária"},
            {"Linha": 3, "Data": pd.Timestamp("2026-01-12"), "Valor": Decimal("30.00"), "Descricao": "PAGAMENTO", "Problema": "", "Categoria": "Sem categoria"},
        ])
        financeiro = pd.DataFrame([
            {"Linha": 5, "Data": pd.Timestamp("2026-01-10"), "Valor": Decimal("102.50"), "Descricao": "TARIFA", "Problema": "", "Categoria": "Despesa Bancária"},
            {"Linha": 6, "Data": pd.Timestamp("2026-01-13"), "Valor": Decimal("80.00"), "Descricao": "PAGAMENTO", "Problema": "", "Categoria": "Sem categoria"},
        ])

        result = conciliar(banco, financeiro, tolerancia_dias=2, tolerancia_valor=Decimal("5.00"))
        fechadas, pendencias = relatorio_pendencias(result)
        summary = resumo_gerencial(result)

        self.assertIn("Conciliado com diferença", result["Status"].tolist())
        self.assertEqual(fechadas["Status"].isin(["Conciliado", "Conciliado com diferença"]).sum(), 1)
        self.assertFalse(pendencias.empty)
        self.assertTrue("Apenas no banco" in pendencias["Status"].tolist() or "Apenas no financeiro" in pendencias["Status"].tolist())
        self.assertIn("Status", summary.columns)


if __name__ == "__main__":
    unittest.main()