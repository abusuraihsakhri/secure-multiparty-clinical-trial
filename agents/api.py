"""
FastAPI REST API Server for Secure Multiparty Clinical Trial.
"""
from typing import Dict, Any, List
import time
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from .base import AuditLogger, PHIGuard, SecurityException
from .metrics import GLOBAL_METRICS
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Secure Multiparty Clinical Trial API",
    description="Local rule-based demonstration API; not a clinical or MPC service",
    version="3.0.0-ENTERPRISE",
)


class ChatRequest(BaseModel):
    query: str


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "secure-multiparty-clinical-trial", "domain": "Clinical & Biomedical AI", "standard": "demonstration thresholds only", "version": "3.0.1-demo"}


@app.get("/metrics", response_class=PlainTextResponse)
def metrics():
    return GLOBAL_METRICS.export_prometheus_text()


@app.get("/api/metrics")
def metrics_json():
    return {
        "dossiers_processed_total": GLOBAL_METRICS.tasks_total,
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "RUNNING",
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    started = time.perf_counter()
    try:
        dossier = supervisor.process_task(payload)
    except SecurityException:
        GLOBAL_METRICS.record_phi_block()
        raise HTTPException(status_code=422, detail="Sensitive identifier pattern detected")
    GLOBAL_METRICS.record_task(dossier.overall_urgency.value, time.perf_counter() - started)
    return dossier.to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except SecurityException:
        GLOBAL_METRICS.record_phi_block()
        raise HTTPException(status_code=422, detail="Sensitive identifier pattern detected")


@app.get("/api/audit/logs")
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}
