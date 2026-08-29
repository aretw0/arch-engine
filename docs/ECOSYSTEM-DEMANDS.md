# Demandas do consumidor arch-engine ao ecossistema

Este arquivo evita que necessidades genéricas virem implementações privadas
aqui. Segue o formato do `enem/docs/ECOSYSTEM-DEMANDS.md`.

## Baseline consumido

- Packet de handoff `refarm/.refarm/handoff/vault-seed/2026-08-29`
  (`@refarm.dev/quality-contract-v1@0.1.0`, `@refarm.dev/artifact-contract-v1@0.1.0`),
  vendorizado por `scripts/vendor_refarm.mjs`.
- Formas espelhadas em Python: `core/arch_engine/contracts.py` (ADR-004).
- Prova de consumo: `npm run test:refarm` sobre os artefatos do `arch-engine build`.

O que este consumidor traz de novo para o refarm: **um produtor que não é
JavaScript**. Se `quality:v1` e `artifact:v1` servem a um motor Python via
JSON, são contratos de verdade, não tipos TypeScript.

## Demandas que devem virar release

| Prioridade | Dono | Bloco esperado | Prova que o arch-engine fornece |
|---|---|---|---|
| P0 | refarm | release npm de `quality-contract-v1` e `artifact-contract-v1` (sem deps, já `consumer-proven`) | `scripts/test_refarm_contracts.mjs` passa; o job `refarm-proof` deixa de ser manual e vira `npm ci` |
| P0 | refarm | JSON Schema publicado ao lado de cada `types.ts` (ou gerado deles) | `contracts.py` encolhe para `jsonschema.validate`; fim do espelho manual |
| P1 | refarm | `provenance-contract-v1` na lane `consumer-ready` | cada insumo de `materiais.yaml` carrega `provenance`; o validador aplica os mesmos checks nomeados (`has-channel`, `collected-at-valid`, …) |
| P1 | refarm | `vendor_refarm` como comando do refarm (`refarm handoff vendor`) | é a terceira cópia do script (coop-vault, enem, arch-engine) |
| P2 | refarm | `ds` + `local-surface` para uma landing page estática que renderize `relatorio.md` e `manifest.json` | página do exemplo publicada em GitHub Pages sem CSS próprio |
| P2 | refarm | `records-contract-v1` (YAML-LD) para `materiais.yaml` como registros com relações insumo → fonte | DB de materiais navegável em um vault-seed |

## Defeitos e atritos observados

- `provenance-contract-v1` não está no packet de handoff, embora o README do
  refarm o marque `consumer-proven`; o espelho Python foi feito a partir do
  `types.ts` e não pôde ser provado contra o tarball.
- A `runQualityV1Conformance` assume um checker sobre texto com regras regex
  (`"alpha beta alpha"`); um checker de domínio físico não consegue usá-la.
  Falta um `validateQualityReport(report)` puro, simétrico ao
  `validateTaskArtifactManifest`.
- `TaskArtifactReference.role` é um enum fechado (`dataset|report|…|other`):
  artefatos CAD caem todos em `other` e se distinguem só por `labels`.

## Seam local temporário

- `contracts.py` espelha três `types.ts` à mão. Quando o P0 de JSON Schema
  sair, este arquivo é o primeiro a ser reduzido.
- O job `refarm-proof` do CI clona o refarm e gera o packet — caro e frágil;
  existe só para não deixar a prova depender da máquina de uma pessoa.
