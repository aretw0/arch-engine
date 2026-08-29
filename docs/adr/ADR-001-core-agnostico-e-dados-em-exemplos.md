# ADR-001 · Core agnóstico em `core/`, domínio em `examples/`

**Status:** aceita · **Data:** 2026-08-29

## Contexto

Ferramentas de projeto costumam misturar o motor com o caso de uso: a planilha
sabe que é "uma casa", o CAD tem "parede" hardcoded. Isso impede reutilizar o
mesmo fluxo para um galpão, uma horta ou um contêiner, e torna o próprio motor
difícil de testar sem os dados de um projeto real.

## Decisão

1. `core/` só conhece **dimensões, insumos, composições e regras**. Nenhum
   módulo do core contém as palavras "casa", "terreno" ou nomes de materiais.
   As bases geométricas são um registro (`compiler.BASES`); os checks do
   validador são outro (`validator.CHECKS`). Estender = registrar, não editar.
2. `examples/<caso>/` contém tudo que é domínio: `data/*.yaml`, `cad/*.scad`,
   `cad/sh3d/Home.xml`, `engenharia/*.md`. A demo da casa ecológica é o
   **teste de aceitação** do core (`tests/test_demo_e2e.py`), não parte dele.
3. O pacote Python chama-se `arch_engine` e mora em `core/arch_engine/` — o
   nome importável é o do projeto, e o caminho no disco mostra a fronteira.
   (A árvore inicial pedia `core/engine/`; `engine` seria um nome de pacote
   genérico demais para instalar via `uv`/pip.)
4. Os testes do core usam fixtures em memória (`tests/conftest.py`), não a
   demo. Se a demo mudar, o core não quebra; se o core mudar, a demo avisa.

## Consequências

- Um novo caso de uso é uma pasta nova, sem tocar em `core/`.
- Novas bases geométricas ou checks entram como funções puras registradas — o
  custo de estender é um `dict` a mais, com teste.
- As chaves YAML ficam em pt-BR (linguagem ubíqua do domínio no Brasil:
  `orcamento_limite`, `pe_direito`), enquanto o mecanismo do core (nomes de
  módulos, contratos do refarm) fica em inglês.

## Referências

- Evans, *Domain-Driven Design* — linguagem ubíqua.
- `docs/superpowers/specs/2026-08-29-arch-engine-design.md`, §2–3.
