#!/usr/bin/env node
// Prova de consumo dos contratos do refarm por um produtor que NÃO é JavaScript.
//
// O arch-engine emite `quality-report.json` (quality:v1) e `manifest.json`
// (artifact:v1) em Python. Este script valida esses arquivos com o código real
// dos pacotes @refarm.dev — é a evidência de que os contratos são formas, não
// bibliotecas, e de que servem a consumidores fora do ecossistema Node.
//
// Pré-requisitos: `npm run vendor:refarm && npm install --no-package-lock` e
// `uv run arch-engine build examples/eco-house-demo`.

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import {
  TASK_ARTIFACT_MANIFEST_SCHEMA,
  isTaskArtifactManifest,
  selectTaskArtifacts,
  validateTaskArtifactManifest,
} from "@refarm.dev/artifact-contract-v1";
import { QUALITY_CAPABILITY, countFindings } from "@refarm.dev/quality-contract-v1";

const ROOT = fileURLToPath(new URL("..", import.meta.url));
const INSTANCIA = process.argv[2] ?? "examples/eco-house-demo";
const ler = (rel) => JSON.parse(readFileSync(join(ROOT, INSTANCIA, rel), "utf8"));

// --- artifact:v1 -------------------------------------------------------------
const manifest = ler("artifacts/manifest.json");
const validacao = validateTaskArtifactManifest(manifest);
assert.deepEqual(validacao.issues, [], `manifest inválido: ${JSON.stringify(validacao.issues)}`);
assert.ok(isTaskArtifactManifest(manifest));
assert.equal(manifest.schema, TASK_ARTIFACT_MANIFEST_SCHEMA);
const relatorios = selectTaskArtifacts(manifest, { roles: ["report"] });
assert.equal(relatorios.length, 1, "o build produz exatamente um relatório");
assert.equal(relatorios[0].uri, "artifacts/relatorio.md");
assert.ok(manifest.artifacts.every((a) => a.provenance.producer.startsWith("arch-engine@")));
assert.ok(manifest.artifacts.every((a) => a.provenance.inputHashes.length >= 3), "hashes das fontes YAML");

// --- quality:v1 --------------------------------------------------------------
const qualidade = ler("artifacts/quality-report.json");
assert.equal(qualidade.capability, QUALITY_CAPABILITY);
assert.ok(qualidade.checkerId && qualidade.domain && qualidade.profileName);
assert.deepEqual(qualidade.counts, countFindings(qualidade.findings), "counts = countFindings(findings)");
for (const f of qualidade.findings) {
  assert.equal(typeof f.severity, "string");
  assert.equal(typeof f.ruleId, "string");
  assert.equal(typeof f.message, "string");
}

console.log(
  `refarm contracts: ok — ${manifest.artifacts.length} artefatos (artifact:v1), ` +
    `${qualidade.findings.length} achados (quality:v1) em ${INSTANCIA}`,
);
