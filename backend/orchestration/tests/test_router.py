from types import SimpleNamespace

import pytest

from orchestration.router import DeterministicRouter


def _doc(file_path: str) -> SimpleNamespace:
    return SimpleNamespace(file_path=file_path)


@pytest.mark.parametrize(
    "file_path,expected_route",
    [
        ("rfp_2024.pdf", "sales_rfp"),
        ("Security_Questionnaire.docx", "sales_rfp"),
        ("vendor_invoice.pdf", "invoice_reconciliation"),
        ("general_ledger_export.csv", "invoice_reconciliation"),
        ("compliance_review.pdf", "compliance_audit"),
        ("soc2_report.pdf", "compliance_audit"),
    ],
)
def test_keyword_routes_take_priority(file_path, expected_route):
    assert DeterministicRouter().route(_doc(file_path)) == expected_route


@pytest.mark.parametrize(
    "file_path,expected_route",
    [
        ("random_upload.pdf", "invoice_reconciliation"),
        ("data_export.csv", "invoice_reconciliation"),
        ("proposal_draft.docx", "sales_rfp"),
        ("server_output.log", "compliance_audit"),
    ],
)
def test_extension_fallback_when_no_keyword_matches(file_path, expected_route):
    assert DeterministicRouter().route(_doc(file_path)) == expected_route


def test_default_route_for_unrecognized_extension():
    assert DeterministicRouter().route(_doc("mystery_file.xyz")) == "general_intake"


def test_route_is_case_insensitive():
    assert (
        DeterministicRouter().route(_doc("INVOICE_Q3.PDF")) == "invoice_reconciliation"
    )


def test_route_uses_basename_not_full_path():
    assert (
        DeterministicRouter().route(_doc("documents/2026/01/01/rfp_response.txt"))
        == "sales_rfp"
    )
