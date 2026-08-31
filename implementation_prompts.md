# OpsNexus: Missing Worker Agent Implementation Prompts

The following prompts are designed to be copied and pasted into an AI assistant (like Claude, Gemini, or ChatGPT) to seamlessly implement the missing worker agents into the OpsNexus LangGraph pipeline.

---

## 1. Prompt to Implement the Compliance Auditor Agent

**Copy & Paste the following:**

```text
[SYSTEM CONTEXT]
You are a Staff Software Architect working on the OpsNexus Django/LangGraph platform. 
Currently, the `graph.py` only implements the `sales_worker_node` for the `sales_rfp` route. The `compliance_audit` route correctly classifies, but falls back to a deterministic mock pipeline.

[YOUR TASK]
Implement the Compliance Auditor Sub-Agent by following these sequential steps. Ensure strict adherence to our Pydantic auto-correction loops and MCP tool patterns.

1. **Update Schemas (`backend/orchestration/schemas.py`)**
   - Create a new Pydantic schema named `ComplianceAuditResult`.
   - Fields: 
     - `is_compliant`: boolean
     - `violations`: list of strings detailing specific policy breaches (e.g., "Port 22 exposed in server.log").
     - `severity`: Literal["Low", "Medium", "High", "Critical", "None"]
     - `recommended_remediations`: list of actionable remediation steps.

2. **Add MCP Security Tool (`backend/mcp_host/server.py`)**
   - Create a new `@mcp.tool()` named `get_security_policies()`.
   - Have it return a JSON string mocking internal company policies (e.g., "All SSH access must use MFA", "Ports 22 and 3389 must be closed to the public internet", "Logs must not contain plaintext passwords").

3. **Implement Compliance Worker Node (`backend/orchestration/graph.py`)**
   - Define a new system prompt `COMPLIANCE_WORKER_SYSTEM_PROMPT`. Instruct the agent to read the uploaded `.log` or `.pdf` audit file, use the MCP tool to fetch security policies, and strictly cross-reference them to find violations.
   - Create a new async function `_run_compliance_worker_agent(...)` mirroring `_run_sales_worker_agent`. Use `create_react_agent` with the `ComplianceAuditResult` response format and the `MAX_VALIDATION_LOOPS` auto-correction logic.
   - Create the node `compliance_worker_node(state: GraphState)`. Wrap the tool setup in an `AsyncExitStack` (just like the sales worker) to safely connect to the MCP server and grab the `get_security_policies` tool. 

4. **Update Graph Routing (`backend/orchestration/graph.py`)**
   - Add the node to the graph: `workflow.add_node("compliance_worker", compliance_worker_node)`
   - Update `_route_after_supervisor` to return `"compliance_worker"` when `state["route"] == "compliance_audit"`.
   - Update `workflow.add_conditional_edges` to include the `"compliance_worker"` map.
   - Add the edge: `workflow.add_edge("compliance_worker", END)`.

5. **Update Agent Runner (`backend/orchestration/agent_runner.py`)**
   - In `trigger_agent_run`, handle the specific output mapping for the `compliance_audit` route. 
   - Extract the `ComplianceAuditResult` from the graph output, format it into a comprehensive string, and save it to the `Answer` model so the Next.js frontend can display the violations and remediations on the dashboard.
```

---

## 2. Prompt to Implement the Invoice Reconciliation Agent

**Copy & Paste the following:**

```text
[SYSTEM CONTEXT]
You are a Staff Software Architect working on the OpsNexus platform. We need to implement the final major LangGraph worker node: the Invoice Reconciliation Agent. The system currently classifies `invoice_reconciliation` but falls back to a mock pipeline.

[YOUR TASK]
Implement the Invoice Reconciliation Sub-Agent by following these sequential steps.

1. **Update Schemas (`backend/orchestration/schemas.py`)**
   - Create a Pydantic schema named `InvoiceReconciliationResult`.
   - Fields: 
     - `is_matched`: boolean (True if invoice matches internal ledgers perfectly).
     - `discrepancies`: list of strings (e.g., "Vendor name mismatch", "Total amount exceeds PO by $500").
     - `approved_for_payment`: boolean
     - `extracted_total`: float

2. **Add MCP Ledger Tool (`backend/mcp_host/server.py`)**
   - Create a new `@mcp.tool()` named `get_open_purchase_orders()`.
   - Have it return a JSON string mocking internal financial data (e.g., a list of active PO numbers, approved vendors, and max approved amounts).

3. **Implement Invoice Worker Node (`backend/orchestration/graph.py`)**
   - Define a new system prompt `INVOICE_WORKER_SYSTEM_PROMPT`. Instruct the agent to read the uploaded invoice document, use the MCP tool to fetch open purchase orders, and mathematically reconcile the invoice against the internal ledger.
   - Create `_run_invoice_worker_agent(...)` enforcing the `InvoiceReconciliationResult` output with Pydantic auto-correction loops.
   - Create `invoice_worker_node(state: GraphState)` using `AsyncExitStack` to securely load the MCP tools.

4. **Update Graph Routing (`backend/orchestration/graph.py`)**
   - Add the node: `workflow.add_node("invoice_worker", invoice_worker_node)`.
   - Update `_route_after_supervisor` to route to `"invoice_worker"` when `route == "invoice_reconciliation"`.
   - Add edges and conditional routing maps accordingly.

5. **Update Agent Runner (`backend/orchestration/agent_runner.py`)**
   - In `trigger_agent_run`, handle the `invoice_reconciliation` route output.
   - Persist the extracted JSON into the `Answer` model (mapping discrepancies to `risk_flags` and `action_items`) so the frontend telemetry can display the financial reconciliation status to the operator.
```

---

## Summary of How This Works:
By providing these prompts to the AI, it will follow the exact architectural patterns already established in your codebase. It will:
1. Use **Pydantic** to guarantee the LLM outputs exact structures (like `is_compliant` or `discrepancies`).
2. Utilize **MCP 2.0** to inject new mock enterprise databases (Security Policies and Open Purchase Orders).
3. Connect the nodes cleanly into the **LangGraph** orchestrator so that `trigger_agent_run` can seamlessly pass the document down the correct worker pipeline.
