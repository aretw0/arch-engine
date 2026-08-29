"""Envelopes dos contratos do refarm, emitidos nativamente em Python.

Espelham as formas de `@refarm.dev/quality-contract-v1`,
`@refarm.dev/artifact-contract-v1` e `@refarm.dev/provenance-contract-v1`.
Os contratos são *formas* (JSON + validador), não bibliotecas: um produtor
em outra linguagem pode cumpri-los, e a prova de conformidade roda em Node
contra o tarball real (`scripts/test_refarm_contracts.mjs`).

Mantido em sincronia manualmente com os `types.ts` do refarm — se o refarm
publicar JSON Schema, esta é a primeira coisa a ser substituída.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# --- quality:v1 ------------------------------------------------------------------

QUALITY_CAPABILITY = "quality:v1"


def count_findings(findings: list[dict[str, Any]]) -> dict[str, int]:
    contagem: dict[str, int] = {}
    for f in findings:
        contagem[f["severity"]] = contagem.get(f["severity"], 0) + 1
    return contagem


def quality_report(
    *,
    checker_id: str,
    domain: str,
    profile_name: str,
    findings: list[dict[str, Any]],
    metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    relatorio: dict[str, Any] = {
        "capability": QUALITY_CAPABILITY,
        "checkerId": checker_id,
        "domain": domain,
        "profileName": profile_name,
        "findings": findings,
        "counts": count_findings(findings),
    }
    if metrics is not None:
        relatorio["metrics"] = metrics
    return relatorio


# --- provenance:v1 -----------------------------------------------------------------

_HEX_SHA256 = re.compile(r"^[a-f0-9]{64}$")


@dataclass(frozen=True)
class ProvenanceVerification:
    valid: bool
    failures: tuple[str, ...]
    checks: dict[str, bool] = field(default_factory=dict)


def verify_provenance(prov: dict[str, Any] | None) -> ProvenanceVerification:
    """`channel` é obrigatório; formas só são checadas quando o campo existe;
    "tem origem" é aviso brando (não invalida)."""
    if not isinstance(prov, dict):
        return ProvenanceVerification(False, ("has-channel",), {"has-channel": False})
    checks: dict[str, bool] = {}
    failures: list[str] = []

    checks["has-channel"] = isinstance(prov.get("channel"), str) and bool(prov["channel"].strip())
    if not checks["has-channel"]:
        failures.append("has-channel")

    if "collectedAt" in prov:
        checks["collected-at-valid"] = _iso_valido(prov["collectedAt"])
        if not checks["collected-at-valid"]:
            failures.append("collected-at-valid")

    if "contentSha256" in prov:
        checks["sha256-shape"] = isinstance(prov["contentSha256"], str) and bool(
            _HEX_SHA256.match(prov["contentSha256"])
        )
        if not checks["sha256-shape"]:
            failures.append("sha256-shape")

    checks["not-empty-origin"] = any(
        prov.get(k) for k in ("sourceFile", "sourcePath", "originLink")
    )
    return ProvenanceVerification(not failures, tuple(failures), checks)


def _iso_valido(valor: Any) -> bool:
    if not isinstance(valor, str):
        return False
    try:
        datetime.fromisoformat(valor.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


# --- artifact:v1 -------------------------------------------------------------------

TASK_ARTIFACT_MANIFEST_SCHEMA = "sovereign.task-artifacts.v1"
TASK_ARTIFACT_ROLES = ("dataset", "report", "audit-trail", "receipt", "log", "manifest", "other")
ARTIFACT_REVIEW_STATES = ("unreviewed", "accepted", "rejected", "superseded")


def sha256_file(caminho: Path) -> str:
    h = hashlib.sha256()
    with caminho.open("rb") as f:
        for bloco in iter(lambda: f.read(1 << 16), b""):
            h.update(bloco)
    return h.hexdigest()


def artifact_hash(caminho: Path) -> dict[str, str]:
    return {"algorithm": "sha256", "value": sha256_file(caminho)}


def _sem_nulos(d: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}


def artifact_provenance(
    *,
    run_id: str,
    producer: str,
    produced_at: str,
    command: str | None = None,
    process: dict[str, Any] | None = None,
    source: str | None = None,
    source_version: str | None = None,
    input_hashes: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    return _sem_nulos(
        {
            "runId": run_id,
            "producer": producer,
            "producedAt": produced_at,
            "command": command,
            "process": process,
            "source": source,
            "sourceVersion": source_version,
            "inputHashes": input_hashes,
        }
    )


def artifact_reference(
    *,
    id: str,
    uri: str,
    media_type: str,
    role: str,
    provenance: dict[str, Any],
    hash: dict[str, str] | None = None,
    labels: list[str] | None = None,
    review_state: str | None = None,
) -> dict[str, Any]:
    return _sem_nulos(
        {
            "id": id,
            "uri": uri,
            "mediaType": media_type,
            "role": role,
            "hash": hash,
            "reviewState": review_state,
            "provenance": provenance,
            "labels": labels,
        }
    )


def task_artifact_manifest(
    *,
    artifacts: list[dict[str, Any]],
    created_at: str,
    task_id: str | None = None,
    effort_id: str | None = None,
) -> dict[str, Any]:
    return _sem_nulos(
        {
            "schema": TASK_ARTIFACT_MANIFEST_SCHEMA,
            "taskId": task_id,
            "effortId": effort_id,
            "createdAt": created_at,
            "artifacts": artifacts,
        }
    )


def validate_task_artifact_manifest(manifest: Any) -> list[str]:
    """Espelho reduzido de `validateTaskArtifactManifest`: devolve caminhos com defeito.

    A validação canônica é a do refarm em Node; esta existe para o `build`
    falhar cedo, antes de produzir um manifest que a prova rejeitaria.
    """
    issues: list[str] = []
    if not isinstance(manifest, dict):
        return ["$"]
    if manifest.get("schema") != TASK_ARTIFACT_MANIFEST_SCHEMA:
        issues.append("$.schema")
    if not _texto(manifest.get("createdAt")):
        issues.append("$.createdAt")
    artefatos = manifest.get("artifacts")
    if not isinstance(artefatos, list):
        return [*issues, "$.artifacts"]
    ids: set[str] = set()
    for i, a in enumerate(artefatos):
        p = f"$.artifacts.{i}"
        if not isinstance(a, dict):
            issues.append(p)
            continue
        for campo in ("id", "uri", "mediaType"):
            if not _texto(a.get(campo)):
                issues.append(f"{p}.{campo}")
        if a.get("role") not in TASK_ARTIFACT_ROLES:
            issues.append(f"{p}.role")
        if "hash" in a and not (
            isinstance(a["hash"], dict)
            and a["hash"].get("algorithm") == "sha256"
            and _HEX_SHA256.match(str(a["hash"].get("value", "")))
        ):
            issues.append(f"{p}.hash")
        if "reviewState" in a and a["reviewState"] not in ARTIFACT_REVIEW_STATES:
            issues.append(f"{p}.reviewState")
        prov = a.get("provenance")
        if not isinstance(prov, dict):
            issues.append(f"{p}.provenance")
        else:
            for campo in ("runId", "producer", "producedAt"):
                if not _texto(prov.get(campo)):
                    issues.append(f"{p}.provenance.{campo}")
            proc = prov.get("process")
            if (
                proc is not None
                and _texto(prov.get("command"))
                and prov["command"] != proc.get("display")
            ):
                issues.append(f"{p}.provenance.command")
        if _texto(a.get("id")):
            if a["id"] in ids:
                issues.append(f"{p}.id")
            ids.add(a["id"])
    return issues


def _texto(v: Any) -> bool:
    return isinstance(v, str) and len(v) > 0
