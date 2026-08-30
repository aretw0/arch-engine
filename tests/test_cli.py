import json
import zipfile
from pathlib import Path

import yaml

from arch_engine.cli import main
from tests.conftest import LOTE, MATERIAIS, PERFIL, PROJETO
from tests.test_mesh import CUBO_OFF
from tests.test_sh3d import TEMPLATE


def _instancia(tmp_path: Path, projeto: dict = PROJETO) -> Path:
    raiz = tmp_path / "demo"
    (raiz / "data" / "terrenos").mkdir(parents=True)
    (raiz / "cad" / "sh3d").mkdir(parents=True)
    (raiz / "data" / "projeto.yaml").write_text(
        yaml.safe_dump(projeto, allow_unicode=True), encoding="utf-8"
    )
    (raiz / "data" / "materiais.yaml").write_text(
        yaml.safe_dump(MATERIAIS, allow_unicode=True), encoding="utf-8"
    )
    (raiz / "data" / "perfil_qualidade.yaml").write_text(
        yaml.safe_dump(PERFIL, allow_unicode=True), encoding="utf-8"
    )
    (raiz / "data" / "terrenos" / "lote_a.yaml").write_text(
        yaml.safe_dump(LOTE, allow_unicode=True), encoding="utf-8"
    )
    (raiz / "cad" / "sh3d" / "Home.xml").write_text(TEMPLATE, encoding="utf-8")
    return raiz


def test_build_gera_todos_os_artefatos_e_passa(tmp_path, capsys):
    raiz = _instancia(tmp_path)
    assert main(["build", str(raiz)]) == 0
    relatorio = (raiz / "artifacts" / "relatorio.md").read_text(encoding="utf-8")
    assert "# Relatório · Casa de teste" in relatorio
    assert "`area_paredes_externas`" in relatorio
    assert "material.origem_local" in relatorio
    quant = json.loads((raiz / "artifacts" / "quantitativos.json").read_text())
    assert quant["lote"] == "lote_teste" and len(quant["itens"]) == 2
    qualidade = json.loads((raiz / "artifacts" / "quality-report.json").read_text())
    assert qualidade["capability"] == "quality:v1" and qualidade["counts"] == {"warn": 2}
    insumos = json.loads((raiz / "artifacts" / "insumos.json").read_text())
    assert insumos["materiais"]["taipa"]["provenance"] == {
        "channel": "literature",
        "originLink": "https://example.org/ice",
    }
    assert insumos["materiais"]["tinta_mineral"]["provenance"] is None
    assert "edificacao_largura = 900;" in (raiz / "cad" / "gen" / "params.scad").read_text()
    manifest = json.loads((raiz / "artifacts" / "manifest.json").read_text())
    assert manifest["schema"] == "sovereign.task-artifacts.v1"
    uris = {a["uri"] for a in manifest["artifacts"]}
    assert {
        "artifacts/relatorio.md",
        "artifacts/quality-report.json",
        "artifacts/insumos.json",
        "cad/gen/params.scad",
    } <= uris
    assert all(len(a["hash"]["value"]) == 64 for a in manifest["artifacts"])
    assert len(manifest["artifacts"][0]["provenance"]["inputHashes"]) == 4
    insumos_ref = next(a for a in manifest["artifacts"] if a["uri"] == "artifacts/insumos.json")
    assert insumos_ref["role"] == "dataset"
    assert "✓" in capsys.readouterr().out


def test_build_bloqueia_com_fail_mas_ainda_escreve_o_relatorio(tmp_path, capsys):
    projeto = json.loads(json.dumps(PROJETO))
    projeto["composicao"][1]["material"] = "esmalte"
    raiz = _instancia(tmp_path, projeto)
    assert main(["build", str(raiz)]) == 1
    assert "material.vif.bloqueado" in (raiz / "artifacts" / "relatorio.md").read_text(
        encoding="utf-8"
    )
    assert "bloqueado" in capsys.readouterr().err


def test_validate_so_lista_achados(tmp_path, capsys):
    raiz = _instancia(tmp_path)
    assert main(["validate", str(raiz)]) == 0
    assert "[warn] material.origem_local" in capsys.readouterr().out
    assert not (raiz / "artifacts").exists()


def test_lote_inexistente_e_erro_2(tmp_path, capsys):
    raiz = _instancia(tmp_path)
    assert main(["validate", str(raiz), "--lote", "marte"]) == 2
    assert "disponíveis: lote_a" in capsys.readouterr().err


def test_off2obj_e_pack_sh3d_fecham_o_ciclo_cad(tmp_path, capsys):
    raiz = _instancia(tmp_path)
    off = raiz / "cad" / "render" / "modelo.off"
    off.parent.mkdir(parents=True)
    off.write_text(CUBO_OFF, encoding="utf-8")
    assert main(["off2obj", str(off), str(raiz / "cad" / "render" / "modelo.obj")]) == 0
    assert main(["pack-sh3d", str(raiz)]) == 0
    with zipfile.ZipFile(raiz / "cad" / "render" / "modelo.sh3d") as z:
        assert sorted(z.namelist()) == ["Home.xml", "luz/luz.obj", "modelo/modelo.obj"]
        assert 'model="modelo/modelo.obj"' in z.read("Home.xml").decode()
    # o manifest pós-CAD enxerga os artefatos novos
    assert main(["manifest", str(raiz)]) == 0
    uris = {
        a["uri"]
        for a in json.loads((raiz / "artifacts" / "manifest.json").read_text())["artifacts"]
    }
    assert {"cad/render/modelo.obj", "cad/render/modelo.sh3d"} <= uris


def test_pack_sh3d_sem_obj_orienta(tmp_path, capsys):
    raiz = _instancia(tmp_path)
    assert main(["pack-sh3d", str(raiz)]) == 2
    assert "off2obj" in capsys.readouterr().err
