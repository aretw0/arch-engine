# ADR-005 · Metros no YAML, centímetros no CAD, Y-up na malha

**Status:** aceita · **Data:** 2026-08-29

## Contexto

Três sistemas, três convenções: quem escreve um projeto pensa em metros;
o OpenSCAD é adimensional com Z para cima; o Sweet Home 3D trabalha em
**centímetros** e, sendo Java 3D, com **Y para cima**.

## Decisão

- `data/*.yaml`: metros, graus, percentuais — a linguagem de quem projeta.
- `cad/gen/params.scad` e `Home.xml`: centímetros inteiros (`scad.parametros_cm`),
  para que as coordenadas do plano do SH3D e do SCAD coincidam sem fator.
- A troca Z-up → Y-up é feita na conversão OFF → OBJ
  (`(x, y, z) ↦ (x, z, −y)`, rotação de −90° em X, sem espelhamento), e o
  `Home.xml` mantém `modelRotation` identidade.
- Ângulos: graus no YAML e no SCAD; radianos onde o DTD do SH3D exige
  (`compass northDirection`, `yaw`, `pitch`) — a conversão é do `sh3d.py`.

## Consequências

- Um erro de unidade aparece como um fator 100 óbvio, não como um 2,54 sutil.
- Quem quiser polegadas muda `CM_POR_M` num lugar só.

## Referências

- DTD do SH3D (atributos `x`, `y`, `width` em cm; `northDirection`, `yaw` em rad):
  <https://www.sweethome3d.com/SweetHome3D.dtd>
- OpenSCAD *Export* (STL/OFF adimensionais): <https://en.wikibooks.org/wiki/OpenSCAD_User_Manual/Export>
