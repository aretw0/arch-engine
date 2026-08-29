#!/usr/bin/env node
// Popula vendor/ com os tarballs @refarm.dev do packet de handoff local do Refarm.
//
// Adaptado de coop-vault/scripts/vendor_refarm.mjs — a terceira cópia deste script
// no ecossistema (coop-vault, enem, arch-engine). Isso é a demanda P1 em
// docs/ECOSYSTEM-DEMANDS.md: virar um comando do próprio refarm.
//
// Enquanto o Refarm não publica em npm, quem clonar este repo precisa do checkout
// do refarm ao lado (ou REFARM_ROOT). Os tarballs NÃO são versionados: nome e
// versão ficam estáveis enquanto os bytes mudam entre packets (ADR-080 do refarm).

import { createHash } from "node:crypto";
import { copyFileSync, existsSync, mkdirSync, readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = fileURLToPath(new URL("..", import.meta.url));
const REFARM = process.env.REFARM_ROOT ?? join(ROOT, "..", "refarm");
const HANDOFF = join(REFARM, ".refarm/handoff/vault-seed");

if (!existsSync(HANDOFF)) {
  console.error(`Packet de handoff do Refarm não encontrado em ${HANDOFF}`);
  console.error("");
  console.error("Os contratos @refarm.dev ainda não estão publicados em npm. Enquanto isso:");
  console.error("  git clone https://github.com/aretw0/refarm ../refarm");
  console.error("  (cd ../refarm && pnpm install && pnpm run release:vault-seed:handoff)");
  console.error("Ou aponte REFARM_ROOT para onde o refarm estiver.");
  process.exit(2);
}

const packets = readdirSync(HANDOFF).filter((d) => /^\d{4}-\d{2}-\d{2}$/.test(d)).sort();
const packet = join(HANDOFF, packets.at(-1));
const manifestPath = join(packet, "manifest.json");
if (!existsSync(manifestPath)) {
  console.error(`Packet sem manifest.json: ${packet} — um diretório sem manifest não é um packet.`);
  process.exit(2);
}
const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
const noPacket = [...manifest.packages, ...(manifest.consumerInstall?.transitivePackages ?? [])];

// O que vendorizar sai do package.json, não de uma lista paralela.
const pkg = JSON.parse(readFileSync(join(ROOT, "package.json"), "utf8"));
const wanted = Object.entries(pkg.dependencies ?? {})
  .filter(([name, spec]) => name.startsWith("@refarm.dev/") && String(spec).startsWith("file:vendor/"))
  .map(([name]) => name);

mkdirSync(join(ROOT, "vendor"), { recursive: true });
let problemas = 0;
for (const name of wanted) {
  const entry = noPacket.find((p) => p.packageName === name);
  if (!entry) {
    console.error(`ausente no packet ${packets.at(-1)}: ${name}`);
    problemas += 1;
    continue;
  }
  const destino = join(ROOT, "vendor", entry.tarball);
  copyFileSync(join(packet, entry.tarball), destino);
  const sha = createHash("sha256").update(readFileSync(destino)).digest("hex");
  if (sha !== entry.sha256) {
    console.error(`sha256 diverge do manifest: ${entry.tarball}`);
    problemas += 1;
    continue;
  }
  console.log(`  ${entry.tarball}  ${sha.slice(0, 12)}`);
}
console.log(`packet ${packets.at(-1)} (refarm ${String(manifest.sourceGitSha).slice(0, 12)})`);
if (problemas) process.exit(1);
console.log("agora: npm install --no-package-lock && npm run test:refarm");
