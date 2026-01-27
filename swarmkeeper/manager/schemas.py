"""Pydantic schemas for LLM structured outputs."""

from pydantic import BaseModel, Field


class AnalysisResult(BaseModel):
    """Schema for LLM analysis of tmux session output."""

    status: str = Field(
        description="Status of the agent: 'working' or 'stopped'",
        pattern="^(working|stopped)$",
    )
    log: str = Field(
        description="Brief description of what the agent was doing at capture time",
        max_length=100,
    )


class SessionReport(BaseModel):
    """Report for a single session analysis."""

    session_name: str
    status: str
    log: str
    timestamp: str
    is_alive: bool
