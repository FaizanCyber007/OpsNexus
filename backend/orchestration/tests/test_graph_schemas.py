import pytest
from pydantic import ValidationError

from orchestration.schemas import ClassificationResult, StructuredAnswer


class TestClassificationResult:
    @pytest.mark.parametrize(
        "route",
        ["sales_rfp", "invoice_reconciliation", "compliance_audit", "general_intake"],
    )
    def test_all_valid_routes_construct_successfully(self, route):
        result = ClassificationResult(
            route=route, reasoning="Valid classification reason."
        )
        assert result.route == route
        assert result.reasoning == "Valid classification reason."

    def test_invalid_route_raises_validation_error(self):
        with pytest.raises(ValidationError):
            ClassificationResult(route="not_a_real_route", reasoning="bad")

    def test_missing_reasoning_raises_validation_error(self):
        with pytest.raises(ValidationError):
            ClassificationResult(route="sales_rfp")

    def test_missing_route_raises_validation_error(self):
        with pytest.raises(ValidationError):
            ClassificationResult(reasoning="Reason without route.")

    def test_invalid_json_raises_validation_error_not_uncaught_crash(self):
        with pytest.raises(ValidationError):
            ClassificationResult.model_validate_json(
                '{"route": "sales_rfp"'
            )  # malformed

    def test_json_roundtrip(self):
        result = ClassificationResult(route="sales_rfp", reasoning="RFP questionnaire.")
        json_str = result.model_dump_json()
        restored = ClassificationResult.model_validate_json(json_str)
        assert restored.route == result.route
        assert restored.reasoning == result.reasoning


def _make_structured_answer(**overrides):
    defaults = dict(
        content="Here is our answer.",
        executive_summary="We can meet the requirements with minor caveats.",
        risk_flags=["Missing SOC2 Policy"],
        action_items=["Email CFO"],
        confidence_score=0.85,
    )
    defaults.update(overrides)
    return StructuredAnswer(**defaults)


class TestStructuredAnswer:
    def test_valid_data_constructs_successfully(self):
        answer = _make_structured_answer()
        assert answer.confidence_score == 0.85
        assert answer.risk_flags == ["Missing SOC2 Policy"]
        assert answer.action_items == ["Email CFO"]

    @pytest.mark.parametrize("valid_score", [0.0, 0.5, 1.0])
    def test_boundary_confidence_scores_allowed(self, valid_score):
        answer = _make_structured_answer(confidence_score=valid_score)
        assert answer.confidence_score == valid_score

    @pytest.mark.parametrize("bad_score", [-0.1, -0.001, 1.001, 1.1, 5.0])
    def test_out_of_range_confidence_raises_validation_error(self, bad_score):
        with pytest.raises(ValidationError):
            _make_structured_answer(confidence_score=bad_score)

    def test_missing_content_raises_validation_error(self):
        with pytest.raises(ValidationError):
            StructuredAnswer(
                executive_summary="summary",
                risk_flags=[],
                action_items=[],
                confidence_score=0.5,
            )

    def test_missing_executive_summary_raises_validation_error(self):
        with pytest.raises(ValidationError):
            StructuredAnswer(
                content="text",
                risk_flags=[],
                action_items=[],
                confidence_score=0.5,
            )

    def test_missing_risk_flags_raises_validation_error(self):
        with pytest.raises(ValidationError):
            StructuredAnswer(
                content="text",
                executive_summary="summary",
                action_items=[],
                confidence_score=0.5,
            )

    def test_missing_action_items_raises_validation_error(self):
        with pytest.raises(ValidationError):
            StructuredAnswer(
                content="text",
                executive_summary="summary",
                risk_flags=[],
                confidence_score=0.5,
            )

    def test_wrong_type_for_action_items_raises_validation_error(self):
        with pytest.raises(ValidationError):
            _make_structured_answer(action_items="Email CFO")

    def test_wrong_type_for_risk_flags_raises_validation_error(self):
        with pytest.raises(ValidationError):
            _make_structured_answer(risk_flags="High Churn")

    def test_wrong_type_raises_validation_error_not_silent_coercion_failure(self):
        with pytest.raises(ValidationError):
            _make_structured_answer(confidence_score="not-a-number")

    def test_malformed_json_raises_validation_error(self):
        with pytest.raises(ValidationError):
            StructuredAnswer.model_validate_json("{not valid json at all")

    def test_json_roundtrip(self):
        answer = _make_structured_answer()
        json_str = answer.model_dump_json()
        restored = StructuredAnswer.model_validate_json(json_str)
        assert restored.content == answer.content
        assert restored.executive_summary == answer.executive_summary
        assert restored.risk_flags == answer.risk_flags
        assert restored.action_items == answer.action_items
        assert restored.confidence_score == answer.confidence_score
