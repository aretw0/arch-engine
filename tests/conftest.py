"""Fixtures em memória: os testes do core não dependem da demo."""

from __future__ import annotations

import pytest

from arch_engine.loader import carregar_lote, carregar_materiais, carregar_perfil, carregar_projeto

PROJETO = {
    "schema": "arch-engine.projeto.v1",
    "nome": "Casa de teste",
    "moeda": "BRL",
    "orcamento_limite": 20000.0,
    "dimensoes": {
        "largura": 9.0,
        "profundidade": 12.0,
        "pe_direito": 3.0,
        "espessura_parede": 0.30,
        "aberturas_percentual": 0.15,
        "inclinacao_cobertura_graus": 20,
    },
    "composicao": [
        {"elemento": "paredes externas", "material": "taipa", "base": "area_paredes_externas"},
        {
            "elemento": "pintura interna",
            "material": "tinta_mineral",
            "base": "area_paredes_externas",
        },
    ],
}

MATERIAIS = {
    "schema": "arch-engine.materiais.v1",
    "materiais": {
        "taipa": {
            "nome": "Taipa de pilão",
            "unidade": "m3",
            "preco_unitario": 350.0,
            "consumo_por_m2": 0.30,
            "saude": {"vif": "Isento", "respirabilidade": "Alta"},
            "ecologico": {"pegada_carbono_kg_co2": 45.6, "origem_local": True},
            "provenance": {"channel": "literature", "originLink": "https://example.org/ice"},
        },
        "tinta_mineral": {
            "nome": "Tinta mineral de silicato",
            "unidade": "L",
            "preco_unitario": 40.0,
            "consumo_por_m2": 0.25,
            "saude": {"vif": "Baixo", "respirabilidade": "Alta"},
            "ecologico": {"pegada_carbono_kg_co2": 3.2, "origem_local": False},
        },
        "esmalte": {
            "nome": "Esmalte sintético",
            "unidade": "L",
            "preco_unitario": 60.0,
            "consumo_por_m2": 0.20,
            "saude": {"vif": "Alto", "respirabilidade": "Baixa"},
            "ecologico": {"pegada_carbono_kg_co2": 4.5, "origem_local": False},
        },
    },
}

LOTE = {
    "schema": "arch-engine.lote.v1",
    "id": "lote_teste",
    "nome": "Lote de teste",
    "largura": 15.0,
    "profundidade": 30.0,
    "recuos": {"frente": 5.0, "fundo": 3.0, "lateral": 1.5},
    "orientacao_norte_graus": 0,
    "declividade_percentual": 2,
    "solo": {"ensaios": ["spt"]},
}

PERFIL = {
    "name": "teste",
    "rules": [
        {
            "id": "material.vif.bloqueado",
            "severity": "fail",
            "description": "Nenhum insumo da composição pode ter COV Alto.",
            "check": {
                "type": "material-field-forbidden",
                "campo": "saude.vif",
                "valores": ["Alto"],
            },
        },
        {
            "id": "orcamento.limite",
            "severity": "fail",
            "description": "Custo total não pode passar do orçamento.",
            "check": {"type": "budget-limit"},
        },
        {
            "id": "material.origem_local",
            "severity": "warn",
            "description": "Prefira insumos de origem local.",
            "check": {
                "type": "material-field-expected",
                "campo": "ecologico.origem_local",
                "valor": True,
            },
        },
        {
            "id": "material.provenance",
            "severity": "warn",
            "description": "Todo insumo deve dizer de onde vêm seus números.",
            "check": {"type": "provenance-required"},
        },
        {
            "id": "lote.cabe",
            "severity": "fail",
            "description": "A edificação mais recuos deve caber no lote.",
            "check": {"type": "lot-fit"},
        },
    ],
}


@pytest.fixture
def projeto():
    return carregar_projeto(PROJETO, origem="projeto.yaml")


@pytest.fixture
def materiais():
    return carregar_materiais(MATERIAIS, origem="materiais.yaml")


@pytest.fixture
def lote():
    return carregar_lote(LOTE, origem="lote.yaml")


@pytest.fixture
def perfil():
    return carregar_perfil(PERFIL, origem="perfil.yaml")
