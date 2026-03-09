from __future__ import annotations

from .schema_core import APIModel


class AgentCapability(APIModel):
    id: str
    label: str
    description: str
    read_only: bool = True
    route: str
    entity: str


class AgentContext(APIModel):
    mode: str
    account_mode: str
    available_capabilities: list[str]
    capabilities: list[AgentCapability]
    domain_vocabulary: list[str]
    resources: dict[str, str]
