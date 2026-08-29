import math

import pytest

from arch_engine.compiler import SpecError, bases_geometricas, compilar


def test_bases_geometricas_derivam_das_dimensoes(projeto):
    bases = bases_geometricas(projeto.dimensoes)
    assert bases["area_piso"] == pytest.approx(108.0)
    assert bases["perimetro"] == pytest.approx(42.0)
    # 42 m × 3 m × (1 − 15 % de aberturas)
    assert bases["area_paredes_externas"] == pytest.approx(107.1)
    assert bases["area_cobertura"] == pytest.approx(108.0 / math.cos(math.radians(20)))
    # (9 − 2·0,3) × (12 − 2·0,3) × 3
    assert bases["volume_interno"] == pytest.approx(8.4 * 11.4 * 3.0)


def test_compilacao_cruza_dimensoes_e_insumos(projeto, materiais, lote):
    resultado = compilar(projeto, materiais, lote)
    taipa = resultado.itens[0]
    assert taipa.elemento == "paredes externas"
    assert taipa.quantidade_base == pytest.approx(107.1)
    assert taipa.consumo == pytest.approx(107.1 * 0.30)
    assert taipa.unidade == "m3"
    assert taipa.custo == pytest.approx(107.1 * 0.30 * 350.0)
    assert taipa.carbono_kg == pytest.approx(107.1 * 0.30 * 45.6)
    assert resultado.custo_total == pytest.approx(sum(i.custo for i in resultado.itens))
    assert resultado.carbono_total_kg == pytest.approx(sum(i.carbono_kg for i in resultado.itens))
    assert resultado.lote is lote


def test_fator_escala_a_base(projeto, materiais):
    item = projeto.composicao[0]
    projeto_dobro = type(projeto)(
        nome=projeto.nome,
        dimensoes=projeto.dimensoes,
        composicao=(type(item)(item.elemento, item.material, item.base, fator=2.0),),
    )
    resultado = compilar(projeto_dobro, materiais, lote=None)
    assert resultado.itens[0].quantidade_base == pytest.approx(214.2)


def test_material_desconhecido_na_composicao_e_erro(projeto, materiais):
    item = projeto.composicao[0]
    quebrado = type(projeto)(
        nome=projeto.nome,
        dimensoes=projeto.dimensoes,
        composicao=(type(item)(item.elemento, "unobtainium", item.base),),
    )
    with pytest.raises(SpecError, match="unobtainium"):
        compilar(quebrado, materiais, lote=None)


def test_base_desconhecida_e_erro(projeto, materiais):
    item = projeto.composicao[0]
    quebrado = type(projeto)(
        nome=projeto.nome,
        dimensoes=projeto.dimensoes,
        composicao=(type(item)(item.elemento, item.material, "area_da_lua"),),
    )
    with pytest.raises(SpecError, match="area_da_lua"):
        compilar(quebrado, materiais, lote=None)
