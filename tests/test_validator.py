import dataclasses

import pytest

from arch_engine.compiler import compilar
from arch_engine.loader import SpecError, carregar_perfil
from arch_engine.validator import CHECKER_ID, DOMAIN, tem_falhas, validar
from tests.conftest import PERFIL


def _regras(relatorio, severity):
    return sorted(f["ruleId"] for f in relatorio["findings"] if f["severity"] == severity)


def test_relatorio_e_um_quality_report(projeto, materiais, lote, perfil):
    relatorio = validar(compilar(projeto, materiais, lote), perfil)
    assert relatorio["capability"] == "quality:v1"
    assert relatorio["checkerId"] == CHECKER_ID
    assert relatorio["domain"] == DOMAIN
    assert relatorio["profileName"] == "teste"
    assert set(relatorio["counts"]) <= {"fail", "warn", "notice"}
    assert relatorio["metrics"]["materiais"] == 2
    assert relatorio["counts"] == {"warn": 2}  # sem fail: build passaria


def test_avisos_apontam_material_e_campo(projeto, materiais, lote, perfil):
    relatorio = validar(compilar(projeto, materiais, lote), perfil)
    assert _regras(relatorio, "warn") == ["material.origem_local", "material.provenance"]
    origem = next(f for f in relatorio["findings"] if f["ruleId"] == "material.origem_local")
    assert origem["locus"] == {
        "material": "tinta_mineral",
        "campo": "ecologico.origem_local",
        "valor": False,
    }
    assert not tem_falhas(relatorio)


def test_material_com_vif_alto_bloqueia(projeto, materiais, lote, perfil):
    tinta = projeto.composicao[1]
    com_esmalte = dataclasses.replace(
        projeto, composicao=(projeto.composicao[0], dataclasses.replace(tinta, material="esmalte"))
    )
    relatorio = validar(compilar(com_esmalte, materiais, lote), perfil)
    assert tem_falhas(relatorio)
    falha = next(f for f in relatorio["findings"] if f["ruleId"] == "material.vif.bloqueado")
    assert falha["locus"] == {"material": "esmalte", "campo": "saude.vif", "valor": "Alto"}


def test_orcamento_estourado_bloqueia(projeto, materiais, lote, perfil):
    pobre = dataclasses.replace(projeto, orcamento_limite=100.0)
    relatorio = validar(compilar(pobre, materiais, lote), perfil)
    assert "orcamento.limite" in _regras(relatorio, "fail")
    falha = next(f for f in relatorio["findings"] if f["ruleId"] == "orcamento.limite")
    assert falha["locus"]["excesso"] == pytest.approx(falha["locus"]["custo_total"] - 100.0)


def test_sem_orcamento_limite_nao_ha_o_que_checar(projeto, materiais, lote, perfil):
    livre = dataclasses.replace(projeto, orcamento_limite=None)
    relatorio = validar(compilar(livre, materiais, lote), perfil)
    assert "orcamento.limite" not in _regras(relatorio, "fail")


def test_edificacao_que_nao_cabe_no_lote_bloqueia(projeto, materiais, lote, perfil):
    apertado = dataclasses.replace(lote, largura=10.0)  # 9 + 2×1,5 = 12 > 10
    relatorio = validar(compilar(projeto, materiais, apertado), perfil)
    falhas = [f for f in relatorio["findings"] if f["ruleId"] == "lote.cabe"]
    assert [f["locus"]["eixo"] for f in falhas] == ["largura"]


def test_check_desconhecido_e_erro_de_perfil():
    perfil = carregar_perfil(
        {
            "name": "x",
            "rules": [
                {"id": "r", "severity": "fail", "description": "d", "check": {"type": "magia"}}
            ],
        },
        origem="perfil.yaml",
    )
    with pytest.raises(SpecError, match="magia"):
        validar(None, perfil)  # type: ignore[arg-type]


def test_perfil_fixture_tem_todas_as_regras_documentadas():
    assert [r["id"] for r in PERFIL["rules"]] == [
        "material.vif.bloqueado",
        "orcamento.limite",
        "material.origem_local",
        "material.provenance",
        "lote.cabe",
    ]
