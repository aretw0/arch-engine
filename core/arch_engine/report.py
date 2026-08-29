"""Relatório em Markdown: o artefato que um humano lê primeiro.

É derivado da compilação e do relatório de qualidade — nunca editado à mão.
"""

from __future__ import annotations

from typing import Any

from arch_engine.compiler import Compilacao

SEVERIDADE_ICONE = {"fail": "❌", "warn": "⚠️", "notice": "ℹ️"}


def _moeda(valor: float, moeda: str) -> str:
    return f"{valor:,.2f} {moeda}"


def _sim_nao(valor: Any) -> str:
    return "sim" if valor is True else "não" if valor is False else "—"


def gerar_markdown(compilacao: Compilacao, qualidade: dict[str, Any], gerado_em: str) -> str:
    p, lote, bases = compilacao.projeto, compilacao.lote, compilacao.bases
    linhas: list[str] = [
        f"# Relatório · {p.nome}",
        "",
        f"> Gerado por `arch-engine` em {gerado_em}. Fonte: `data/*.yaml`. Não edite este arquivo.",
        "",
        "## Bases geométricas",
        "",
        "| Base | Valor |",
        "|---|---:|",
    ]
    unidades = {"perimetro": "m", "volume_interno": "m³"}
    linhas += [
        f"| `{nome}` | {valor:,.2f} {unidades.get(nome, 'm²')} |" for nome, valor in bases.items()
    ]

    linhas += [
        "",
        "## Quantitativos",
        "",
        "| Elemento | Insumo | Base | Qtd. base | Consumo | Custo | CO₂e (kg) |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for i in compilacao.itens:
        linhas.append(
            f"| {i.elemento} | {i.material.nome} | `{i.base}` | {i.quantidade_base:,.2f} "
            f"| {i.consumo:,.2f} {i.unidade} | {_moeda(i.custo, p.moeda)} | {i.carbono_kg:,.1f} |"
        )
    area = bases.get("area_piso") or 1.0
    linhas += [
        "",
        "## Totais",
        "",
        f"- **Custo de insumos:** {_moeda(compilacao.custo_total, p.moeda)}"
        + (
            f" (limite: {_moeda(p.orcamento_limite, p.moeda)})"
            if p.orcamento_limite is not None
            else ""
        ),
        f"- **Carbono incorporado:** {compilacao.carbono_total_kg:,.1f} kg CO₂e "
        f"({compilacao.carbono_total_kg / area:,.1f} kg CO₂e/m² de piso)",
        f"- **Custo por m² de piso:** {_moeda(compilacao.custo_total / area, p.moeda)}",
    ]

    linhas += [
        "",
        "## Saúde e ecologia dos insumos",
        "",
        "| Insumo | COV (`vif`) | Respirabilidade | Origem local | CO₂e/unid. | Fonte |",
        "|---|---|---|---|---:|---|",
    ]
    for m in compilacao.materiais_usados:
        fonte = "—"
        if m.provenance is not None:
            fonte = (
                f"[{m.provenance.channel}]({m.provenance.origin_link})"
                if m.provenance.origin_link
                else m.provenance.channel
            )
        pegada = float(m.ecologico.get("pegada_carbono_kg_co2", 0))
        linhas.append(
            f"| {m.nome} | {m.saude.get('vif', '—')} | {m.saude.get('respirabilidade', '—')} "
            f"| {_sim_nao(m.ecologico.get('origem_local'))} | {pegada:,.2f} | {fonte} |"
        )

    if lote is not None:
        linhas += [
            "",
            "## Lote",
            "",
            f"- **{lote.nome}** (`{lote.id}`): {lote.largura:,.1f} × {lote.profundidade:,.1f} m",
            f"- Recuos: frente {lote.recuos.frente} m · fundo {lote.recuos.fundo} m "
            f"· lateral {lote.recuos.lateral} m",
            f"- Norte a {lote.orientacao_norte_graus}° "
            f"· declividade {lote.declividade_percentual}%",
        ]

    counts = qualidade["counts"]
    resumo = (
        ", ".join(f"{SEVERIDADE_ICONE.get(s, s)} {n} {s}" for s, n in sorted(counts.items()))
        or "✅ nenhum achado"
    )
    linhas += ["", f"## Validação · perfil `{qualidade['profileName']}`", "", f"{resumo}", ""]
    for f in qualidade["findings"]:
        linhas.append(
            f"- {SEVERIDADE_ICONE.get(f['severity'], '')} `{f['ruleId']}` — {f['message']}"
        )
    return "\n".join(linhas) + "\n"
