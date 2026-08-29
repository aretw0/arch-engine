"""Empacota um `.sh3d` a partir de texto: `Home.xml` + o `.obj` do OpenSCAD.

Um `.sh3d` é um zip. Desde a versão 5.3 ele carrega `Home.xml` (DTD oficial
`SweetHome3D.dtd`), lido em prioridade sobre a entrada serializada `Home`.
Versionamos o XML; o zip é artefato. Ver ADR-003.

O `Home.xml` fonte é um `string.Template`: `${edificacao_largura}` etc. são
os mesmos nomes de `scad.parametros_cm`, mais derivados para posicionar a
peça, as câmeras, a luz e a bússola no plano.
"""

from __future__ import annotations

import math
import zipfile
from pathlib import Path
from string import Template
from xml.etree import ElementTree

from arch_engine.loader import SpecError
from arch_engine.mesh import Caixa
from arch_engine.model import Lote, Projeto
from arch_engine.scad import parametros_cm

ENTRADA_HOME = "Home.xml"
TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates" / "base_humanizer"
# Entradas extras que todo .sh3d gerado carrega: o corpo mínimo da peça `light`.
EXTRAS_PADRAO = {"luz/luz.obj": TEMPLATES_DIR / "luz.obj"}


def parametros_sh3d(
    projeto: Projeto, lote: Lote | None, nome_obj: str, caixa: Caixa | None = None
) -> dict[str, float | int | str]:
    """Placeholders do Home.xml. Centímetros; ângulos em radianos onde o SH3D exige.

    `caixa` é o bbox real da malha exportada: é ela — não o YAML — que dita as
    dimensões da peça, para que cumeeiras e beirais não sejam achatados.
    """
    p: dict[str, float | int | str] = dict(parametros_cm(projeto, lote))
    largura, profundidade = int(p["edificacao_largura"]), int(p["edificacao_profundidade"])
    pe_direito = int(p["edificacao_pe_direito"])
    # SH3D posiciona a peça pelo centro; sem lote, a origem do plano é o canto da edificação.
    x0 = int(p.get("lote_recuo_lateral", 0))
    y0 = int(p.get("lote_recuo_frente", 0))
    x1, y1 = x0 + largura, y0 + profundidade
    cx, cy = x0 + largura / 2, y0 + profundidade / 2
    caixa = caixa or Caixa(largura=largura, altura=pe_direito, profundidade=profundidade)
    altura = max(caixa.altura, pe_direito)
    p.update(
        {
            "edificacao_x": cx,
            "edificacao_y": cy,
            "edificacao_x0": x0,
            "edificacao_y0": y0,
            "edificacao_x1": x1,
            "edificacao_y1": y1,
            "modelo_obj": nome_obj,
            "modelo_largura": round(caixa.largura, 2),
            "modelo_profundidade": round(caixa.profundidade, 2),
            "modelo_altura": round(caixa.altura, 2),
            "projeto_nome": projeto.nome,
            # Bússola no canto do plano; o SH3D guarda o norte em radianos.
            "compass_x": x0 - 150,
            "compass_y": y0 - 150,
            "lote_orientacao_norte_rad": round(
                math.radians(float(p.get("lote_orientacao_norte", 0))), 4
            ),
            # Aérea: atrás/acima, olhando para o centro; observador: diante da fachada (y0).
            "camera_top_x": cx,
            "camera_top_y": y1 + profundidade,
            "camera_top_z": altura * 3,
            "camera_top_yaw": round(math.pi, 4),
            "camera_obs_x": cx,
            "camera_obs_y": y0 - 600,
            "camera_obs_yaw": 0,
            # Sol de tarde, alto, a noroeste.
            "luz_x": x0 - 300,
            "luz_y": y0 - 300,
            "luz_z": altura * 2,
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
    except ValueError as e:  # "$" solto: o Template não sabe o que fazer com ele
        raise SpecError(origem, "template", f"{e}; escape cifrão literal como $$") from e
    try:
        ElementTree.fromstring(xml)
    except ElementTree.ParseError as e:
        raise SpecError(origem, "xml", f"Home.xml inválido após substituição: {e}") from e
    return xml


def empacotar(
    home_xml: str,
    saida: Path,
    obj: Path | None = None,
    nome_obj: str = "modelo/modelo.obj",
    extras: dict[str, Path] | None = None,
) -> Path:
    """Escreve o zip: `Home.xml`, o modelo e as entradas extras (`{entrada: arquivo}`)."""
    saida.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(saida, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr(ENTRADA_HOME, home_xml)
        if obj is not None:
            z.write(obj, nome_obj)
        for entrada, arquivo in (extras or {}).items():
            z.write(arquivo, entrada)
    return saida
