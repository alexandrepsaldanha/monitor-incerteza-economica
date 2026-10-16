"""Gera gráficos, tabelas e a nota mensal do monitor de incerteza.

Uso, a partir da raiz do repositório:
    python src/main.py

A cada divulgação do IIE-Br pelo FGV IBRE (fim do mês), acrescente uma linha em
data/iie_br.csv com o índice e os dois componentes do press release.
"""

from __future__ import annotations

import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import analise  # noqa: E402
import graficos  # noqa: E402
from graficos import mes_ano  # noqa: E402

FIG, TAB = "output/figuras", "output/tabelas"


def br(x: float, d: int = 1, sinal: bool = False) -> str:
    if round(x, d) == 0:
        x = 0.0
        sinal = False
    s = f"{x:+.{d}f}" if sinal else f"{x:.{d}f}"
    return s.replace(".", ",").replace("-", "−")


def nota(d, c, k, conf, eventos) -> str:
    u, a = d.iloc[-1], d.iloc[-2]
    cu = c.iloc[-1]
    mm3 = analise.media_movel(d).iloc[-1]
    mm3_ant = analise.media_movel(d).iloc[-2]
    maior = "Mídia" if abs(cu["contrib_midia"]) >= abs(cu["contrib_expectativa"]) else "Expectativa"
    ano = d[d["data"] > u["data"] - pd.DateOffset(months=12)]
    ev = eventos[eventos["data"] >= u["data"] - pd.DateOffset(months=6)]
    linhas_ev = "\n".join(f"- {mes_ano(e.data)}: {e.evento}" for e in ev.itertuples()) or "- Nenhum evento marcado no período."
    leitura = ""
    if os.path.exists("nota/leitura.md"):
        leitura = "\n## Leitura\n\n" + open("nota/leitura.md", encoding="utf-8").read().strip() + "\n"
    aviso = ""
    if len(conf):
        aviso = ("\n> Conferência da base: em " + ", ".join(mes_ano(x) for x in conf["data"]) +
                 ", o índice publicado não é reproduzido pelos componentes registrados. Vale conferir esses meses com o press release.\n")
    return f"""# Monitor de incerteza econômica: IIE-Br de {mes_ano(u['data'])}

*Leitura mensal do Indicador de Incerteza da Economia (FGV IBRE).*

## Destaques

- **IIE-Br de {mes_ano(u['data'])}: {br(u['iiebr'])} pontos** ({br(u['iiebr'] - a['iiebr'], sinal=True)} no mês), {analise.classificar(u['iiebr'])}. Na média móvel de três meses, {br(mm3)} pontos ({br(mm3 - mm3_ant, sinal=True)}).
- **Mídia: {br(u['midia'])} pontos** ({br(u['midia'] - a['midia'], sinal=True)}), contribuição de {br(cu['contrib_midia'], sinal=True)} ponto para a variação do índice.
- **Expectativa: {br(u['expectativa'])} pontos** ({br(u['expectativa'] - a['expectativa'], sinal=True)}), contribuição de {br(cu['contrib_expectativa'], sinal=True)} ponto.
- O componente que mais moveu o índice no mês foi **{maior}**.
- Nos últimos 12 meses, o IIE-Br variou entre {br(ano['iiebr'].min())} e {br(ano['iiebr'].max())} pontos. O nível atual supera {br(analise.percentil(d, u['iiebr']), 0)}% dos meses desde 2000.
{leitura}
## Eventos recentes marcados

{linhas_ev}

![IIE-Br e componentes](../output/figuras/recente.png)

![Contribuições](../output/figuras/contribuicoes.png)

![Série histórica](../output/figuras/historico.png)
{aviso}
*Contribuições calculadas com o fator de repadronização do índice estimado na janela de referência (k = {br(k, 3)}): cada ponto da Mídia vale {br(0.8 * k, 2)} ponto no IIE-Br, e cada ponto da Expectativa, {br(0.2 * k, 2)}.*
"""


def main():
    for p in (FIG, TAB, "nota"):
        os.makedirs(p, exist_ok=True)
    d = analise.carregar()
    eventos = pd.read_csv("data/eventos.csv")
    eventos["data"] = pd.to_datetime(eventos["data"], format="%Y-%m")
    k = analise.fator_escala(d)
    c = analise.contribuicoes(d, k)
    conf = analise.conferir(d, k)

    c.to_csv(f"{TAB}/contribuicoes.csv", index=False)
    conf.to_csv(f"{TAB}/conferencia_base.csv", index=False)
    graficos.historico(d, eventos, f"{FIG}/historico.png")
    graficos.recente(d, eventos, f"{FIG}/recente.png")
    graficos.contribuicoes(c, f"{FIG}/contribuicoes.png")
    with open("nota/ultima_nota.md", "w", encoding="utf-8") as fh:
        fh.write(nota(d, c, k, conf, eventos))
    print(f"Monitor atualizado: IIE-Br de {mes_ano(d['data'].iloc[-1])}. k = {k:.3f}. "
          f"Meses a conferir: {len(conf)}")


if __name__ == "__main__":
    main()
