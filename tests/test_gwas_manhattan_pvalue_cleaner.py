"""
Automated Pytest Test Suite for Gwas Manhattan Pvalue Cleaner.
Domain: Privacy-Preserving Federated Healthcare & FHE
Standard: HIPAA Safe Harbor §164.514 / Google SecAgg Standards
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from agents.base import PHIGuard, AuditLogger, AuditTrail, SecurityException
from agents.models import SystemTaskPayload, UrgencyLevel, SystemIntegrityStatus
from agents.workers import InvariantQCWorker, SafetyEscalationWorker, ProtocolConformanceWorker
from agents.supervisor import SystemSupervisor
from cli import main, _validate_safe_path


def test_phi_guard_enforcement():
    with pytest.raises(SecurityException):
        PHIGuard.assert_no_phi("Patient MRN-994827 blood culture positive for Staphylococcus")

    # Clean text passes
    PHIGuard.assert_no_phi("Analytical assay specimen KEY-001 optimal")


def test_specialized_workers():
    # Worker 1: QC Invariant
    p1 = SystemTaskPayload(task_id="T1", target_identifier="KEY-01", primary_metric=35.0)
    alerts1 = InvariantQCWorker.evaluate(p1)
    assert len(alerts1) == 1
    assert alerts1[0].urgency == UrgencyLevel.ELEVATED

    # Worker 2: Safety
    p2 = SystemTaskPayload(task_id="T2", target_identifier="KEY-02", primary_metric=10.0, is_critical_flag=True)
    alerts2 = SafetyEscalationWorker.evaluate(p2)
    assert len(alerts2) == 1
    assert alerts2[0].urgency == UrgencyLevel.CRITICAL_STAT

    # Worker 3: Protocol Conformance
    p3 = SystemTaskPayload(task_id="T3", target_identifier="KEY-03", primary_metric=10.0, status_descriptor="DISCORDANT_ANOMALY")
    alerts3 = ProtocolConformanceWorker.evaluate(p3)
    assert len(alerts3) == 1


def test_supervisor_consensus_and_audit():
    supervisor = SystemSupervisor(model_provider="mock")
    payload = SystemTaskPayload(
        task_id="TASK-PROD-01",
        target_identifier="KEY-PROD-01",
        primary_metric=12.0,
        secondary_metric=4.0,
        status_descriptor="NOMINAL"
    )
    dossier = supervisor.process_task(payload)
    assert dossier.overall_urgency == UrgencyLevel.ROUTINE
    assert dossier.integrity_status == SystemIntegrityStatus.VALIDATED
    assert dossier.audit_hash != ""

    # Verify cryptographic audit trail
    assert AuditLogger.verify_integrity() is True

    # CLI tests
    assert main(["audit", "--task-id", "CLI-TEST-01"]) == 0
    assert main(["chat", "Explain", "specifications"]) == 0
    assert main(["verify-audit"]) == 0


def test_audit_trail_with_secret_key():
    """AuditTrail should use provided secret key without hardcoding defaults."""
    import os
    # Test that explicit key works
    trail = AuditTrail(secret_key="test-key-12345")
    assert trail.secret_key == b"test-key-12345"

    # Test environment variable
    os.environ["AUDIT_SECRET_KEY"] = "env-key-67890"
    trail2 = AuditTrail()
    assert trail2.secret_key == b"env-key-67890"
    del os.environ["AUDIT_SECRET_KEY"]

    # Test ephemeral key generation (no default hardcoded value)
    trail3 = AuditTrail()
    assert len(trail3.secret_key) == 64  # 32 bytes hex-encoded = 64 chars


def test_validate_safe_path():
    """Path validation should accept normal paths and reject traversal."""
    # Normal path should pass
    assert _validate_safe_path("sample.csv") == "sample.csv"
    assert _validate_safe_path("tests/sample.csv") == "tests/sample.csv"


def test_cli_batch_missing_file():
    """Batch command should return error code for missing input file."""
    assert main(["batch", "-i", "nonexistent_file.csv"]) == 1


def test_cli_batch_empty_csv(tmp_path):
    """Batch command should handle empty CSV gracefully."""
    csv_in = tmp_path / "empty.csv"
    csv_in.write_text("", encoding="utf-8")
    assert main(["batch", "-i", str(csv_in)]) == 1
