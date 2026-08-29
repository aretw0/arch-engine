"""Parâmetros para o CAD: o YAML fala em metros, o SCAD e o SH3D em centímetros.

`gen/params.scad` é gerado (e ignorado pelo Git): a única fonte de verdade
das dimensões continua sendo `data/projeto.yaml`. Os nomes são agnósticos
(`edificacao_*`, `lote_*`) — o `main.scad` de cada exemplo mapeia para os
módulos do seu domínio.
"""

from __future__ import annotations

from arch_engine.model import Lote, Projeto

CM_POR_M = 100


def _cm(metros: float) -> int:
    return round(metros * CM_POR_M)


def parametros_cm(projeto: Projeto, lote: Lote | None) -> dict[str, float | int]:
    d = projeto.dimensoes
    params: dict[str, float | int] = {
        "edificacao_largura": _cm(d.largura),
        "edificacao_profundidade": _cm(d.profundidade),
        "edificacao_pe_direito": _cm(d.pe_direito),
        "edificacao_espessura_parede": _cm(d.espessura_parede),
        "edificacao_inclinacao_cobertura": d.inclinacao_cobertura_graus,
    }
    if lote is not None:
        params.update(
            {
                "lote_largura": _cm(lote.largura),
                "lote_profundidade": _cm(lote.profundidade),
                "lote_recuo_frente": _cm(lote.recuos.frente),
                "lote_recuo_fundo": _cm(lote.recuos.fundo),
                "lote_recuo_lateral": _cm(lote.recuos.lateral),
                "lote_orientacao_norte": lote.orientacao_norte_graus,
                "lote_declividade": lote.declividade_percentual,
            }
        )
    return params


def gerar_params_scad(projeto: Projeto, lote: Lote | None) -> str:
    linhas = [
        "// GERADO por `arch-engine scad-params` a partir de data/projeto.yaml — não edite.",
        "// Unidade: centímetros (nativa do Sweet Home 3D). Ângulos em graus, declividade em %.",
        f"// Projeto: {projeto.nome}" + (f" · Lote: {lote.nome}" if lote else ""),
        "",
    ]
    linhas += [f"{nome} = {valor};" for nome, valor in parametros_cm(projeto, lote).items()]
    return "\n".join(linhas) + "\n"
