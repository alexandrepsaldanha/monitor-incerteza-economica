"""Gráficos do monitor de incerteza."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

AZUL, LARANJA, VERDE, AMARELO, ROSA = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"
CINZA, TINTA, TINTA2 = "#8a8a8a", "#1f1f1f", "#5c5c5c"
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def mes_ano(d) -> str:
    return f"{MESES[d.month - 1]}/{d.strftime('%y')}"


def _fmt_mes(x, _):
    return mes_ano(mdates.num2date(x))


def _estilo(ax, titulo: str, subtitulo: str | None = None):
    ax.set_title(titulo, loc="left", fontsize=13, fontweight="bold", color=TINTA, pad=22 if subtitulo else 10)
    if subtitulo:
        ax.text(0, 1.02, subtitulo, transform=ax.transAxes, fontsize=9.5, color=TINTA2)
    ax.grid(axis="y", color="#e6e6e6", linewidth=0.8)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(colors=TINTA2, labelsize=9)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.1f}".replace(".", ","))



FONTE_IIE = "Fonte: FGV IBRE (IIE-Br). Elaboração própria. Média 100 e desvio-padrão 10 em 2006–2015."
CORES_EVENTO = {"eleicao": TINTA2, "choque": TINTA2, "politica": TINTA2}  # eventos em cinza, sem competir com as séries


def _faixa(ax):
    ax.axhspan(90, 110, color="#efefef", zorder=0, label="Média ± 1 desvio-padrão")
    ax.axhline(100, color=CINZA, linewidth=1, linestyle="--", zorder=1)


def _rodape_iie(fig):
    fig.text(0.01, 0.01, FONTE_IIE, fontsize=8, color=TINTA2)


def historico(d: pd.DataFrame, eventos: pd.DataFrame, caminho: str):
    """Série completa do IIE-Br com os eventos de referência."""
    fig, ax = plt.subplots(figsize=(10, 4.8))
    _faixa(ax)
    ax.plot(d["data"], d["iiebr"], color=AZUL, linewidth=1.4, label="IIE-Br")
    topo = d["iiebr"].max() * 1.04
    for e in eventos.itertuples():
        if e.data < d["data"].min() or e.tipo == "politica":
            continue
        ax.axvline(e.data, color=CORES_EVENTO.get(e.tipo, TINTA2), linewidth=0.8, linestyle=":", zorder=1)
        rot = "Eleição " + e.data.strftime("%Y") if e.tipo == "eleicao" else e.evento
        ax.text(e.data, topo, rot, rotation=90, fontsize=7.5, color=CORES_EVENTO.get(e.tipo, TINTA2),
                ha="right", va="top")
    u = d.iloc[-1]
    ax.annotate(f"{mes_ano(u['data'])}: {u['iiebr']:.1f}".replace(".", ","), (u["data"], u["iiebr"]),
                xytext=(6, 0), textcoords="offset points", fontsize=9, fontweight="bold", color=AZUL, va="center")
    _estilo(ax, "Indicador de Incerteza da Economia (IIE-Br)", "pontos; 10 pontos = 1 desvio-padrão da média histórica")
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}")
    ax.set_ylim(top=topo * 1.01)
    ax.set_xlim(d["data"].min() - pd.DateOffset(months=3), d["data"].max() + pd.DateOffset(months=10))
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.legend(frameon=False, fontsize=8.5, loc="upper left", bbox_to_anchor=(0, -0.08), ncol=2)
    _rodape_iie(fig)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(caminho, dpi=200)
    plt.close(fig)


def recente(d: pd.DataFrame, eventos: pd.DataFrame, caminho: str, meses: int = 24):
    """Últimos meses: índice e componentes, com os eventos do período."""
    x = d.tail(meses)
    fig, ax = plt.subplots(figsize=(10, 4.8))
    _faixa(ax)
    ax.plot(x["data"], x["midia"], color=LARANJA, linewidth=1.4, label="Componente Mídia (peso 0,8)")
    ax.plot(x["data"], x["expectativa"], color=VERDE, linewidth=1.4, label="Componente Expectativa (peso 0,2)")
    ax.plot(x["data"], x["iiebr"], color=AZUL, linewidth=2.4, label="IIE-Br")
    fim = max(x["data"].max(), eventos["data"].max()) + pd.DateOffset(months=1)
    ev = eventos[(eventos["data"] >= x["data"].min()) & (eventos["data"] <= fim)]
    topo = max(x[["iiebr", "midia", "expectativa"]].max().max(), 110) + 2
    meio = x["data"].min() + (fim - x["data"].min()) / 2
    for i, e in enumerate(ev.itertuples()):
        ax.axvline(e.data, color=CORES_EVENTO.get(e.tipo, TINTA2), linewidth=1, linestyle=":", zorder=1)
        direita = e.data > meio
        ax.text(e.data + pd.DateOffset(days=-6 if direita else 6), topo + 2.5 + 2.2 * (i % 2), e.evento,
                fontsize=8, color=TINTA2, ha="right" if direita else "left", va="bottom")
    u = x.iloc[-1]
    ax.annotate(f"{u['iiebr']:.1f}".replace(".", ","), (u["data"], u["iiebr"]), xytext=(6, 0),
                textcoords="offset points", fontsize=9, fontweight="bold", color=AZUL, va="center")
    _estilo(ax, "IIE-Br e componentes nos últimos 24 meses", "pontos; 10 pontos = 1 desvio-padrão da média histórica")
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}")
    ax.set_xlim(x["data"].min() - pd.DateOffset(days=15), fim)
    ax.set_ylim(top=topo + 7.5)
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax.xaxis.set_major_formatter(_fmt_mes)
    ax.legend(frameon=False, fontsize=8.5, loc="upper left", bbox_to_anchor=(0, -0.08), ncol=4)
    _rodape_iie(fig)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(caminho, dpi=200)
    plt.close(fig)


def contribuicoes(c: pd.DataFrame, caminho: str, meses: int = 12):
    """Variação mensal do IIE-Br decomposta entre Mídia e Expectativa."""
    x = c.tail(meses).reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(10, 4.4))
    pos = range(len(x))
    m, e = x["contrib_midia"], x["contrib_expectativa"]
    base_e = [mi if (mi >= 0) == (ei >= 0) else 0 for mi, ei in zip(m, e)]
    ax.bar(pos, m, color=LARANJA, width=0.7, edgecolor="white", label="Mídia")
    ax.bar(pos, e, bottom=base_e, color=VERDE, width=0.7, edgecolor="white", label="Expectativa")
    ax.plot(list(pos), x["var_iiebr"], "o", color=TINTA, markersize=5, label="Variação do IIE-Br")
    for p, v in zip(pos, x["var_iiebr"]):
        ax.annotate(f"{v:+.1f}".replace(".", ",").replace("-", "−"), (p, v), xytext=(0, 7 if v >= 0 else -12),
                    textcoords="offset points", ha="center", fontsize=7.5, color=TINTA)
    ax.axhline(0, color=TINTA2, linewidth=0.8)
    ax.set_xticks(list(pos), [mes_ano(dt) for dt in x["data"]], fontsize=8.5)
    _estilo(ax, "O que moveu o IIE-Br mês a mês", "pontos; contribuição de cada componente para a variação do índice")
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}".replace("-", "−"))
    ax.legend(frameon=False, fontsize=8.5, loc="upper left", bbox_to_anchor=(0, -0.1), ncol=3)
    _rodape_iie(fig)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(caminho, dpi=200)
    plt.close(fig)
