# ADR-002 · OBJ nasce de OFF convertido em Python

**Status:** aceita · **Data:** 2026-08-29

## Contexto

O Sweet Home 3D importa modelos em OBJ, DAE, 3DS e KMZ — não em STL. A
especificação inicial pedia "o `.obj` gerado pelo OpenSCAD". Verificamos:

- A última release estável do OpenSCAD é a **2021.01** (GitHub Releases não
  lista nada mais novo). É a versão empacotada no Ubuntu (22.04: `2021.01-4build1`).
- Os formatos aceitos pelo `-o` no manual de linha de comando são
  `stl, off, wrl, amf, 3mf, csg, dxf, svg, pdf, png, echo, ast, term, nef3,
  nefdbg, param, pov` — **sem `obj`**. O pedido de exportação OBJ
  (openscad/openscad#351, aberto em 2013) foi atendido apenas em snapshots
  de desenvolvimento.

## Decisão

- O pipeline exporta **OFF** (`openscad -o modelo.off`) e converte para OBJ em
  `core/arch_engine/mesh.py` (`arch-engine off2obj`). OFF preserva vértices
  compartilhados e é textual: a conversão é ~40 linhas sem dependências.
- STL continua sendo exportado para impressão 3D; PNG para o relatório.
- Quem tiver um snapshot com OBJ nativo pode pular a conversão — o
  `cli_runner.sh` não impede, mas o caminho padrão é o que funciona no apt.

## Consequências

- O CI usa `apt install openscad` sem AppImage nem nightly.
- A troca de eixos Z-up → Y-up (ADR-005) acontece na conversão, no mesmo lugar.
- Se o OpenSCAD lançar uma estável com OBJ, o conversor vira opcional, e esta
  ADR é substituída.

## Referências

- OpenSCAD User Manual, *Using OpenSCAD in a command line environment*:
  <https://en.wikibooks.org/wiki/OpenSCAD_User_Manual/Using_OpenSCAD_in_a_command_line_environment>
- OpenSCAD User Manual, *Export*: <https://en.wikibooks.org/wiki/OpenSCAD_User_Manual/Export>
- Releases: <https://github.com/openscad/openscad/releases>
- Pedido de OBJ: <https://github.com/openscad/openscad/issues/351>
- Formatos de importação do Sweet Home 3D (FAQ/Import furniture wizard): OBJ, DAE, 3DS, KMZ.
