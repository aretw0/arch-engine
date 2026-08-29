"""Layout de uma *instância* (um caso de uso): onde cada arquivo-fonte mora.

O core não impõe domínio, mas impõe *lugar*: `data/` descreve, `cad/`
modela, `artifacts/` recebe o que foi gerado. Toda a CLI passa por aqui, e
um exemplo novo só precisa seguir esta árvore.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from arch_engine.loader import (
    SpecError,
    carregar_lote_arquivo,
    carregar_materiais_arquivo,
    carregar_perfil_arquivo,
    carregar_projeto_arquivo,
)
from arch_engine.model import Lote, Material, Perfil, Projeto


@dataclass(frozen=True)
class Instancia:
    raiz: Path

    @property
    def projeto_yaml(self) -> Path:
        return self.raiz / "data" / "projeto.yaml"

    @property
    def materiais_yaml(self) -> Path:
        return self.raiz / "data" / "materiais.yaml"

    @property
    def perfil_yaml(self) -> Path:
        return self.raiz / "data" / "perfil_qualidade.yaml"

    @property
    def terrenos_dir(self) -> Path:
        return self.raiz / "data" / "terrenos"

    @property
    def cad_dir(self) -> Path:
        return self.raiz / "cad"

    @property
    def params_scad(self) -> Path:
        return self.cad_dir / "gen" / "params.scad"

    @property
    def render_dir(self) -> Path:
        return self.cad_dir / "render"

    @property
    def home_xml(self) -> Path:
        return self.cad_dir / "sh3d" / "Home.xml"

    @property
    def artifacts_dir(self) -> Path:
        return self.raiz / "artifacts"

    def fontes(self) -> list[Path]:
        """Arquivos-fonte cujo hash entra na provenance dos artefatos."""
        return [
            p
            for p in [self.projeto_yaml, self.materiais_yaml, self.perfil_yaml, *self.lotes()]
            if p.exists()
        ]

    def lotes(self) -> list[Path]:
        if not self.terrenos_dir.is_dir():
            return []
        return sorted(self.terrenos_dir.glob("*.yaml"))

    def caminho_do_lote(self, nome: str | None) -> Path | None:
        lotes = self.lotes()
        if nome is None:
            return lotes[0] if lotes else None
        candidato = self.terrenos_dir / f"{nome}.yaml"
        if not candidato.exists():
            disponiveis = ", ".join(p.stem for p in lotes) or "nenhum"
            raise SpecError(
                str(self.terrenos_dir), nome, f"lote não encontrado; disponíveis: {disponiveis}"
            )
        return candidato


@dataclass(frozen=True)
class Fontes:
    projeto: Projeto
    materiais: dict[str, Material]
    perfil: Perfil
    lote: Lote | None
    lote_path: Path | None


def carregar_instancia(instancia: Instancia, lote: str | None = None) -> Fontes:
    for obrigatorio in (instancia.projeto_yaml, instancia.materiais_yaml, instancia.perfil_yaml):
        if not obrigatorio.exists():
            raise SpecError(
                str(instancia.raiz),
                obrigatorio.relative_to(instancia.raiz).as_posix(),
                "arquivo ausente",
            )
    lote_path = instancia.caminho_do_lote(lote)
    return Fontes(
        projeto=carregar_projeto_arquivo(instancia.projeto_yaml),
        materiais=carregar_materiais_arquivo(instancia.materiais_yaml),
        perfil=carregar_perfil_arquivo(instancia.perfil_yaml),
        lote=carregar_lote_arquivo(lote_path) if lote_path else None,
        lote_path=lote_path,
    )
