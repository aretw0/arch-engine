"""Linter de restrições: executa um `Perfil` (quality:v1) sobre a compilação.

Cada `check.type` é uma função pura `(Compilacao, Regra) -> [Finding]`.
O validador nunca interrompe o build: ele descreve. Quem decide bloquear é
quem lê `counts["fail"]` (a CLI e o CI).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from typing import Any

from arch_engine.compiler import Compilacao
from arch_engine.contracts import quality_report, verify_provenance
from arch_engine.loader import SpecError
from arch_engine.model import Perfil, Regra

CHECKER_ID = "arch-engine.validator"
DOMAIN = "physical-design"

FAIL, WARN, NOTICE = "fail", "warn", "notice"


@dataclass(frozen=True)
class Finding:
    severity: str
    rule_id: str
    message: str
    locus: dict[str, Any] = field(default_factory=dict)

    def como_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return {
            "severity": d["severity"],
            "ruleId": d["rule_id"],
            "message": d["message"],
            "locus": d["locus"],
        }


Check = Callable[[Compilacao, Regra], list[Finding]]


def _material_field_forbidden(c: Compilacao, r: Regra) -> list[Finding]:
    campo, valores = r.check["campo"], set(r.check["valores"])
    return [
        Finding(
            r.severity,
            r.id,
            f"{m.nome}: {campo} = {valor!r} é proibido",
            {"material": m.id, "campo": campo, "valor": valor},
        )
        for m in c.materiais_usados
        if (valor := m.campo(campo)) in valores
    ]


def _material_field_expected(c: Compilacao, r: Regra) -> list[Finding]:
    campo, esperado = r.check["campo"], r.check["valor"]
    return [
        Finding(
            r.severity,
            r.id,
            f"{m.nome}: {campo} = {valor!r}, esperado {esperado!r}",
            {"material": m.id, "campo": campo, "valor": valor},
        )
        for m in c.materiais_usados
        if (valor := m.campo(campo)) != esperado
    ]


def _budget_limit(c: Compilacao, r: Regra) -> list[Finding]:
    limite = c.projeto.orcamento_limite
    if limite is None or c.custo_total <= limite:
        return []
    return [
        Finding(
            r.severity,
            r.id,
            f"custo total {c.custo_total:,.2f} estoura o limite {limite:,.2f} ({c.projeto.moeda})",
            {
                "custo_total": round(c.custo_total, 2),
                "orcamento_limite": limite,
                "excesso": round(c.custo_total - limite, 2),
            },
        )
    ]


def _provenance_required(c: Compilacao, r: Regra) -> list[Finding]:
    achados = []
    for m in c.materiais_usados:
        prov = (
            None
            if m.provenance is None
            else {"channel": m.provenance.channel, "originLink": m.provenance.origin_link}
        )
        resultado = verify_provenance(prov)
        if not resultado.valid:
            achados.append(
                Finding(
                    r.severity,
                    r.id,
                    f"{m.nome}: sem provenance ({', '.join(resultado.failures)})",
                    {"material": m.id},
                )
            )
    return achados


def _lot_fit(c: Compilacao, r: Regra) -> list[Finding]:
    if c.lote is None:
        return []
    d, lote = c.projeto.dimensoes, c.lote
    largura_necessaria = d.largura + 2 * lote.recuos.lateral
    profundidade_necessaria = d.profundidade + lote.recuos.frente + lote.recuos.fundo
    achados = []
    if largura_necessaria > lote.largura:
        achados.append(
            Finding(
                r.severity,
                r.id,
                f"largura {largura_necessaria:.2f} m > lote {lote.largura:.2f} m",
                {"lote": lote.id, "eixo": "largura"},
            )
        )
    if profundidade_necessaria > lote.profundidade:
        achados.append(
            Finding(
                r.severity,
                r.id,
                f"profundidade {profundidade_necessaria:.2f} m > lote {lote.profundidade:.2f} m",
                {"lote": lote.id, "eixo": "profundidade"},
            )
        )
    return achados


CHECKS: dict[str, Check] = {
    "material-field-forbidden": _material_field_forbidden,
    "material-field-expected": _material_field_expected,
    "budget-limit": _budget_limit,
    "provenance-required": _provenance_required,
    "lot-fit": _lot_fit,
}


def validar(compilacao: Compilacao, perfil: Perfil) -> dict[str, Any]:
    """Devolve um `QualityReport` (dict pronto para JSON)."""
    findings: list[Finding] = []
    for regra in perfil.rules:
        tipo = regra.check["type"]
        if tipo not in CHECKS:
            raise SpecError(
                perfil.name,
                f"rules[{regra.id}].check.type",
                f"check desconhecido {tipo!r}; conhecidos: {sorted(CHECKS)}",
            )
        findings.extend(CHECKS[tipo](compilacao, regra))
    return quality_report(
        checker_id=CHECKER_ID,
        domain=DOMAIN,
        profile_name=perfil.name,
        findings=[f.como_dict() for f in findings],
        metrics={
            "custo_total": round(compilacao.custo_total, 2),
            "orcamento_limite": compilacao.projeto.orcamento_limite,
            "carbono_total_kg": round(compilacao.carbono_total_kg, 2),
            "materiais": len(compilacao.materiais_usados),
        },
    )


def tem_falhas(relatorio: dict[str, Any]) -> bool:
    return relatorio["counts"].get(FAIL, 0) > 0
