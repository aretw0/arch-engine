# ADR-004 · Contratos do refarm emitidos em Python, provados em Node

**Status:** aceita · **Data:** 2026-08-29

## Contexto

O `refarm` é um monorepo TypeScript com contratos versionados
(`@refarm.dev/*-contract-v1`) que os consumidores (`vault-seed`,
`coop-vault`, `enem`) adotam via tarballs de um packet de handoff local,
provam com testes de consumo e registram demandas — e é essa evidência que
destrava a release npm. O `arch-engine` é Python: importar as bibliotecas
não faz sentido, mas os **envelopes** fazem.

Candidatos avaliados (ver `refarm/packages/README.md`):

| Contrato | Uso aqui | No packet de handoff? |
|---|---|---|
| `quality-contract-v1` | o validador é um `QualityChecker`; o perfil YAML é um `QualityProfile`; a saída é um `QualityReport` | sim |
| `artifact-contract-v1` | `manifest.json` (`sovereign.task-artifacts.v1`) com hash e provenance de cada artefato | sim |
| `provenance-contract-v1` | `provenance` de cada insumo (`channel` obrigatório) | **não** (candidato) |
| `process-handoff` | forma `{command,args,display}` da provenance de processo | sim (só a forma) |
| `budget-contract-v1` | orçamento de *dispatch* (tokens/USD/prazo), não de obra | não se aplica |
| `ds`, `local-surface` | landing page (baixa prioridade) | sim, depois |

## Decisão

1. `core/arch_engine/contracts.py` espelha as formas dos três contratos, com
   um validador reduzido de `artifact:v1` para falhar cedo.
2. O `build` escreve `quality-report.json` e `manifest.json` nessas formas.
3. `scripts/test_refarm_contracts.mjs` valida os arquivos com o **código
   real** dos tarballs (`validateTaskArtifactManifest`, `countFindings`,
   `QUALITY_CAPABILITY`). Node é opcional e só existe para a prova; o core
   não depende dele.
4. `scripts/vendor_refarm.mjs` copia os tarballs do packet local (mecanismo do
   `coop-vault`), conferindo sha256. Sem lockfile: os bytes mudam entre packets.
5. As demandas ao refarm ficam em `docs/ECOSYSTEM-DEMANDS.md`, no formato do
   `enem`.

## Consequências

- O refarm ganha um consumidor **fora do Node** — evidência de que os contratos
  são formas neutras, não detalhes de implementação TypeScript.
- Manter os espelhos sincronizados com os `types.ts` é manual. Se o refarm
  publicar JSON Schema, `contracts.py` encolhe para um validador genérico.
- A prova no CI é manual (`workflow_dispatch`) até haver release npm.

## Referências

- `refarm/docs/EXTERNAL_CONSUMER_CALIBRATION.md`, `refarm/docs/RELEASE_POLICY.md`
- `coop-vault/scripts/vendor_refarm.mjs`, `coop-vault/scripts/test_*_consumer_contract.mjs`
- `enem/docs/ECOSYSTEM-DEMANDS.md`
- Tipos espelhados: `refarm/packages/{quality,artifact,provenance}-contract-v1/src/types.ts`
