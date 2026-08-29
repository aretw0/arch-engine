"""Modelo de dados puro (sem I/O).

As chaves seguem a linguagem ubíqua do domínio em pt-BR, igual aos YAML que
as originam. Tudo é imutável: a compilação é uma função dos dados.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Provenance:
    """Espelho mínimo de `provenance:v1` (refarm): `channel` é o único campo obrigatório."""

    channel: str
    origin_link: str | None = None
    collected_at: str | None = None
    license: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Material:
    id: str
    nome: str
    unidade: str
    preco_unitario: float
    consumo_por_m2: float
    saude: dict[str, Any] = field(default_factory=dict)
    ecologico: dict[str, Any] = field(default_factory=dict)
    provenance: Provenance | None = None

    def campo(self, caminho: str) -> Any:
        """Lê um campo aninhado por caminho pontuado, ex.: ``"saude.vif"``."""
        atual: Any = {"saude": self.saude, "ecologico": self.ecologico, "unidade": self.unidade}
        for parte in caminho.split("."):
            if not isinstance(atual, dict) or parte not in atual:
                return None
            atual = atual[parte]
        return atual


@dataclass(frozen=True)
class Dimensoes:
    """Dimensões em metros. Derivações geométricas ficam no compilador."""

    largura: float
    profundidade: float
    pe_direito: float
    espessura_parede: float = 0.20
    aberturas_percentual: float = 0.0
    inclinacao_cobertura_graus: float = 0.0


@dataclass(frozen=True)
class ItemComposicao:
    elemento: str
    material: str
    base: str
    fator: float = 1.0


@dataclass(frozen=True)
class Projeto:
    nome: str
    dimensoes: Dimensoes
    composicao: tuple[ItemComposicao, ...]
    moeda: str = "BRL"
    orcamento_limite: float | None = None


@dataclass(frozen=True)
class Recuos:
    frente: float = 0.0
    fundo: float = 0.0
    lateral: float = 0.0


@dataclass(frozen=True)
class Lote:
    id: str
    nome: str
    largura: float
    profundidade: float
    recuos: Recuos = field(default_factory=Recuos)
    orientacao_norte_graus: float = 0.0
    declividade_percentual: float = 0.0
    solo: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Regra:
    """Uma `QualityRule` de `quality:v1`: o `check.type` é resolvido pelo validador."""

    id: str
    severity: str
    description: str
    check: dict[str, Any]
    category: str | None = None


@dataclass(frozen=True)
class Perfil:
    """Um `QualityProfile` de `quality:v1`."""

    name: str
    rules: tuple[Regra, ...]
