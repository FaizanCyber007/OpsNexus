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


if __name__ == "__main__":
    mcp.run()
