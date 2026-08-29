"""Empacota um `.sh3d` a partir de texto: `Home.xml` + o `.obj` do OpenSCAD.

Um `.sh3d` é um zip. Desde a versão 5.3 ele carrega `Home.xml` (DTD oficial
`SweetHome3D.dtd`), lido em prioridade sobre a entrada serializada `Home`.
Versionamos o XML; o zip é artefato. Ver ADR-003.

O `Home.xml` fonte é um `string.Template`: `${edificacao_largura}` etc. são
os mesmos nomes de `scad.parametros_cm`, mais alguns derivados úteis para
posicionar a peça no plano (`${edificacao_x}`, `${edificacao_y}`).
"""

from __future__ import annotations

import zipfile
from pathlib import Path
from string import Template
from xml.etree import ElementTree

from arch_engine.loader import SpecError
from arch_engine.model import Lote, Projeto
from arch_engine.scad import parametros_cm

ENTRADA_HOME = "Home.xml"


def parametros_sh3d(
    projeto: Projeto, lote: Lote | None, nome_obj: str
) -> dict[str, float | int | str]:
    p: dict[str, float | int | str] = dict(parametros_cm(projeto, lote))
    largura, profundidade = int(p["edificacao_largura"]), int(p["edificacao_profundidade"])
    # SH3D posiciona a peça pelo centro; sem lote, a origem do plano é o canto da edificação.
    x0 = int(p.get("lote_recuo_lateral", 0))
    y0 = int(p.get("lote_recuo_frente", 0))
    p.update(
        {
            "edificacao_x": x0 + largura / 2,
            "edificacao_y": y0 + profundidade / 2,
            "edificacao_x0": x0,
            "edificacao_y0": y0,
            "edificacao_x1": x0 + largura,
            "edificacao_y1": y0 + profundidade,
            "modelo_obj": nome_obj,
            "projeto_nome": projeto.nome,
        }
    )
    return p


def renderizar_home_xml(
    template: str, parametros: dict[str, float | int | str], origem: str = "Home.xml"
) -> str:
    try:
        xml = Template(template).substitute(parametros)
    except KeyError as e:
        raise SpecError(origem, f"${{{e.args[0]}}}", "placeholder sem valor correspondente") from e
    try:
        ElementTree.fromstring(xml)
    except ElementTree.ParseError as e:
        raise SpecError(origem, "xml", f"Home.xml inválido após substituição: {e}") from e
    return xml


def empacotar(
    home_xml: str, saida: Path, obj: Path | None = None, nome_obj: str = "modelo/modelo.obj"
) -> Path:
    saida.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(saida, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr(ENTRADA_HOME, home_xml)
        if obj is not None:
            z.write(obj, nome_obj)
    return saida
