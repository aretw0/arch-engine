"""Ponta a ponta sobre a demo real: o exemplo é o teste de aceitação do core."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from arch_engine.cli import main

DEMO = Path(__file__).resolve().parent.parent / "examples" / "eco-house-demo"


@pytest.fixture
def demo(tmp_path: Path) -> Path:
    # Copia para não deixar artefatos no repositório durante os testes.
    destino = tmp_path / "eco-house-demo"
    shutil.copytree(DEMO, destino, ignore=shutil.ignore_patterns("artifacts", "render", "gen"))
    return destino


def test_demo_compila_e_passa_no_perfil(demo: Path):
    assert main(["build", str(demo)]) == 0
    qualidade = json.loads((demo / "artifacts" / "quality-report.json").read_text(encoding="utf-8"))
    assert "fail" not in qualidade["counts"]
    # A tinta de silicato não é local: um aviso, de propósito, para o relatório mostrar algo.
    assert qualidade["counts"] == {"warn": 1}
    assert qualidade["findings"][0]["locus"]["material"] == "tinta_mineral_silicato"
    quant = json.loads((demo / "artifacts" / "quantitativos.json").read_text(encoding="utf-8"))
    assert quant["custo_total"] < 60000
    assert quant["lote"] == "lote_a"
    maior_carbono = max(quant["itens"], key=lambda i: i["carbono_kg"])
    assert maior_carbono["material"] == "radier_concreto"  # o relatório existe para mostrar isso
    relatorio = (demo / "artifacts" / "relatorio.md").read_text(encoding="utf-8")
    assert "Lote A" in relatorio and "icev2.0summarytables.pdf" in relatorio


def test_trocar_a_tinta_por_esmalte_bloqueia_o_build(demo: Path):
    projeto = yaml.safe_load((demo / "data" / "projeto.yaml").read_text(encoding="utf-8"))
    for item in projeto["composicao"]:
        if item["material"] == "tinta_mineral_silicato":
            item["material"] = "esmalte_sintetico"
    (demo / "data" / "projeto.yaml").write_text(
        yaml.safe_dump(projeto, allow_unicode=True), encoding="utf-8"
    )
    assert main(["build", str(demo)]) == 1
    qualidade = json.loads((demo / "artifacts" / "quality-report.json").read_text(encoding="utf-8"))
    assert [f["ruleId"] for f in qualidade["findings"] if f["severity"] == "fail"] == [
        "material.vif.bloqueado"
    ]


def test_lote_apertado_bloqueia_sem_mudar_a_casa(demo: Path):
    lote = yaml.safe_load((demo / "data" / "terrenos" / "lote_a.yaml").read_text(encoding="utf-8"))
    lote["largura"] = 11.0  # 9 + 2 × 1,5 = 12 > 11
    (demo / "data" / "terrenos" / "lote_a.yaml").write_text(
        yaml.safe_dump(lote, allow_unicode=True), encoding="utf-8"
    )
    assert main(["build", str(demo)]) == 1
    quant = json.loads((demo / "artifacts" / "quantitativos.json").read_text(encoding="utf-8"))
    assert quant["bases"]["area_piso"] == 108.0  # a casa não mudou; só não cabe


@pytest.mark.skipif(shutil.which("openscad") is None, reason="OpenSCAD não instalado")
def test_openscad_exporta_a_casa_sem_o_terreno(demo: Path):
    assert main(["scad-params", str(demo)]) == 0
    off = demo / "cad" / "render" / "modelo.off"
    off.parent.mkdir(parents=True)
    subprocess.run(
        ["openscad", "-o", str(off), str(demo / "cad" / "main.scad")],
        check=True,
        capture_output=True,
    )
    assert main(["off2obj", str(off), str(off.with_suffix(".obj"))]) == 0
    assert main(["pack-sh3d", str(demo)]) == 0
