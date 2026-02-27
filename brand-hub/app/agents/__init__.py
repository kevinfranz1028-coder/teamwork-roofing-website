"""
Brand Intelligence Content Hub - Agent Module

Provides the multi-agent orchestration pipeline:
- ResearchAgent: retrieval pipeline for brand knowledge
- ContentBrief: structured research output
- ComplianceAgent: brand validation
- OrchestratorAgent: request decomposition into TaskPlans
- WriterAgent: structured content generation
- DesignerAgent: final file assembly via existing generators
- AgentRouter: step-by-step plan execution with retry loop
- VisualAgent: intelligent visual routing (Napkin / DALL-E / Pexels)
"""

from app.agents.task_plan import (
    AgentType,
    ContentBrief,
    TaskPlan,
    TaskStatus,
    TaskStep,
)
from app.agents.research_agent import ResearchAgent
from app.agents.compliance_agent import ComplianceAgent
from app.agents.orchestrator import OrchestratorAgent
from app.agents.writer_agent import WriterAgent
from app.agents.designer_agent import DesignerAgent
from app.agents.agent_router import AgentRouter
from app.agents.visual_agent import VisualAgent

__all__ = [
    "AgentType",
    "ContentBrief",
    "TaskPlan",
    "TaskStatus",
    "TaskStep",
    "ResearchAgent",
    "ComplianceAgent",
    "OrchestratorAgent",
    "WriterAgent",
    "DesignerAgent",
    "AgentRouter",
    "VisualAgent",
]
