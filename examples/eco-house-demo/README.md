# eco-house-demo — casa ecológica, saudável e paramétrica

A instância de demonstração do `arch-engine`: uma residência térrea de
9 × 12 m em taipa de pilão, reboco de cal, cobertura de madeira de
reflorestamento e telha cerâmica, sobre radier de concreto, num lote de
15 × 30 m. Os números são ilustrativos; as fontes, não
([ADR-006](../../docs/adr/ADR-006-provenance-nos-insumos.md)).

## Rodar

```bash
uv run arch-engine build examples/eco-house-demo      # relatório + linter
scripts/cli_runner.sh all examples/eco-house-demo     # + OpenSCAD + .sh3d
```

Saídas (ignoradas pelo Git):

| Arquivo | O que é |
|---|---|
| `artifacts/relatorio.md` | quantitativos, custo, CO₂e/m², saúde dos insumos, achados do linter |
| `artifacts/quantitativos.json` | os mesmos números, para máquinas |
| `artifacts/quality-report.json` | relatório `quality:v1` (refarm) do perfil `eco-house-demo` |
| `artifacts/manifest.json` | manifesto `artifact:v1` com sha256 e provenance de cada artefato |
| `cad/gen/params.scad` | dimensões em cm para o OpenSCAD — **gerado, não edite** |
| `cad/render/modelo.{off,stl,png}` | a casa exportada pelo OpenSCAD (o terreno fica fora, está no `%`) |
| `cad/render/modelo.obj` | a mesma malha em OBJ, Y para cima, para o Sweet Home 3D |
| `cad/render/modelo.sh3d` | `Home.xml` + OBJ empacotados: abra no Sweet Home 3D |

## Os arquivos-fonte

```
data/projeto.yaml            dimensões + composição (base geométrica × insumo) + orçamento
data/materiais.yaml          7 insumos com preço, consumo, COV (vif), respirabilidade, CO₂e, origem, provenance
data/perfil_qualidade.yaml   5 regras: vif Alto → fail · orçamento → fail · cabe no lote → fail
                                       origem local → warn · provenance → warn
data/terrenos/lote_a.yaml    o container: 15 × 30 m, recuos 5/3/1,5 m, norte, declividade, solo
cad/casa.scad                módulo paramétrico: paredes (caixa − caixa) + cobertura de duas águas
cad/terreno.scad             wrapper do `container()` de core/templates/base_container.scad
cad/main.scad                inclui gen/params.scad; `%terreno(...)` + `casa(...)`
cad/sh3d/Home.xml            a casa no Sweet Home 3D, como texto (template)
engenharia/solo_tests.md     triagem: teste do frasco → infiltração (NBR 13969) → SPT (NBR 6484)
```

## Quebre de propósito (é para isso que o linter existe)

**1. Um insumo tóxico.** Em `data/projeto.yaml`, troque
`tinta_mineral_silicato` por `esmalte_sintetico` (que está no DB com
`saude.vif: Alto`) e rode o build:

```
  [fail] material.vif.bloqueado: Esmalte sintético (base solvente): saude.vif = 'Alto' é proibido
✗ build bloqueado: há achados com severidade fail
```

O relatório é escrito mesmo assim — o artefato explica o erro. Exit code 1.

**2. Um lote menor.** Em `data/terrenos/lote_a.yaml`, ponha `largura: 11.0`.
A casa (9 m) mais os recuos laterais (2 × 1,5 m) precisa de 12 m:

```
  [fail] lote.cabe: largura 12.00 m > lote 11.00 m
```

Repare que `quantitativos.json` não mudou: alterar o terreno não altera a
integridade matemática da casa — só a implantação. É o mesmo no OpenSCAD:
mude `LL`/`LP` em `main.scad` e a `casa()` continua idêntica.

**3. Um orçamento apertado.** `orcamento_limite: 30000` → `orcamento.limite` falha,
com o excesso no `locus`.

**4. Endureça o perfil.** Em `data/perfil_qualidade.yaml`, suba
`material.origem_local` para `severity: fail`: a tinta importada passa a
bloquear o build. Regras são dados, não código.

## O CAD

- Unidade: centímetros. `main.scad` lê `gen/params.scad` (gerado do YAML); sem
  ele, usa defaults — o arquivo abre sozinho no OpenSCAD.
- `%terreno(...)`: modificador de fundo — transparente no preview e **fora da
  exportação**. Por isso `modelo.off` contém só a casa.
- Exportar à mão: `openscad -o cad/render/modelo.off cad/main.scad`, depois
  `uv run arch-engine off2obj cad/render/modelo.off cad/render/modelo.obj`.
- Variações sem tocar no YAML: `openscad -D lote_largura=1200 -o x.png cad/main.scad`.

## O Sweet Home 3D

`cad/sh3d/Home.xml` é a fonte; `cad/render/modelo.sh3d` é o zip gerado
(`Home.xml` + `modelo/modelo.obj` + `luz/luz.obj`). A peça da casa tem as
dimensões do **bbox da malha** (a cumeeira conta), a bússola segue
`orientacao_norte_graus`, há uma câmera aérea, um observador diante da
fachada e um "sol de tarde".

Edite na GUI à vontade; para trazer de volta:

```bash
unzip -p cad/render/modelo.sh3d Home.xml > cad/sh3d/Home.xml   # reponha os placeholders
```

Checar sem GUI que o SH3D aceita o zip: `SH3D_JAR_DIR=/usr/share/sweethome3d scripts/cli_runner.sh sh3d-check`
(`apt install sweethome3d libjava3d-java`).
Foto headless (Java, sem GPU): `SH3D_JAR_DIR=/caminho/dos/jars scripts/cli_runner.sh photo`.
Planta em PDF sem GUI: não há caminho verificado
([ADR-003](../../docs/adr/ADR-003-sh3d-como-home-xml-versionado.md)).

## Checklist de verificação

O que já foi verificado e o que ainda depende de uma máquina com as ferramentas:

- [x] `build` ponta a ponta, com bloqueio por `vif`, orçamento e lote (`tests/test_demo_e2e.py`)
- [x] `Home.xml` do template renderiza e parseia como XML
- [x] `.sh3d` gerado contém `Home.xml`, o OBJ e a luz
- [x] `main.scad` exporta OFF/STL/PNG no OpenSCAD 2021.01 (AppImage; só a casa: 26 vértices, bbox 900 × 463,8 × 1200 cm)
- [x] O parser do Sweet Home 3D 7.5 lê `modelo.sh3d` gerado só com `Home.xml` e resolve o OBJ de dentro do zip (`scripts/cli_runner.sh sh3d-check`)
- [ ] Abrir na GUI: orientação e escala da peça OBJ (Y-up, cm) — ajustar `modelRotation` se necessário
- [ ] Câmeras e luz: posições são ponto de partida; ajustar na GUI e trazer o XML de volta
- [ ] `ConsolePhotoGenerator` com os jars da versão instalada

## Engenharia

[`engenharia/solo_tests.md`](engenharia/solo_tests.md) descreve a triagem de
solo em três camadas (frasco → infiltração → SPT) com as normas e o que volta
para `lote_a.yaml` quando cada ensaio é feito.
