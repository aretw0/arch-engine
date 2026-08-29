# Referências verificáveis

Tudo que o projeto afirma sobre ferramentas, normas e números tem uma fonte
aqui. Data de verificação: **2026-08-29**. Se um link morrer, a ADR que o
cita continua descrevendo o que foi lido.

## OpenSCAD

- Manual — linha de comando (formatos do `-o`, `-D`, `--render`, `--imgsize`, `--camera`):
  <https://en.wikibooks.org/wiki/OpenSCAD_User_Manual/Using_OpenSCAD_in_a_command_line_environment>
- Manual — exportação (STL/OFF/AMF/3MF/DXF/SVG/PNG/PDF e versões mínimas):
  <https://en.wikibooks.org/wiki/OpenSCAD_User_Manual/Export>
- Releases (última estável: 2021.01): <https://github.com/openscad/openscad/releases>
- Pedido de exportação OBJ (#351): <https://github.com/openscad/openscad/issues/351>

## Sweet Home 3D

- Release 5.3 (entrada `Home.xml`, DTD): <https://www.sweethome3d.com/blog/sweet-home-3d-5-3/>
- DTD oficial: <https://www.sweethome3d.com/SweetHome3D.dtd>
- Formato `.sh3d` explicado pelo autor (XML lido em prioridade; futuro `.sh3x`):
  <https://www.sweethome3d.com/support/forum/viewthread_thread,8431>
- Foto headless (`ConsolePhotoGenerator`, `-Dj3d.rend=noop`, níveis 3/4):
  <https://github.com/AnimMouse/SH3D-ConsolePhotoGenerator> ·
  <https://www.sweethome3d.com/support/forum/viewthread_thread,7464>

## Engenharia e solo

- ABNT NBR 6484:2020 — SPT: <https://www.target.com.br/produtos/normas-tecnicas/28006/nbr6484-solo-sondagem-de-simples-reconhecimento-com-spt-metodo-de-ensaio>
- ABNT NBR 13969:1997, Anexo A — ensaio de infiltração; avaliação crítica:
  <https://files.abrhidro.org.br/Eventos/Trabalhos/4/PAP020736.pdf>
- Embrapa — análise granulométrica:
  <https://www.infoteca.cnptia.embrapa.br/infoteca/bitstream/doc/1087262/1/Pt1Cap10Analisegranulometrica.pdf>
- Ecocentro IPEC — teste do frasco em campo: <https://saracura.org/2017/06/02/1733/>

## Sustentabilidade e saúde

- ICE v2.0 Summary Tables (Hammond & Jones, Bath, 2011):
  <https://kps.fsv.cvut.cz/upload/files/icev2.0summarytables.pdf>
- Rótulo francês de emissões de COV (A+/A/B/C; ISO 16000-9, EN 16516):
  <https://www.iaqip.wki.fraunhofer.de/en/data_and_facts/assessment_emissions_iaq/assessment_building_product_emission/french_regulation.html>

## Ecossistema (refarm)

- Registro de pacotes e lanes de release: `refarm/packages/README.md`
- Calibração de consumidores externos: `refarm/docs/EXTERNAL_CONSUMER_CALIBRATION.md`
- Política de release: `refarm/docs/RELEASE_POLICY.md`
- Padrão de demandas de consumidor: `enem/docs/ECOSYSTEM-DEMANDS.md`
- Vendorização de tarballs: `coop-vault/scripts/vendor_refarm.mjs`
