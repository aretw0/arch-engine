from arch_engine.scad import gerar_params_scad, parametros_cm


def test_parametros_em_centimetros(projeto, lote):
    p = parametros_cm(projeto, lote)
    assert p["edificacao_largura"] == 900
    assert p["edificacao_profundidade"] == 1200
    assert p["edificacao_espessura_parede"] == 30
    assert p["edificacao_inclinacao_cobertura"] == 20
    assert p["lote_largura"] == 1500
    assert p["lote_recuo_frente"] == 500
    assert p["lote_declividade"] == 2


def test_sem_lote_nao_ha_variaveis_de_lote(projeto):
    assert not any(k.startswith("lote_") for k in parametros_cm(projeto, None))


def test_params_scad_e_texto_openscad_valido(projeto, lote):
    scad = gerar_params_scad(projeto, lote)
    assert scad.startswith("// GERADO")
    assert "edificacao_largura = 900;" in scad
    assert "lote_profundidade = 3000;" in scad
    assert all(ln.endswith(";") or ln.startswith("//") or not ln for ln in scad.splitlines())
