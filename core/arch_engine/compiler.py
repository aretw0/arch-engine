"""Motor matemático genérico: dimensões × insumos → quantitativos.

O compilador não sabe o que é "parede" ou "telhado". Ele conhece *bases
geométricas* (funções puras sobre `Dimensoes`) e *composições* (item = base ×
fator × consumo do insumo). Um novo tipo de edificação é só um novo registro
em `BASES`, não uma nova versão do motor.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass

from arch_engine.loader import SpecError
from arch_engine.model import Dimensoes, Lote, Material, Projeto

# --- bases geométricas -----------------------------------------------------------


def _area_piso(d: Dimensoes) -> float:
    return d.largura * d.profundidade


def _perimetro(d: Dimensoes) -> float:
    return 2 * (d.largura + d.profundidade)


def _area_paredes_externas(d: Dimensoes) -> float:
    return _perimetro(d) * d.pe_direito * (1 - d.aberturas_percentual)


def _area_cobertura(d: Dimensoes) -> float:
    # Área real do plano inclinado: projeção / cos(θ). θ = 0 → cobertura plana.
    return _area_piso(d) / math.cos(math.radians(d.inclinacao_cobertura_graus))


def _volume_interno(d: Dimensoes) -> float:
    e = d.espessura_parede
    return (d.largura - 2 * e) * (d.profundidade - 2 * e) * d.pe_direito


BASES: dict[str, Callable[[Dimensoes], float]] = {
    "area_piso": _area_piso,
    "perimetro": _perimetro,
    "area_paredes_externas": _area_paredes_externas,
    "area_cobertura": _area_cobertura,
    "volume_interno": _volume_interno,
}


def bases_geometricas(dimensoes: Dimensoes) -> dict[str, float]:
    return {nome: funcao(dimensoes) for nome, funcao in BASES.items()}


# --- resultado da compilação -------------------------------------------------------


@dataclass(frozen=True)
class Quantitativo:
    elemento: str
    material: Material
    base: str
    quantidade_base: float  # m² (ou m, m³) da base × fator
    consumo: float  # na unidade do insumo
    unidade: str
    custo: float
    carbono_kg: float


@dataclass(frozen=True)
class Compilacao:
    projeto: Projeto
    lote: Lote | None
    bases: dict[str, float]
    itens: tuple[Quantitativo, ...]

    @property
    def custo_total(self) -> float:
        return sum(i.custo for i in self.itens)

    @property
    def carbono_total_kg(self) -> float:
        return sum(i.carbono_kg for i in self.itens)

    @property
    def materiais_usados(self) -> tuple[Material, ...]:
        vistos: dict[str, Material] = {}
        for item in self.itens:
            vistos.setdefault(item.material.id, item.material)
        return tuple(vistos.values())


def compilar(projeto: Projeto, materiais: dict[str, Material], lote: Lote | None) -> Compilacao:
    bases = bases_geometricas(projeto.dimensoes)
    itens = []
    for indice, item in enumerate(projeto.composicao):
        caminho = f"composicao[{indice}]"
        if item.base not in bases:
            raise SpecError(projeto.nome, f"{caminho}.base", f"base desconhecida {item.base!r}")
        if item.material not in materiais:
            raise SpecError(
                projeto.nome, f"{caminho}.material", f"material {item.material!r} não está no DB"
            )
        material = materiais[item.material]
        quantidade = bases[item.base] * item.fator
        consumo = quantidade * material.consumo_por_m2
        carbono_unitario = float(material.ecologico.get("pegada_carbono_kg_co2", 0.0))
        itens.append(
            Quantitativo(
                elemento=item.elemento,
                material=material,
                base=item.base,
                quantidade_base=quantidade,
                consumo=consumo,
                unidade=material.unidade,
                custo=consumo * material.preco_unitario,
                carbono_kg=consumo * carbono_unitario,
            )
        )
    return Compilacao(projeto=projeto, lote=lote, bases=bases, itens=tuple(itens))
