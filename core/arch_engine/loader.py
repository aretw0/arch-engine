"""YAML → modelo, com erros que apontam arquivo e caminho da chave.

O loader é a única fronteira entre texto e tipos. Ele valida esquema por
esquema (`schema:` na raiz) e converte para as dataclasses de `model`. Nada
aqui sabe o que é uma casa: só o formato dos dados.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from arch_engine.model import (
    Dimensoes,
    ItemComposicao,
    Lote,
    Material,
    Perfil,
    Projeto,
    Provenance,
    Recuos,
    Regra,
)

SCHEMA_PROJETO = "arch-engine.projeto.v1"
SCHEMA_MATERIAIS = "arch-engine.materiais.v1"
SCHEMA_LOTE = "arch-engine.lote.v1"


class SpecError(ValueError):
    """Erro de especificação legível: ``<origem>: <caminho>: <motivo>``."""

    def __init__(self, origem: str, caminho: str, motivo: str) -> None:
        self.origem, self.caminho, self.motivo = origem, caminho, motivo
        super().__init__(f"{origem}: {caminho}: {motivo}")


class _Leitor:
    """Acesso a dicts com caminho acumulado para mensagens de erro precisas."""

    def __init__(self, dados: Any, origem: str, caminho: str = "") -> None:
        if not isinstance(dados, dict):
            raise SpecError(origem, caminho or "$", "esperava um mapeamento YAML")
        self.dados, self.origem, self.caminho = dados, origem, caminho

    def _junta(self, chave: str) -> str:
        return f"{self.caminho}.{chave}" if self.caminho else chave

    def obrigatorio(self, chave: str) -> Any:
        if chave not in self.dados or self.dados[chave] is None:
            raise SpecError(self.origem, self._junta(chave), "campo obrigatório ausente")
        return self.dados[chave]

    def opcional(self, chave: str, padrao: Any = None) -> Any:
        return self.dados.get(chave, padrao)

    def numero(self, chave: str, padrao: float | None = None) -> float:
        valor = self.opcional(chave, padrao) if padrao is not None else self.obrigatorio(chave)
        if isinstance(valor, bool) or not isinstance(valor, int | float):
            raise SpecError(self.origem, self._junta(chave), f"esperava número, veio {valor!r}")
        return float(valor)

    def texto(self, chave: str, padrao: str | None = None) -> str:
        valor = self.opcional(chave, padrao) if padrao is not None else self.obrigatorio(chave)
        if not isinstance(valor, str) or not valor.strip():
            raise SpecError(self.origem, self._junta(chave), "esperava texto não vazio")
        return valor

    def dicionario(self, chave: str, padrao: dict | None = None) -> dict[str, Any]:
        valor = self.opcional(chave, padrao if padrao is not None else {})
        if not isinstance(valor, dict):
            raise SpecError(self.origem, self._junta(chave), "esperava um mapeamento")
        return valor

    def lista(self, chave: str) -> list[Any]:
        valor = self.obrigatorio(chave)
        if not isinstance(valor, list):
            raise SpecError(self.origem, self._junta(chave), "esperava uma lista")
        return valor

    def sub(self, chave: str, dados: Any | None = None) -> _Leitor:
        return _Leitor(
            dados if dados is not None else self.obrigatorio(chave), self.origem, self._junta(chave)
        )

    def exige_schema(self, esperado: str) -> None:
        schema = self.opcional("schema")
        if schema != esperado:
            raise SpecError(
                self.origem, self._junta("schema"), f"esperava {esperado!r}, veio {schema!r}"
            )


# --- leitura de arquivos ------------------------------------------------------


def ler_yaml(caminho: Path) -> Any:
    with caminho.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def carregar_projeto_arquivo(caminho: Path) -> Projeto:
    return carregar_projeto(ler_yaml(caminho), origem=str(caminho))


def carregar_materiais_arquivo(caminho: Path) -> dict[str, Material]:
    return carregar_materiais(ler_yaml(caminho), origem=str(caminho))


def carregar_lote_arquivo(caminho: Path) -> Lote:
    return carregar_lote(ler_yaml(caminho), origem=str(caminho))


def carregar_perfil_arquivo(caminho: Path) -> Perfil:
    return carregar_perfil(ler_yaml(caminho), origem=str(caminho))


# --- conversores puros (dict → modelo) -----------------------------------------


def carregar_projeto(dados: Any, origem: str) -> Projeto:
    raiz = _Leitor(dados, origem)
    raiz.exige_schema(SCHEMA_PROJETO)
    dim = raiz.sub("dimensoes")
    dimensoes = Dimensoes(
        largura=dim.numero("largura"),
        profundidade=dim.numero("profundidade"),
        pe_direito=dim.numero("pe_direito"),
        espessura_parede=dim.numero("espessura_parede", 0.20),
        aberturas_percentual=dim.numero("aberturas_percentual", 0.0),
        inclinacao_cobertura_graus=dim.numero("inclinacao_cobertura_graus", 0.0),
    )
    composicao = []
    for indice, bruto in enumerate(raiz.lista("composicao")):
        item = raiz.sub(f"composicao[{indice}]", bruto)
        composicao.append(
            ItemComposicao(
                elemento=item.texto("elemento"),
                material=item.texto("material"),
                base=item.texto("base"),
                fator=item.numero("fator", 1.0),
            )
        )
    limite = raiz.opcional("orcamento_limite")
    return Projeto(
        nome=raiz.texto("nome"),
        dimensoes=dimensoes,
        composicao=tuple(composicao),
        moeda=raiz.texto("moeda", "BRL"),
        orcamento_limite=raiz.numero("orcamento_limite") if limite is not None else None,
    )


def _provenance(leitor: _Leitor) -> Provenance | None:
    bruto = leitor.opcional("provenance")
    if bruto is None:
        return None
    prov = leitor.sub("provenance", bruto)
    conhecidos = {"channel", "originLink", "collectedAt", "license"}
    return Provenance(
        channel=prov.texto("channel"),
        origin_link=prov.opcional("originLink"),
        collected_at=str(prov.opcional("collectedAt")) if prov.opcional("collectedAt") else None,
        license=prov.opcional("license"),
        extra={k: v for k, v in prov.dados.items() if k not in conhecidos},
    )


def carregar_materiais(dados: Any, origem: str) -> dict[str, Material]:
    raiz = _Leitor(dados, origem)
    raiz.exige_schema(SCHEMA_MATERIAIS)
    materiais: dict[str, Material] = {}
    for id_material, bruto in raiz.dicionario("materiais").items():
        m = raiz.sub(f"materiais.{id_material}", bruto)
        materiais[id_material] = Material(
            id=id_material,
            nome=m.texto("nome"),
            unidade=m.texto("unidade"),
            preco_unitario=m.numero("preco_unitario"),
            consumo_por_m2=m.numero("consumo_por_m2"),
            saude=m.dicionario("saude"),
            ecologico=m.dicionario("ecologico"),
            provenance=_provenance(m),
        )
    return materiais


def carregar_lote(dados: Any, origem: str) -> Lote:
    raiz = _Leitor(dados, origem)
    raiz.exige_schema(SCHEMA_LOTE)
    recuos = raiz.sub("recuos", raiz.dicionario("recuos"))
    return Lote(
        id=raiz.texto("id"),
        nome=raiz.texto("nome"),
        largura=raiz.numero("largura"),
        profundidade=raiz.numero("profundidade"),
        recuos=Recuos(
            frente=recuos.numero("frente", 0.0),
            fundo=recuos.numero("fundo", 0.0),
            lateral=recuos.numero("lateral", 0.0),
        ),
        orientacao_norte_graus=raiz.numero("orientacao_norte_graus", 0.0),
        declividade_percentual=raiz.numero("declividade_percentual", 0.0),
        solo=raiz.dicionario("solo"),
    )


def carregar_perfil(dados: Any, origem: str) -> Perfil:
    """Lê um `QualityProfile` (`quality:v1`): nome + regras com `check.type`."""
    raiz = _Leitor(dados, origem)
    regras = []
    for indice, bruto in enumerate(raiz.lista("rules")):
        r = raiz.sub(f"rules[{indice}]", bruto)
        check = r.dicionario("check")
        if "type" not in check:
            raise SpecError(origem, f"rules[{indice}].check.type", "campo obrigatório ausente")
        regras.append(
            Regra(
                id=r.texto("id"),
                severity=r.texto("severity"),
                description=r.texto("description"),
                check=check,
                category=r.opcional("category"),
            )
        )
    return Perfil(name=raiz.texto("name"), rules=tuple(regras))
