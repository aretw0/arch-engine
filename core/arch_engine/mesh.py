"""Conversão OFF → OBJ, sem dependências.

Por que existe: o OpenSCAD estável (2021.01, o pacote das distros) exporta
STL/OFF/AMF/3MF, mas não OBJ — e o Sweet Home 3D importa OBJ, não STL. OFF é
o formato mais simples que preserva vértices compartilhados, então a
conversão é textual e determinística. Ver ADR-002.

Eixos: OpenSCAD é Z-para-cima; Sweet Home 3D (Java 3D) é Y-para-cima. A
troca de eixos é feita aqui para que o `Home.xml` use `modelRotation`
identidade. Ver ADR-005.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class MeshError(ValueError):
    pass


@dataclass(frozen=True)
class Malha:
    vertices: tuple[tuple[float, float, float], ...]
    faces: tuple[tuple[int, ...], ...]  # índices 0-based


def ler_off(texto: str) -> Malha:
    linhas = [ln.split("#", 1)[0].strip() for ln in texto.splitlines()]
    linhas = [ln for ln in linhas if ln]
    if not linhas or not linhas[0].startswith("OFF"):
        raise MeshError("cabeçalho OFF ausente")
    # "OFF" sozinho ou "OFF nv nf ne" na mesma linha — ambos aparecem por aí.
    cabecalho = linhas[0][3:].split()
    corpo = linhas[1:]
    if not cabecalho:
        cabecalho, corpo = corpo[0].split(), corpo[1:]
    if len(cabecalho) < 2:
        raise MeshError("contagens de vértices/faces ausentes")
    n_vertices, n_faces = int(cabecalho[0]), int(cabecalho[1])
    if len(corpo) < n_vertices + n_faces:
        raise MeshError(f"esperava {n_vertices} vértices e {n_faces} faces, arquivo truncado")
    vertices = tuple(_vertice(corpo[i]) for i in range(n_vertices))
    faces = []
    for i in range(n_vertices, n_vertices + n_faces):
        campos = corpo[i].split()
        n = int(campos[0])
        faces.append(tuple(int(x) for x in campos[1 : 1 + n]))
    return Malha(vertices=vertices, faces=tuple(faces))


def _vertice(linha: str) -> tuple[float, float, float]:
    x, y, z = (float(v) for v in linha.split()[:3])
    return (x, y, z)


def escrever_obj(malha: Malha, nome: str, y_para_cima: bool = True) -> str:
    saida = ["# gerado por arch-engine (OFF → OBJ)", f"o {nome}"]
    for x, y, z in malha.vertices:
        # Z-up → Y-up: (x, y, z) ↦ (x, z, −y) é uma rotação de −90° em X, sem espelhar.
        px, py, pz = (x, z, -y) if y_para_cima else (x, y, z)
        saida.append(f"v {px:.6g} {py:.6g} {pz:.6g}")
    for face in malha.faces:
        saida.append("f " + " ".join(str(i + 1) for i in face))
    return "\n".join(saida) + "\n"


def off_para_obj(texto_off: str, nome: str, y_para_cima: bool = True) -> str:
    return escrever_obj(ler_off(texto_off), nome, y_para_cima)


def converter_arquivo(origem: Path, destino: Path, y_para_cima: bool = True) -> Malha:
    malha = ler_off(origem.read_text(encoding="utf-8"))
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(escrever_obj(malha, destino.stem, y_para_cima), encoding="utf-8")
    return malha
