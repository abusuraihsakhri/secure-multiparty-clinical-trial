"""
FastAPI REST API Server for MPC-TrialSync: Multi-Hospital Yao Garbled Circuit Kaplan-Meier Survival Agent.
"""
from typing import Dict, Any
from .models import FrontierPayload
from .agents import MPCTrialCoordinator

coordinator = MPCTrialCoordinator()


def create_app():
    try:
        from fastapi import FastAPI
        from pydantic import BaseModel, Field

        app = FastAPI(
            title="MPC-TrialSync: Multi-Hospital Yao Garbled Circuit Kaplan-Meier Survival Agent",
            description="Legacy rule-based threshold demonstration. Does not perform cryptographic MPC or survival analysis; aggregate-only survival analysis is available in mpc_clinical_trial.survival.",
            version="2.0.1-demo",
        )

        class TaskRequest(BaseModel):
            task_id: str = "TASK-2026-001"
            target_identifier: str = "TARGET-BIO-KEY"
            primary_metric: float = Field(default=28.5, allow_inf_nan=False)
            secondary_metric: float = Field(default=14.2, allow_inf_nan=False)
            status_descriptor: str = "DISCORDANT_ANOMALY"
            is_critical_flag: bool = True
            attributes: Dict[str, Any] = {}

        class ChatRequest(BaseModel):
            query: str

        @app.get("/health")
        def health():
            return {"status": "HEALTHY", "system": "secure-multiparty-clinical-trial", "domain": "Privacy-Preserving Federated Healthcare & FHE", "version": "2.0.0-FRONTIER"}

        @app.post("/api/audit")
        def api_audit(req: TaskRequest):
            payload = FrontierPayload(
                task_id=req.task_id,
                target_identifier=req.target_identifier,
                primary_metric=req.primary_metric,
                secondary_metric=req.secondary_metric,
                status_descriptor=req.status_descriptor,
                is_critical_flag=req.is_critical_flag,
                attributes=req.attributes,
            )
            return coordinator.process(payload)

        @app.post("/api/chat")
        def api_chat(req: ChatRequest):
            return {"response": coordinator.query_supervisory_chat(req.query)}

        return app
    except ImportError:
        return None
