from pathlib import Path

from arch_engine.contracts import (
    artifact_hash,
    artifact_provenance,
    artifact_reference,
    count_findings,
    quality_report,
    task_artifact_manifest,
    validate_task_artifact_manifest,
    verify_provenance,
)


def test_count_findings_agrupa_por_severidade():
    findings = [{"severity": "fail"}, {"severity": "warn"}, {"severity": "fail"}]
    assert count_findings(findings) == {"fail": 2, "warn": 1}


def test_quality_report_tem_o_envelope_do_refarm():
    r = quality_report(checker_id="c", domain="d", profile_name="p", findings=[], metrics={"x": 1})
    assert r == {
        "capability": "quality:v1",
        "checkerId": "c",
        "domain": "d",
        "profileName": "p",
        "findings": [],
        "counts": {},
        "metrics": {"x": 1},
    }


def test_verify_provenance_exige_channel_e_checa_formas_so_quando_presentes():
    assert not verify_provenance(None).valid
    assert not verify_provenance({"originLink": "https://x"}).valid
    ok = verify_provenance({"channel": "literature"})
    assert ok.valid and ok.checks["not-empty-origin"] is False  # brando: não invalida
    ruim = verify_provenance({"channel": "web", "collectedAt": "ontem", "contentSha256": "zz"})
    assert ruim.failures == ("collected-at-valid", "sha256-shape")
    bom = verify_provenance(
        {"channel": "web", "collectedAt": "2026-08-29T00:00:00Z", "contentSha256": "a" * 64}
    )
    assert bom.valid


def test_manifest_valido_passa_no_espelho_do_validador(tmp_path: Path):
    arquivo = tmp_path / "relatorio.md"
    arquivo.write_text("# oi\n", encoding="utf-8")
    prov = artifact_provenance(
        run_id="run-1",
        producer="arch-engine",
        produced_at="2026-08-29T00:00:00Z",
        command="arch-engine build",
        process={"command": "arch-engine", "args": ["build"], "display": "arch-engine build"},
    )
    manifest = task_artifact_manifest(
        task_id="demo",
        created_at="2026-08-29T00:00:00Z",
        artifacts=[
            artifact_reference(
                id="relatorio",
                uri="artifacts/relatorio.md",
                media_type="text/markdown",
                role="report",
                hash=artifact_hash(arquivo),
                provenance=prov,
                labels=["orcamento"],
            )
        ],
    )
    assert validate_task_artifact_manifest(manifest) == []
    assert len(manifest["artifacts"][0]["hash"]["value"]) == 64
    assert "effortId" not in manifest  # None nunca vira null no JSON


def test_manifest_invalido_lista_os_caminhos():
    prov = {
        "runId": "r",
        "producer": "p",
        "producedAt": "t",
        "command": "a",
        "process": {"display": "b"},
    }
    ruim = {
        "schema": "errado",
        "createdAt": "",
        "artifacts": [
            {"id": "x", "uri": "u", "mediaType": "m", "role": "poema", "provenance": prov},
            {"id": "x", "uri": "u", "mediaType": "m", "role": "report", "provenance": {}},
        ],
    }
    issues = validate_task_artifact_manifest(ruim)
    assert "$.schema" in issues
    assert "$.createdAt" in issues
    assert "$.artifacts.0.role" in issues
    assert "$.artifacts.0.provenance.command" in issues  # command ≠ process.display
    assert "$.artifacts.1.provenance.runId" in issues
    assert "$.artifacts.1.id" in issues  # duplicado
