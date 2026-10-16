"""Leitura do Indicador de Incerteza da Economia (IIE-Br, FGV IBRE).

Metodologia do IBRE (nota de janeiro de 2021):
- IIE-Br Mídia e IIE-Br Expectativa são padronizados, cada um, para média 100
  e desvio-padrão 10 na janela de referência (jan/2006 a dez/2015);
- o índice combina os dois com pesos 0,8 (Mídia) e 0,2 (Expectativa);
- a combinação é padronizada de novo para média 100 e desvio-padrão 10 na
  mesma janela.

Como a combinação é repadronizada, cada ponto dos componentes vale um pouco
mais de 0,8 ou 0,2 ponto no índice. O fator de escala k é estimado aqui a partir
dos próprios dados: IIE-Br - 100 = k × [0,8 (Mídia - 100) + 0,2 (Expectativa - 100)].
"""

from __future__ import annotations

import numpy as np
import pandas as pd

PESO_MIDIA, PESO_EXPECTATIVA = 0.8, 0.2
JANELA = ("2006-01", "2015-12")


def carregar(caminho: str = "data/iie_br.csv") -> pd.DataFrame:
    d = pd.read_csv(caminho)
    d["data"] = pd.to_datetime(d["data"], format="%Y-%m")
    return d.sort_values("data").reset_index(drop=True)


def _combinacao(d: pd.DataFrame) -> pd.Series:
    return PESO_MIDIA * (d["midia"] - 100) + PESO_EXPECTATIVA * (d["expectativa"] - 100)


def fator_escala(d: pd.DataFrame) -> float:
    """k que leva a combinação ponderada dos componentes à escala do índice.

    Pela construção, k = 10 / desvio-padrão da combinação na janela de referência.
    """
    w = d[(d["data"] >= JANELA[0]) & (d["data"] <= JANELA[1])].dropna(subset=["midia", "expectativa"])
    return float(10 / _combinacao(w).std())


def conferir(d: pd.DataFrame, k: float, tolerancia: float = 1.5) -> pd.DataFrame:
    """Meses em que o índice publicado não é reproduzido pelos componentes.

    Diferenças acima da tolerância indicam provável erro de digitação na base.
    """
    x = d.dropna(subset=["midia", "expectativa"]).copy()
    x["implicito"] = 100 + k * _combinacao(x)
    x["diferenca"] = x["iiebr"] - x["implicito"]
    return x.loc[x["diferenca"].abs() > tolerancia, ["data", "iiebr", "midia", "expectativa", "implicito", "diferenca"]]


def contribuicoes(d: pd.DataFrame, k: float) -> pd.DataFrame:
    """Variação mensal do índice decomposta entre Mídia e Expectativa (em pontos)."""
    x = d.copy()
    x["var_iiebr"] = x["iiebr"].diff()
    x["contrib_midia"] = k * PESO_MIDIA * x["midia"].diff()
    x["contrib_expectativa"] = k * PESO_EXPECTATIVA * x["expectativa"].diff()
    x["residuo"] = x["var_iiebr"] - x["contrib_midia"] - x["contrib_expectativa"]
    return x[["data", "var_iiebr", "contrib_midia", "contrib_expectativa", "residuo"]]


def classificar(valor: float) -> str:
    """Distância da média histórica, em desvios-padrão (10 pontos = 1 desvio)."""
    dp = (valor - 100) / 10
    if dp < 0:
        return "abaixo da média histórica"
    if dp < 1:
        return "acima da média, a menos de 1 desvio-padrão"
    if dp < 2:
        return "entre 1 e 2 desvios-padrão acima da média"
    return "mais de 2 desvios-padrão acima da média"


def percentil(d: pd.DataFrame, valor: float, coluna: str = "iiebr") -> float:
    """Percentual dos meses da série com valor menor ou igual ao informado."""
    return float((d[coluna].dropna() <= valor).mean() * 100)


def media_movel(d: pd.DataFrame, coluna: str = "iiebr", n: int = 3) -> pd.Series:
    return d[coluna].rolling(n).mean()
