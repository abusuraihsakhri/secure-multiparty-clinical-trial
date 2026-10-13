"""Security, API, and CSV regression checks."""
import csv

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from agents.base import AuditTrail, SecurityException
from agents.api import app
from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor
from cli import main as legacy_main


def test_hmac_detects_same_chain_entry_tampering():
    trail = AuditTrail("x" * 32)
    trail.log("supervisor", "worker", "TASK", {"status": "OK"})
    assert trail.verify_integrity()
    trail.logs[0]["actor"] = "attacker"
    assert not trail.verify_integrity()


def test_exposed_trail_is_copy():
    trail = AuditTrail("x" * 32)
    trail.log("a", "b", "c", {})
    trail.get_trail()[0]["actor"] = "malicious"
    assert trail.verify_integrity()


def test_phi_in_nested_attributes_rejected():
    payload = SystemTaskPayload(task_id="TEST", target_identifier="SYN-1", primary_metric=1,
                                attributes={"notes": {"patient": "MRN-123456"}})
    with pytest.raises(SecurityException):
        SystemSupervisor().process_task(payload)


def test_nonfinite_numeric_values_rejected():
    with pytest.raises(ValidationError):
        SystemTaskPayload(task_id="T", target_identifier="S", primary_metric=float("nan"))


def test_csv_false_not_treated_as_true(tmp_path):
    source = tmp_path / "input.csv"
    dest = tmp_path / "output.csv"
    source.write_text("task_id,target_identifier,primary_metric,secondary_metric,is_critical_flag,status_descriptor\nT,S,5,4,False,NOMINAL\n")
    assert legacy_main(["batch", "-i", str(source), "-o", str(dest)]) == 0
    with dest.open() as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["overall_urgency"] == "ROUTINE"


def test_api_metric_format_and_invalid_phi():
    with TestClient(app) as client:
        ok = client.post("/api/audit", json={
            "task_id": "TEST", "target_identifier": "SYN-01",
            "primary_metric": 2.0, "secondary_metric": 1.0,
        })
        assert ok.status_code == 200
        metrics = client.get("/metrics")
        assert metrics.status_code == 200
        assert "text/plain" in metrics.headers["content-type"]
        assert "system_tasks_total" in metrics.text
        rejected = client.post("/api/audit", json={
            "task_id": "TEST", "target_identifier": "MRN-123456",
            "primary_metric": 2.0
        })
        assert rejected.status_code == 422
