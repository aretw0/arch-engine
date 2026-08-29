import pytest

from arch_engine.mesh import MeshError, bbox_obj, converter_arquivo, ler_off, off_para_obj

CUBO_OFF = """OFF
# cubo unitário, no formato que o OpenSCAD escreve
8 6 12
0 0 0
1 0 0
1 1 0
0 1 0
0 0 1
1 0 1
1 1 1
0 1 1
4 0 1 2 3
4 4 5 6 7
4 0 1 5 4
4 1 2 6 5
4 2 3 7 6
4 3 0 4 7
"""


def test_le_off_com_contagens_na_segunda_linha():
    malha = ler_off(CUBO_OFF)
    assert len(malha.vertices) == 8
    assert len(malha.faces) == 6
    assert malha.faces[0] == (0, 1, 2, 3)


def test_le_off_com_contagens_no_cabecalho():
    malha = ler_off("OFF 3 1 0\n0 0 0\n1 0 0\n0 1 0\n3 0 1 2\n")
    assert len(malha.vertices) == 3 and malha.faces == ((0, 1, 2),)


def test_obj_usa_indices_1_based_e_preserva_quads():
    obj = off_para_obj(CUBO_OFF, "cubo", y_para_cima=False)
    linhas = obj.splitlines()
    assert "o cubo" in linhas
    assert linhas.count("v 0 0 0") == 1
    assert sum(ln.startswith("v ") for ln in linhas) == 8
    assert "f 1 2 3 4" in linhas
    assert sum(ln.startswith("f ") for ln in linhas) == 6


def test_troca_de_eixos_leva_z_para_y():
    obj = off_para_obj("OFF 1 0 0\n1 2 3\n", "p")  # y_para_cima padrão
    assert "v 1 3 -2" in obj.splitlines()


def test_erros_legiveis():
    with pytest.raises(MeshError, match="cabeçalho"):
        ler_off("solid nada\n")
    with pytest.raises(MeshError, match="truncado"):
        ler_off("OFF\n8 6 12\n0 0 0\n")


def test_converter_arquivo_escreve_destino(tmp_path):
    origem = tmp_path / "casa.off"
    origem.write_text(CUBO_OFF, encoding="utf-8")
    destino = tmp_path / "render" / "casa.obj"
    malha = converter_arquivo(origem, destino)
    assert destino.exists() and "o casa" in destino.read_text()
    assert len(malha.faces) == 6


def test_bbox_do_obj_mede_as_tres_extensoes():
    caixa = bbox_obj("o x\nv 0 0 0\nv 900 450 -1200\nv 10 10 -10\n")
    assert (caixa.largura, caixa.altura, caixa.profundidade) == (900, 450, 1200)
    with pytest.raises(MeshError, match="sem vértices"):
        bbox_obj("o vazio\n")
