"""Pydantic schemas enforced on LLM output via LangGraph's structured-output
support (`with_structured_output` / `create_react_agent(response_format=...)`).
"""

from typing import Literal

from pydantic import BaseModel, Field

ROUTES = Literal[
    "sales_rfp", "invoice_reconciliation", "compliance_audit", "general_intake"
]


class ClassificationResult(BaseModel):
    route: ROUTES
    reasoning: str = Field(
        description="One or two sentences explaining the classification"
    )


class StructuredAnswer(BaseModel):
    content: str = Field(description="The synthesized draft response")
    executive_summary: str = Field(
        description="A concise, board-ready TL;DR of the answer"
    )
    risk_flags: list[str] = Field(
        description=(
            'Concrete risks identified, e.g. "High Churn Risk", '
            '"Missing SOC2 Policy"'
        )
    )
    action_items: list[str] = Field(
        description='Concrete next steps, e.g. "Email CFO", "Request updated invoice"'
    )
    confidence_score: float = Field(ge=0.0, le=1.0)
