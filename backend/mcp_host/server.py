"""Standalone MCP server for OpsNexus.

Runs outside the Django request/response cycle -- this process exposes
OpsNexus resources/tools to MCP-compatible clients (the Groq Sales Worker,
via `mcp_host/client.py`) over stdio.
"""

import json

from mcp.server import MCPServer

mcp = MCPServer("opsnexus-mcp-host")


@mcp.resource("opsnexus://documents/schema")
def mock_resource() -> str:
    """Placeholder resource stub."""
    return ""


@mcp.tool()
def get_internal_pricing_policy() -> str:
    """Return OpsNexus's internal pricing policy as a JSON string, for use
    when drafting RFP/questionnaire responses that ask about pricing."""
    return json.dumps(
        {
            "currency": "USD",
            "billing_cycle": "monthly, annual discount available",
            "tiers": [
                {
                    "name": "Starter",
                    "price_per_month": 499,
                    "seats_included": 5,
                    "features": [
                        "Document intake up to 200/mo",
                        "Deterministic + AI routing",
                        "Email support",
                    ],
                },
                {
                    "name": "Growth",
                    "price_per_month": 1499,
                    "seats_included": 20,
                    "features": [
                        "Document intake up to 2,000/mo",
                        "Full Supervisor/Worker AI pipeline",
                        "Semantic search over document history",
                        "Priority support, SLA 24h",
                    ],
                },
                {
                    "name": "Enterprise",
                    "price_per_month": "custom",
                    "seats_included": "unlimited",
                    "features": [
                        "Unlimited document intake",
                        "Dedicated tenancy",
                        "SOC2 compliance reporting",
                        "Dedicated success manager, SLA 4h",
                    ],
                },
            ],
        }
    )


@mcp.tool()
def get_security_policies() -> str:
    """Return OpsNexus's internal company security policies as a JSON string,
    for use when auditing log files or compliance documents against defined
    policy requirements."""
    return json.dumps(
        {
            "version": "2024-Q4",
            "policies": [
                {
                    "id": "SEC-001",
                    "category": "Access Control",
                    "policy": "All SSH access must use Multi-Factor Authentication (MFA). Password-only SSH login is prohibited.",
                    "severity_if_violated": "Critical",
                },
                {
                    "id": "SEC-002",
                    "category": "Network Security",
                    "policy": "Ports 22 (SSH) and 3389 (RDP) must be closed to the public internet. Access must be restricted to VPN or allowlisted IP ranges only.",
                    "severity_if_violated": "Critical",
                },
                {
                    "id": "SEC-003",
                    "category": "Data Protection",
                    "policy": "Logs must not contain plaintext passwords, API keys, or secrets. All sensitive values must be redacted or masked before logging.",
                    "severity_if_violated": "High",
                },
                {
                    "id": "SEC-004",
                    "category": "Encryption",
                    "policy": "All data at rest must be encrypted using AES-256 or stronger. Unencrypted storage of PII or financial data is prohibited.",
                    "severity_if_violated": "High",
                },
                {
                    "id": "SEC-005",
                    "category": "Audit Logging",
                    "policy": "All privileged actions (admin logins, configuration changes, data exports) must be captured in tamper-evident audit logs retained for at least 90 days.",
                    "severity_if_violated": "Medium",
                },
                {
                    "id": "SEC-006",
                    "category": "Vulnerability Management",
                    "policy": "Critical CVEs must be patched within 72 hours of disclosure. High CVEs within 7 days. Medium CVEs within 30 days.",
                    "severity_if_violated": "High",
                },
                {
                    "id": "SEC-007",
                    "category": "Access Control",
                    "policy": "The principle of least privilege must be enforced. Service accounts must not have admin or root-level access unless explicitly justified and approved.",
                    "severity_if_violated": "Medium",
                },
            ],
        }
    )


@mcp.tool()
def get_open_purchase_orders() -> str:
    """Return OpsNexus's internal financial ledger as a JSON string, containing
    all open purchase orders (POs) with their approved vendors, approved
    amounts, and line items. Use this tool when reconciling an incoming invoice
    against the internal ledger to detect discrepancies."""
    return json.dumps(
        {
            "ledger_version": "2024-Q4",
            "open_purchase_orders": [
                {
                    "po_number": "PO-1042",
                    "vendor_name": "Acme Corporation",
                    "vendor_id": "VND-0091",
                    "approved_amount_usd": 10000.00,
                    "currency": "USD",
                    "status": "open",
                    "issue_date": "2024-11-01",
                    "expiry_date": "2025-01-31",
                    "line_items": [
                        {
                            "description": "Cloud Infrastructure - Nov 2024",
                            "quantity": 1,
                            "unit_price_usd": 6000.00,
                        },
                        {
                            "description": "Managed Support Services - Q4",
                            "quantity": 1,
                            "unit_price_usd": 4000.00,
                        },
                    ],
                },
                {
                    "po_number": "PO-1078",
                    "vendor_name": "DataStream Analytics Ltd.",
                    "vendor_id": "VND-0204",
                    "approved_amount_usd": 25000.00,
                    "currency": "USD",
                    "status": "open",
                    "issue_date": "2024-10-15",
                    "expiry_date": "2025-03-15",
                    "line_items": [
                        {
                            "description": "Data Pipeline Licensing - Annual",
                            "quantity": 1,
                            "unit_price_usd": 20000.00,
                        },
                        {
                            "description": "Professional Services - Integration",
                            "quantity": 5,
                            "unit_price_usd": 1000.00,
                        },
                    ],
                },
                {
                    "po_number": "PO-1103",
                    "vendor_name": "SecureNet Solutions",
                    "vendor_id": "VND-0317",
                    "approved_amount_usd": 7500.00,
                    "currency": "USD",
                    "status": "open",
                    "issue_date": "2024-12-01",
                    "expiry_date": "2025-02-28",
                    "line_items": [
                        {
                            "description": "Penetration Testing Service",
                            "quantity": 1,
                            "unit_price_usd": 5000.00,
                        },
                        {
                            "description": "Vulnerability Report & Remediation Guide",
                            "quantity": 1,
                            "unit_price_usd": 2500.00,
                        },
                    ],
                },
            ],
            "approved_vendors": [
                {"vendor_id": "VND-0091", "name": "Acme Corporation"},
                {"vendor_id": "VND-0204", "name": "DataStream Analytics Ltd."},
                {"vendor_id": "VND-0317", "name": "SecureNet Solutions"},
                {"vendor_id": "VND-0412", "name": "CloudBridge Inc."},
            ],
        }
    )


if __name__ == "__main__":
    mcp.run()
