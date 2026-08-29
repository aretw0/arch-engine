import zipfile
from xml.etree import ElementTree

import pytest

from arch_engine.loader import SpecError
from arch_engine.mesh import Caixa
from arch_engine.sh3d import (
    EXTRAS_PADRAO,
    TEMPLATES_DIR,
    empacotar,
    parametros_sh3d,
    renderizar_home_xml,
)

TEMPLATE = """<?xml version="1.0"?>
<home version="7300" name="${projeto_nome}" wallHeight="${edificacao_pe_direito}">
  <pieceOfFurniture name="edificacao" model="${modelo_obj}"
    x="${edificacao_x}" y="${edificacao_y}"
    width="${edificacao_largura}" depth="${edificacao_profundidade}"
    height="${edificacao_pe_direito}"/>
</home>
"""


def test_parametros_posicionam_a_peca_pelo_centro_dentro_dos_recuos(projeto, lote):
    p = parametros_sh3d(projeto, lote, nome_obj="casa/casa.obj")
    assert p["edificacao_x0"] == 150 and p["edificacao_y0"] == 500  # recuos lateral/frente em cm
    assert p["edificacao_x"] == 150 + 450 and p["edificacao_y"] == 500 + 600
    assert p["modelo_obj"] == "casa/casa.obj"


def test_renderiza_home_xml_valido(projeto, lote):
    xml = renderizar_home_xml(TEMPLATE, parametros_sh3d(projeto, lote, "casa/casa.obj"))
    raiz = ElementTree.fromstring(xml)
    peca = raiz.find("pieceOfFurniture")
    assert raiz.get("wallHeight") == "300"
    assert peca is not None and peca.get("model") == "casa/casa.obj" and peca.get("width") == "900"


def test_placeholder_sem_valor_e_erro_legivel(projeto, lote):
    with pytest.raises(SpecError, match=r"\$\{piscina\}"):
        renderizar_home_xml('<home name="${piscina}"/>', parametros_sh3d(projeto, lote, "x.obj"))


def test_xml_quebrado_e_erro_legivel(projeto, lote):
    with pytest.raises(SpecError, match="inválido"):
        renderizar_home_xml(
            '<home name="${projeto_nome}">', parametros_sh3d(projeto, lote, "x.obj")
        )


def test_empacota_home_xml_e_obj_no_zip(tmp_path, projeto, lote):
    obj = tmp_path / "casa.obj"
    obj.write_text("o casa\nv 0 0 0\n", encoding="utf-8")
    xml = renderizar_home_xml(TEMPLATE, parametros_sh3d(projeto, lote, "casa/casa.obj"))
    saida = empacotar(xml, tmp_path / "render" / "casa.sh3d", obj=obj, nome_obj="casa/casa.obj")
    with zipfile.ZipFile(saida) as z:
        assert sorted(z.namelist()) == ["Home.xml", "casa/casa.obj"]
        assert z.read("Home.xml").decode("utf-8") == xml


def test_bbox_da_malha_dita_as_dimensoes_da_peca(projeto, lote):
    p = parametros_sh3d(projeto, lote, "x.obj", Caixa(largura=900, altura=464, profundidade=1200))
    assert p["modelo_altura"] == 464  # pé-direito + cumeeira, não o YAML
    assert p["camera_top_z"] == 464 * 3
    sem_caixa = parametros_sh3d(projeto, lote, "x.obj")
    assert sem_caixa["modelo_altura"] == 300


def test_template_do_core_renderiza_com_os_parametros_do_core(projeto, lote):
    template = (TEMPLATES_DIR / "Home.xml").read_text(encoding="utf-8")
    xml = renderizar_home_xml(template, parametros_sh3d(projeto, lote, "modelo/modelo.obj"))
    raiz = ElementTree.fromstring(xml)
    assert raiz.find("compass") is not None
    assert raiz.find("light").get("model") == "luz/luz.obj"
    assert len(raiz.find("room").findall("point")) == 4


def test_extras_padrao_entram_no_zip(tmp_path, projeto, lote):
    template = (TEMPLATES_DIR / "Home.xml").read_text(encoding="utf-8")
    xml = renderizar_home_xml(template, parametros_sh3d(projeto, lote, "modelo/modelo.obj"))
    saida = empacotar(xml, tmp_path / "x.sh3d", extras=EXTRAS_PADRAO)
    with zipfile.ZipFile(saida) as z:
        assert "luz/luz.obj" in z.namelist()
