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
        name = os.path.basename(document.file_path).lower()

        for keyword, route in self.KEYWORD_ROUTES.items():
            if keyword in name:
                return route

        _, extension = os.path.splitext(name)
        return self.EXTENSION_ROUTES.get(extension, self.DEFAULT_ROUTE)
