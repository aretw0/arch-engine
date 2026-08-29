# ADR-006 · Todo insumo carrega `provenance`; ICE v2.0 como fonte inicial

**Status:** aceita · **Data:** 2026-08-29

## Contexto

Um DB de materiais com "pegada de carbono" e "classe de COV" sem dizer de
onde vieram os números é opinião com casas decimais. A demo precisava de
valores plausíveis *e* rastreáveis; a regra `material.provenance` precisava
de algo para verificar.

## Decisão

1. Cada material pode (e a demo deve) carregar `provenance` no formato de
   `provenance:v1` do refarm: `channel` obrigatório, `originLink`,
   `collectedAt`, `license`. O validador aplica `verify_provenance`.
2. Carbono incorporado: **ICE v2.0** (Hammond & Jones, Univ. of Bath, 2011),
   tabelas-resumo públicas. Valores por kg × densidade assumida, com a conta
   em `notas`. É uma base britânica de 2011 — **ilustrativa**; troque por EPDs
   nacionais quando houver.
3. Classe de COV: a chave chama-se `vif` porque a especificação inicial a
   nomeou assim (regra "`vif: Alto` bloqueia"). Semântica: classe de emissão
   de COV inspirada no rótulo francês *Émissions dans l'air intérieur*
   (A+/A/B/C, ISO 16000-9 / EN 16516), mapeada para Isento/Baixo/Médio/Alto.
   Renomear para `cov` é uma troca de chave em dois arquivos.
4. Preços são ilustrativos (BRL, 2026) e dizem isso no YAML.

## Consequências

- O relatório imprime a fonte de cada insumo (coluna *Fonte*).
- Um material novo sem `provenance` gera `warn` na demo; um perfil mais
  rígido pode subir para `fail`.

## Referências

- ICE v2.0 Summary Tables: <https://kps.fsv.cvut.cz/upload/files/icev2.0summarytables.pdf>
  (valores usados: Lime General 0,78; Soil Rammed 0,024; Sawn Softwood
  0,20 fóssil + 0,39 biogênico; Clay General 0,24; Paint Waterborne 2,54 /
  Solventborne 3,76; Concrete RC 25/30 0,140 kgCO₂e/kg)
- Rótulo francês de COV: <https://www.iaqip.wki.fraunhofer.de/en/data_and_facts/assessment_emissions_iaq/assessment_building_product_emission/french_regulation.html>
- `refarm/packages/provenance-contract-v1/README.md`
