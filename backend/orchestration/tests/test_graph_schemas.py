import pytest
from pydantic import ValidationError

from orchestration.graph import ClassificationResult, StructuredAnswer


class TestClassificationResult:
    def test_valid_data_constructs_successfully(self):
        result = ClassificationResult(route="sales_rfp", reasoning="Looks like an RFP.")
        assert result.route == "sales_rfp"

    def test_invalid_route_raises_validation_error(self):
        with pytest.raises(ValidationError):
            ClassificationResult(route="not_a_real_route", reasoning="bad")

    def test_missing_reasoning_raises_validation_error(self):
        with pytest.raises(ValidationError):
            ClassificationResult(route="sales_rfp")

    def test_invalid_json_raises_validation_error_not_uncaught_crash(self):
        with pytest.raises(ValidationError):
            ClassificationResult.model_validate_json(
                '{"route": "sales_rfp"'
            )  # malformed


class TestStructuredAnswer:
    def test_valid_data_constructs_successfully(self):
        answer = StructuredAnswer(content="Here is our answer.", confidence_score=0.85)
        assert answer.confidence_score == 0.85

    @pytest.mark.parametrize("bad_score", [-0.1, 1.1, 5.0])
    def test_out_of_range_confidence_raises_validation_error(self, bad_score):
        with pytest.raises(ValidationError):
            StructuredAnswer(content="text", confidence_score=bad_score)

    def test_missing_content_raises_validation_error(self):
        with pytest.raises(ValidationError):
            StructuredAnswer(confidence_score=0.5)

    def test_wrong_type_raises_validation_error_not_silent_coercion_failure(self):
        with pytest.raises(ValidationError):
            StructuredAnswer(content="text", confidence_score="not-a-number")

    def test_malformed_json_raises_validation_error(self):
        with pytest.raises(ValidationError):
            StructuredAnswer.model_validate_json("{not valid json at all")
