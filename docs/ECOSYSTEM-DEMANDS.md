# Demandas do consumidor arch-engine ao ecossistema

Este arquivo evita que necessidades genéricas virem implementações privadas
aqui. Segue o formato do `enem/docs/ECOSYSTEM-DEMANDS.md`.

## Baseline consumido

- Packet de handoff `refarm/.refarm/handoff/vault-seed/2026-08-30` (25 pacotes):
  `@refarm.dev/quality-contract-v1@0.1.0`, `@refarm.dev/artifact-contract-v1@0.1.0`,
  `@refarm.dev/provenance-contract-v1@0.1.0`, vendorizados por `scripts/vendor_refarm.mjs`.
- Formas espelhadas em Python: `core/arch_engine/contracts.py` (ADR-004).
- Prova de consumo: `npm run test:refarm` sobre os artefatos do `arch-engine build` —
  `validateTaskArtifactManifest` (manifest), `validateQualityReport` (quality-report),
  `readProvenance` + `verifyProvenance` (cada insumo de `artifacts/insumos.json`).

## Demandas atendidas (2026-08-29/30)

| Demanda | Como foi atendida no refarm | Prova aqui |
|---|---|---|
| `validateQualityReport` puro, simétrico ao `validateTaskArtifactManifest` | `quality-contract-v1` `aaa3b6cc` — path por defeito, `counts` tem de ser a contagem exata de `findings` | `test_refarm_contracts.mjs` valida o `quality-report.json` escrito em Python |
| `provenance-contract-v1` na lane `consumer-ready` | `0efcfd4c` — `consumerPull` `provenance-contract.origin-of-every-input`; packet `2026-08-30` | `insumos.json` leva a provenance de cada insumo; `verifyProvenance` aceita todas |

O que este consumidor traz de novo para o refarm: **um produtor que não é
JavaScript**. Se `quality:v1` e `artifact:v1` servem a um motor Python via
JSON, são contratos de verdade, não tipos TypeScript.

## Demandas que devem virar release

| Prioridade | Dono | Bloco esperado | Prova que o arch-engine fornece |
|---|---|---|---|
| P0 | refarm | release npm de `quality-contract-v1`, `artifact-contract-v1` e `provenance-contract-v1` — agora a unidade `evidence-contracts-ready` (refarm `e8ac2f86`), fechada em dependências, com install smoke 3/3 e first-publish idempotente; falta só a promoção `develop → main` e o dispatch da lane pelo dono do repo | `scripts/test_refarm_contracts.mjs` passa; o job `refarm-proof` deixa de ser manual e vira `npm ci` |
| P0 | refarm | JSON Schema publicado ao lado de cada `types.ts` (ou gerado deles) | `contracts.py` encolhe para `jsonschema.validate`; fim do espelho manual |
| P1 | refarm | `vendor_refarm` como comando do refarm (`refarm handoff vendor`) | é a terceira cópia do script (coop-vault, enem, arch-engine) |
| P2 | refarm | `ds` + `local-surface` para uma landing page estática que renderize `relatorio.md` e `manifest.json` | página do exemplo publicada em GitHub Pages sem CSS próprio |
| P2 | refarm | `records-contract-v1` (YAML-LD) para `materiais.yaml` como registros com relações insumo → fonte | DB de materiais navegável em um vault-seed |

## Defeitos e atritos observados

- ~~`provenance-contract-v1` não está no packet de handoff~~ — resolvido em `0efcfd4c`.
- ~~Falta um `validateQualityReport(report)` puro~~ — resolvido em `aaa3b6cc`.
- ~~`TASK_ARTIFACT_MANIFEST_SCHEMA` declarado duas vezes no refarm (`refarm.` × `sovereign.`)~~ —
  ISS-112 fechada em `46e76097`: o valor do pacote (`sovereign.task-artifacts.v1`, o que este
  consumidor já emitia) é o canônico.
- `TaskArtifactReference.role` é um enum fechado (`dataset|report|…|other`):
  artefatos CAD caem todos em `other` e se distinguem só por `labels`.

## Seam local temporário

- `contracts.py` espelha três `types.ts` à mão. Quando o P0 de JSON Schema
  sair, este arquivo é o primeiro a ser reduzido.
- O job `refarm-proof` do CI clona o refarm e gera o packet — caro e frágil;
  existe só para não deixar a prova depender da máquina de uma pessoa.
