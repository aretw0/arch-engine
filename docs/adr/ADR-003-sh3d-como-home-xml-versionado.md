# ADR-003 · `.sh3d` é artefato; versiona-se o `Home.xml`

**Status:** aceita · **Data:** 2026-08-29

## Contexto

A especificação pedia um `casa.sh3d` no repositório, referenciando o OBJ de
forma relativa, e um `cli_runner.sh` com exemplo "headless" para imagens e
PDFs. Um `.sh3d`, porém, é um **zip** — binário, sem diff. Verificamos com o
autor do Sweet Home 3D (Emmanuel Puybaret) e com a release 5.3:

- Desde a 5.3 o zip contém uma entrada `Home.xml` que "descreve a casa em XML
  respeitando o DTD `SweetHome3D.dtd`"; a entrada serializada `Home` é mantida
  só por compatibilidade e será removida (`.sh3x`).
- "This entry is read in priority when a SH3D file is opened" — o XML manda.
- Não existe flag `-headless` oficial. O que existe: `ConsolePhotoGenerator`
  (classe utilitária do próprio SH3D) rodando com `-Dj3d.rend=noop` para
  fotos via SunFlow sem GPU, só nos níveis 3/4. Exportar a planta em PDF sem
  GUI **não tem caminho verificado**.

## Decisão

1. A fonte é `cad/sh3d/Home.xml` (texto, DTD oficial, `string.Template`).
   `core/templates/base_humanizer/Home.xml` é o ponto de partida agnóstico com
   ambiente, bússola, câmeras, luz e cômodo.
2. `arch-engine pack-sh3d` gera `cad/render/modelo.sh3d` = zip com `Home.xml`,
   `modelo/modelo.obj` (o OBJ do OpenSCAD, referenciado **relativamente dentro
   do zip**: `model="modelo/modelo.obj"`) e `luz/luz.obj` (corpo da luz).
3. As dimensões da peça vêm do **bbox da malha** (`mesh.bbox_obj`), não do
   YAML: o SH3D escala o modelo para `width × depth × height`; usar o
   pé-direito achataria a cumeeira.
4. `cli_runner.sh photo` documenta e executa o `ConsolePhotoGenerator`;
   o PDF da planta fica registrado como limitação, não como função fictícia.
5. Edição na GUI é bem-vinda: abrir o `.sh3d`, salvar, e `unzip -p` o
   `Home.xml` de volta para `cad/sh3d/` (repondo os placeholders).

## Consequências

- Diff legível de câmeras, luzes, cômodos e da peça.
- **Verificado com o parser do próprio SH3D 7.5** (`scripts/verify_sh3d.java`,
  jar do pacote Ubuntu `sweethome3d_7.5+dfsg`): o zip só com `Home.xml` é lido,
  a peça vem com 900 × 1200 × 463,79 cm, o `model="modelo/modelo.obj"` resolve
  e os bytes do OBJ são lidos de dentro do zip; cômodo, luz, bússola e câmeras
  chegam inteiros. Ressalva: `new HomeFileRecorder()` sem argumentos **não**
  instala o `HomeXMLHandler` e falha com "Missing entry Home or Home.xml" —
  a GUI instala; por isso o verificador usa `DefaultHomeInputStream` direto.
- Abrir na GUI e olhar a orientação/escala da peça continua no checklist da
  demo (não há display neste ambiente).

## Referências

- Blog *Sweet Home 3D 5.3*: <https://www.sweethome3d.com/blog/sweet-home-3d-5-3/>
- Fórum, *files format specifications* (resposta do autor):
  <https://www.sweethome3d.com/support/forum/viewthread_thread,8431>
- DTD: <https://www.sweethome3d.com/SweetHome3D.dtd>
- `ConsolePhotoGenerator` headless: <https://github.com/AnimMouse/SH3D-ConsolePhotoGenerator>
  e fórum *Headless Photo Render?*: <https://www.sweethome3d.com/support/forum/viewthread_thread,7464>
