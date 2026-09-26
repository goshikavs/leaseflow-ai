from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

AgentStatus = Literal["SUCCESS", "FAILED", "SKIPPED", "TIMED_OUT", "INSUFFICIENT_EVIDENCE"]


class AgentResult(BaseModel):
    agent_name: str
    execution_id: str
    status: AgentStatus
    findings: dict[str, Any] = Field(default_factory=dict)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    source_versions: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    duration_ms: int = 0


class WorkflowState(BaseModel):
    lease_id: str
    organization_id: str
    property_id: str
    correlation_id: str
    flags: dict[str, bool]
    results: list[AgentResult] = Field(default_factory=list)
    policy: dict[str, Any] | None = None
