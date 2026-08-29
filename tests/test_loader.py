import copy

import pytest

from arch_engine.loader import SpecError, carregar_materiais, carregar_projeto
from tests.conftest import MATERIAIS, PROJETO


def test_projeto_carrega_dimensoes_e_composicao(projeto):
    assert projeto.nome == "Casa de teste"
    assert projeto.dimensoes.largura == 9.0
    assert projeto.dimensoes.inclinacao_cobertura_graus == 20
    assert [i.material for i in projeto.composicao] == ["taipa", "tinta_mineral"]
    assert projeto.composicao[0].fator == 1.0


def test_materiais_carregam_provenance_e_campo_pontuado(materiais):
    taipa = materiais["taipa"]
    assert taipa.provenance is not None
    assert taipa.provenance.channel == "literature"
    assert taipa.campo("saude.vif") == "Isento"
    assert taipa.campo("ecologico.origem_local") is True
    assert taipa.campo("nao.existe") is None
    assert materiais["tinta_mineral"].provenance is None


def test_erro_de_esquema_aponta_arquivo_e_caminho():
    dados = copy.deepcopy(PROJETO)
    del dados["dimensoes"]["pe_direito"]
    with pytest.raises(SpecError) as erro:
        carregar_projeto(dados, origem="data/projeto.yaml")
    assert "data/projeto.yaml" in str(erro.value)
    assert "dimensoes.pe_direito" in str(erro.value)


def test_schema_desconhecido_e_rejeitado():
    dados = copy.deepcopy(MATERIAIS)
    dados["schema"] = "outra-coisa.v9"
    with pytest.raises(SpecError, match="schema"):
        carregar_materiais(dados, origem="materiais.yaml")


def test_numero_invalido_e_rejeitado():
    dados = copy.deepcopy(MATERIAIS)
    dados["materiais"]["taipa"]["preco_unitario"] = "caro"
    with pytest.raises(SpecError, match="materiais.taipa.preco_unitario"):
        carregar_materiais(dados, origem="materiais.yaml")
