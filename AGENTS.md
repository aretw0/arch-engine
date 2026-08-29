# Regras para agentes e contribuidores

1. **Fonte é texto; artefato é derivado.** Nunca edite `artifacts/`, `cad/render/`,
   `cad/gen/` ou qualquer `.sh3d`/`.obj`. Corrija o YAML, o `.scad` ou o `Home.xml`.
2. **Core não conhece domínio.** Nada em `core/` diz "casa", "terreno" ou nomes de
   materiais. Domínio vive em `examples/<caso>/`. Estender = registrar em
   `compiler.BASES` / `validator.CHECKS`, com teste em `tests/`.
3. **Decisão técnica vira ADR** em `docs/adr/`, com fonte verificável em
   `docs/references.md`. Necessidade genérica vira linha em `docs/ECOSYSTEM-DEMANDS.md`,
   não código privado aqui.
4. **Commits atômicos em pt-BR**, `tipo(escopo): frase no imperativo`
   (`.gitmessage`). Sem trailers de coautoria.
5. **Antes de dizer que está pronto:** `uv run ruff check core tests && uv run pytest -q`.
   Para o fluxo completo local: `scripts/cli_runner.sh all`.
6. **Ecossistema:** `refarm` é SDK (contratos), `vault-seed`/`coop-vault`/`enem` são
   pares. Consuma o que estiver maduro; registre o que faltar como demanda.
