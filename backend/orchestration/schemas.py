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


class ComplianceAuditResult(BaseModel):
    is_compliant: bool = Field(
        description="True if the audited document has no policy violations, False otherwise"
    )
    violations: list[str] = Field(
        description=(
            "Specific policy breaches found in the document, "
            'e.g. "Port 22 exposed in server.log", '
            '"Plaintext password found in auth.log"'
        )
    )
    severity: Literal["Low", "Medium", "High", "Critical", "None"] = Field(
        description=(
            "Overall severity of the findings. Use 'None' when is_compliant is True "
            "and no violations were found."
        )
    )
    recommended_remediations: list[str] = Field(
        description=(
            "Actionable remediation steps the team should take to address each "
            "violation, e.g. \"Enforce MFA for all SSH access\", "
            '"Close port 3389 to public internet via firewall rule"'
        )
    )


class InvoiceReconciliationResult(BaseModel):
    is_matched: bool = Field(
        description=(
            "True if the invoice perfectly matches all fields in the internal "
            "purchase order ledger (vendor, amount, line items). False if any "
            "discrepancy was found."
        )
    )
    discrepancies: list[str] = Field(
        description=(
            "A list of concrete mismatches found between the invoice and the "
            "internal ledger, e.g. \"Vendor name mismatch: invoice says 'Acme "
            "Corp' but PO-1042 lists 'Acme Corporation'\", "
            "\"Total amount $12,500 exceeds PO-1042 approved limit of $10,000 "
            "by $2,500\". Empty list if is_matched is True."
        )
    )
    approved_for_payment: bool = Field(
        description=(
            "True only when is_matched is True AND the extracted total does not "
            "exceed the PO approved amount. False in all other cases."
        )
    )
    extracted_total: float = Field(
        description=(
            "The total monetary amount extracted directly from the invoice "
            "document, as a plain float (e.g. 12500.00). Use 0.0 if no amount "
            "can be parsed from the document."
        )
    )
