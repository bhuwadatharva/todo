"""
Data Models for the Autonomous Agent.
Built using Pydantic for robust request validation and structured agent output.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class AgentRequest(BaseModel):
    """Incoming user request for the autonomous agent."""
    request: str = Field(
        ...,
        description="The natural language prompt or project specification.",
        examples=[
            "Create a Q3 Marketing Strategy Plan for an AI SaaS startup launching an automated code review tool with a $20,000 budget and a 3-month timeline."
        ]
    )

    @field_validator("request")
    @classmethod
    def validate_request_content(cls, value: str) -> str:
        clean = value.strip()
        if len(clean) < 5:
            raise ValueError("Request is too short. Please provide at least 5 characters.")
        if len(clean) > 5000:
            raise ValueError("Request exceeds maximum allowed length of 5000 characters.")
        return clean


class TaskItem(BaseModel):
    """A single discrete step in the agent's generated TODO list."""
    id: int = Field(..., description="1-indexed sequence number of the task")
    title: str = Field(..., description="Short title describing the task")
    description: str = Field(..., description="Detailed instructions for task execution")
    target_section: str = Field(
        ...,
        description="The document section this task produces (e.g., 'Executive Summary', 'Market Analysis')"
    )
    status: str = Field(default="pending", description="'pending', 'in_progress', 'completed', or 'failed'")
    output_summary: Optional[str] = Field(default=None, description="Brief summary of execution results")


class Plan(BaseModel):
    """Structured plan produced by the LLM Planner."""
    title: str = Field(..., description="Formal title for the generated document")
    subtitle: str = Field(..., description="Short explanatory subtitle")
    assumptions: List[str] = Field(
        default_factory=list,
        description="Assumptions or heuristics identified to resolve ambiguities or missing data"
    )
    tasks: List[TaskItem] = Field(
        ...,
        description="Ordered list of sequential tasks to execute"
    )


class SectionContent(BaseModel):
    """The drafted content for a single document section."""
    section_title: str
    paragraphs: List[str]
    bullet_points: List[str] = Field(default_factory=list)
    table_headers: Optional[List[str]] = None
    table_rows: Optional[List[List[str]]] = None


class SelfCheckResult(BaseModel):
    """Results of the reflection/self-check engineering validation."""
    passed: bool
    file_exists: bool
    file_size_bytes: int
    sections_found: List[str]
    missing_sections: List[str] = Field(default_factory=list)
    repair_attempted: bool = False
    details: str


class AgentResponse(BaseModel):
    """Final JSON response returned by POST /agent."""
    status: str = Field(..., description="'success' or 'failed'")
    request: str
    document_title: str
    assumptions: List[str]
    tasks: List[TaskItem]
    document_path: str
    download_url: str
    self_check: SelfCheckResult
    execution_time_seconds: float
    llm_provider: str
    error: Optional[str] = None
