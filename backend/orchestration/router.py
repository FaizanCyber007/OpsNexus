import os


class DeterministicRouter:
    """Mock stand-in for the future Supervisor Agent's classification step."""

    KEYWORD_ROUTES = {
        "rfp": "sales_rfp",
        "questionnaire": "sales_rfp",
        "invoice": "invoice_reconciliation",
        "ledger": "invoice_reconciliation",
        "compliance": "compliance_audit",
        "soc2": "compliance_audit",
    }
    EXTENSION_ROUTES = {
        ".pdf": "invoice_reconciliation",
        ".csv": "invoice_reconciliation",
        ".docx": "sales_rfp",
        ".log": "compliance_audit",
    }
    DEFAULT_ROUTE = "general_intake"

    def route(self, document) -> str:
        raw_path = (
            getattr(document, "file_path", "")
            or (document.file.name if getattr(document, "file", None) else "")
            or ""
        )
        name = os.path.basename(raw_path).lower() if raw_path else ""

        for keyword, route in self.KEYWORD_ROUTES.items():
            if keyword in name:
                return route

        _, extension = os.path.splitext(name)
        return self.EXTENSION_ROUTES.get(extension, self.DEFAULT_ROUTE)
