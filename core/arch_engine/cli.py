"""CLI: texto → compilação → artefatos.

Subcomandos pequenos e componíveis, para o `cli_runner.sh` e o CI
encadearem com as ferramentas externas (OpenSCAD, Java) no meio.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from arch_engine import __version__
from arch_engine.compiler import Compilacao, compilar
from arch_engine.contracts import (
    artifact_hash,
    artifact_provenance,
    artifact_reference,
    task_artifact_manifest,
    validate_task_artifact_manifest,
)
from arch_engine.loader import SpecError
from arch_engine.mesh import MeshError, bbox_obj, converter_arquivo
from arch_engine.model import Material
from arch_engine.report import gerar_markdown
from arch_engine.scad import gerar_params_scad
from arch_engine.sh3d import EXTRAS_PADRAO, empacotar, parametros_sh3d, renderizar_home_xml
from arch_engine.validator import tem_falhas, validar
from arch_engine.workspace import Fontes, Instancia, carregar_instancia

PRODUCER = f"arch-engine@{__version__}"

# Artefatos conhecidos: (caminho relativo à instância, mediaType, role, labels)
ARTEFATOS_CONHECIDOS = [
    ("artifacts/relatorio.md", "text/markdown", "report", ["orcamento", "sustentabilidade"]),
    ("artifacts/quantitativos.json", "application/json", "dataset", ["orcamento"]),
    ("artifacts/quality-report.json", "application/json", "audit-trail", ["quality:v1"]),
    ("artifacts/insumos.json", "application/json", "dataset", ["insumos", "provenance:v1"]),
    ("cad/gen/params.scad", "text/x-openscad", "other", ["cad", "gerado"]),
    ("cad/render/modelo.off", "model/off", "other", ["cad", "openscad"]),
    ("cad/render/modelo.obj", "model/obj", "other", ["cad", "sweethome3d"]),
    ("cad/render/modelo.stl", "model/stl", "other", ["cad", "impressao"]),
    ("cad/render/modelo.png", "image/png", "other", ["cad", "render"]),
    ("cad/render/modelo.sh3d", "application/zip", "other", ["cad", "sweethome3d"]),
    ("cad/render/foto.png", "image/png", "other", ["sweethome3d", "render"]),
]


def _agora() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _run_id() -> str:
    return (
        os.environ.get("ARCH_ENGINE_RUN_ID")
        or os.environ.get("GITHUB_RUN_ID")
        or f"local-{_agora()}"
    )


def _escrever(caminho: Path, conteudo: str) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(conteudo, encoding="utf-8")


def _quantitativos_json(c: Compilacao) -> str:
    return json.dumps(
        {
            "projeto": c.projeto.nome,
            "moeda": c.projeto.moeda,
            "lote": c.lote.id if c.lote else None,
            "bases": {k: round(v, 4) for k, v in c.bases.items()},
            "itens": [
                {
                    "elemento": i.elemento,
                    "material": i.material.id,
                    "base": i.base,
                    "quantidade_base": round(i.quantidade_base, 4),
                    "consumo": round(i.consumo, 4),
                    "unidade": i.unidade,
                    "custo": round(i.custo, 2),
                    "carbono_kg": round(i.carbono_kg, 3),
                }
                for i in c.itens
            ],
            "custo_total": round(c.custo_total, 2),
            "carbono_total_kg": round(c.carbono_total_kg, 3),
        },
        ensure_ascii=False,
        indent=2,
    )


def _insumos_json(materiais: dict[str, Material]) -> str:
    """O DB de insumos como JSON, com a `provenance` de cada um no formato provenance:v1.

    É um artefato `dataset`: quem consome (a prova Node, uma landing page) lê
    isto, não o YAML — e a provenance vai junto, porque é ela que torna cada
    número defensável.
    """

    def provenance(m: Material) -> dict[str, Any] | None:
        if m.provenance is None:
            return None
        campos = {
            "channel": m.provenance.channel,
            "originLink": m.provenance.origin_link,
            "collectedAt": m.provenance.collected_at,
            "license": m.provenance.license,
            **m.provenance.extra,
        }
        return {k: v for k, v in campos.items() if v is not None}

    return json.dumps(
        {
            "schema": "arch-engine.insumos.v1",
            "materiais": {
                m.id: {
                    "nome": m.nome,
                    "unidade": m.unidade,
                    "preco_unitario": m.preco_unitario,
                    "consumo_por_m2": m.consumo_por_m2,
                    "saude": m.saude,
                    "ecologico": m.ecologico,
                    "provenance": provenance(m),
                }
                for m in materiais.values()
            },
        },
        ensure_ascii=False,
        indent=2,
    )


def escrever_manifest(instancia: Instancia, argv: list[str]) -> Path:
    """Manifesto `artifact:v1` de tudo que existe agora — pode rodar após o CAD."""
    agora = _agora()
    entradas = [artifact_hash(p) for p in instancia.fontes()]
    prov = artifact_provenance(
        run_id=_run_id(),
        producer=PRODUCER,
        produced_at=agora,
        command=" ".join(["arch-engine", *argv]),
        process={
            "command": "arch-engine",
            "args": argv,
            "display": " ".join(["arch-engine", *argv]),
        },
        source=instancia.raiz.name,
        input_hashes=entradas,
    )
    artefatos = [
        artifact_reference(
            id=rel.replace("/", ".").rsplit(".", 1)[0] + "." + rel.rsplit(".", 1)[1],
            uri=rel,
            media_type=media,
            role=role,
            hash=artifact_hash(instancia.raiz / rel),
            provenance=prov,
            labels=labels,
            review_state="unreviewed",
        )
        for rel, media, role, labels in ARTEFATOS_CONHECIDOS
        if (instancia.raiz / rel).exists()
    ]
    manifest = task_artifact_manifest(
        task_id=f"build-{instancia.raiz.name}", created_at=agora, artifacts=artefatos
    )
    problemas = validate_task_artifact_manifest(manifest)
    if problemas:  # pragma: no cover — guarda contra regressão do próprio espelho
        raise SpecError("manifest.json", ", ".join(problemas), "manifest inválido para artifact:v1")
    destino = instancia.artifacts_dir / "manifest.json"
    _escrever(destino, json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return destino


def _compilar(fontes: Fontes) -> tuple[Compilacao, dict]:
    compilacao = compilar(fontes.projeto, fontes.materiais, fontes.lote)
    return compilacao, validar(compilacao, fontes.perfil)


def _imprimir_findings(qualidade: dict) -> None:
    for f in qualidade["findings"]:
        print(f"  [{f['severity']}] {f['ruleId']}: {f['message']}")
    print(f"  counts: {qualidade['counts'] or 'nenhum achado'}")


def cmd_validate(args: argparse.Namespace) -> int:
    instancia = Instancia(Path(args.instancia))
    _, qualidade = _compilar(carregar_instancia(instancia, args.lote))
    _imprimir_findings(qualidade)
    return 1 if tem_falhas(qualidade) else 0


def cmd_scad_params(args: argparse.Namespace) -> int:
    instancia = Instancia(Path(args.instancia))
    fontes = carregar_instancia(instancia, args.lote)
    _escrever(instancia.params_scad, gerar_params_scad(fontes.projeto, fontes.lote))
    print(f"✓ {instancia.params_scad}")
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    instancia = Instancia(Path(args.instancia))
    fontes = carregar_instancia(instancia, args.lote)
    compilacao, qualidade = _compilar(fontes)
    agora = _agora()
    _escrever(
        instancia.artifacts_dir / "relatorio.md", gerar_markdown(compilacao, qualidade, agora)
    )
    _escrever(
        instancia.artifacts_dir / "quantitativos.json", _quantitativos_json(compilacao) + "\n"
    )
    _escrever(
        instancia.artifacts_dir / "quality-report.json",
        json.dumps(qualidade, ensure_ascii=False, indent=2) + "\n",
    )
    _escrever(instancia.params_scad, gerar_params_scad(fontes.projeto, fontes.lote))
    _escrever(instancia.artifacts_dir / "insumos.json", _insumos_json(fontes.materiais) + "\n")
    manifest = escrever_manifest(instancia, ["build", args.instancia])
    print(f"✓ {instancia.artifacts_dir / 'relatorio.md'}")
    print(f"✓ {instancia.params_scad}")
    print(f"✓ {manifest}")
    _imprimir_findings(qualidade)
    if tem_falhas(qualidade):
        print("✗ build bloqueado: há achados com severidade fail", file=sys.stderr)
        return 1
    return 0


def cmd_manifest(args: argparse.Namespace) -> int:
    destino = escrever_manifest(Instancia(Path(args.instancia)), ["manifest", args.instancia])
    print(f"✓ {destino}")
    return 0


def cmd_off2obj(args: argparse.Namespace) -> int:
    malha = converter_arquivo(Path(args.origem), Path(args.destino), y_para_cima=not args.z_up)
    print(f"✓ {args.destino} ({len(malha.vertices)} vértices, {len(malha.faces)} faces)")
    return 0


def cmd_pack_sh3d(args: argparse.Namespace) -> int:
    instancia = Instancia(Path(args.instancia))
    fontes = carregar_instancia(instancia, args.lote)
    obj = Path(args.obj) if args.obj else instancia.render_dir / "modelo.obj"
    if not obj.exists():
        print(
            f"✗ modelo OBJ não encontrado: {obj} (rode o OpenSCAD e `off2obj` antes)",
            file=sys.stderr,
        )
        return 2
    nome_obj = "modelo/modelo.obj"
    caixa = bbox_obj(obj.read_text(encoding="utf-8"))
    xml = renderizar_home_xml(
        instancia.home_xml.read_text(encoding="utf-8"),
        parametros_sh3d(fontes.projeto, fontes.lote, nome_obj, caixa),
        origem=str(instancia.home_xml),
    )
    saida = Path(args.saida) if args.saida else instancia.render_dir / "modelo.sh3d"
    empacotar(xml, saida, obj=obj, nome_obj=nome_obj, extras=EXTRAS_PADRAO)
    print(f"✓ {saida}")
    return 0


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="arch-engine", description="Declarative Physical-Design Stack"
    )
    parser.add_argument("--version", action="version", version=PRODUCER)
    sub = parser.add_subparsers(dest="comando", required=True)

    def com_instancia(p: argparse.ArgumentParser) -> argparse.ArgumentParser:
        p.add_argument("instancia", help="pasta da instância (ex.: examples/eco-house-demo)")
        p.add_argument("--lote", help="nome do lote em data/terrenos/ (padrão: o primeiro)")
        return p

    com_instancia(
        sub.add_parser("build", help="compila, valida e escreve os artefatos")
    ).set_defaults(fn=cmd_build)
    com_instancia(sub.add_parser("validate", help="só o linter de restrições")).set_defaults(
        fn=cmd_validate
    )
    com_instancia(sub.add_parser("scad-params", help="gera cad/gen/params.scad")).set_defaults(
        fn=cmd_scad_params
    )
    com_instancia(
        sub.add_parser("manifest", help="reescreve artifacts/manifest.json")
    ).set_defaults(fn=cmd_manifest)
    pack = com_instancia(sub.add_parser("pack-sh3d", help="empacota Home.xml + obj em .sh3d"))
    pack.add_argument("--obj", help="OBJ do modelo (padrão: cad/render/modelo.obj)")
    pack.add_argument("--saida", help="destino (padrão: cad/render/modelo.sh3d)")
    pack.set_defaults(fn=cmd_pack_sh3d)
    o2o = sub.add_parser("off2obj", help="converte OFF (OpenSCAD) em OBJ (Sweet Home 3D)")
    o2o.add_argument("origem")
    o2o.add_argument("destino")
    o2o.add_argument("--z-up", action="store_true", help="não trocar eixos (mantém Z para cima)")
    o2o.set_defaults(fn=cmd_off2obj)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = construir_parser().parse_args(argv)
    try:
        return args.fn(args)
    except (SpecError, MeshError) as erro:
        print(f"✗ {erro}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
