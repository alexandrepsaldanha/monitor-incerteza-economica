"""Testes com uma série sintética construída pela própria metodologia do IBRE."""

import os
import shutil
import sys

import numpy as np
import pandas as pd

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "src"))
import analise  # noqa: E402
import main  # noqa: E402


def serie_sintetica(seed=0):
    rng = np.random.default_rng(seed)
    datas = pd.date_range("2002-01-01", "2026-09-01", freq="MS")
    m = rng.normal(0, 1, len(datas)).cumsum() * 0.3 + rng.normal(0, 1, len(datas))
    e = 0.4 * m + rng.normal(0, 1, len(datas))
    d = pd.DataFrame({"data": datas, "m": m, "e": e})
    w = d[(d["data"] >= "2006-01-01") & (d["data"] <= "2015-12-01")]
    d["midia"] = 100 + 10 * (d["m"] - w["m"].mean()) / w["m"].std()
    d["expectativa"] = 100 + 10 * (d["e"] - w["e"].mean()) / w["e"].std()
    z = 0.8 * d["midia"] + 0.2 * d["expectativa"]
    wz = z[(d["data"] >= "2006-01-01") & (d["data"] <= "2015-12-01")]
    d["iiebr"] = 100 + 10 * (z - wz.mean()) / wz.std()
    k = 10 / wz.std()
    return d[["data", "iiebr", "midia", "expectativa"]].round(1), k


def test_fator_escala_recupera_a_repadronizacao():
    d, k = serie_sintetica()
    assert abs(analise.fator_escala(d) - k) < 0.02


def test_contribuicoes_somam_a_variacao():
    d, _ = serie_sintetica()
    c = analise.contribuicoes(d, analise.fator_escala(d))
    assert c["residuo"].dropna().abs().max() < 0.3          # só arredondamento


def test_conferencia_acha_erro_de_digitacao():
    d, _ = serie_sintetica()
    assert analise.conferir(d, analise.fator_escala(d)).empty
    d.loc[100, "midia"] += 15
    achados = analise.conferir(d, analise.fator_escala(d))
    assert list(achados.index) == [100]


def test_monitor_completo(tmp_path, monkeypatch):
    d, _ = serie_sintetica()
    (tmp_path / "data").mkdir()
    d.assign(data=d["data"].dt.strftime("%Y-%m")).to_csv(tmp_path / "data/iie_br.csv", index=False)
    shutil.copy(os.path.join(RAIZ, "data/eventos.csv"), tmp_path / "data/eventos.csv")
    monkeypatch.chdir(tmp_path)
    main.main()
    for f in ["output/figuras/historico.png", "output/figuras/recente.png",
              "output/figuras/contribuicoes.png", "nota/ultima_nota.md"]:
        assert os.path.exists(f), f
    nota = open("nota/ultima_nota.md", encoding="utf-8").read()
    assert "IIE-Br de set/26" in nota and "nan" not in nota.lower()
