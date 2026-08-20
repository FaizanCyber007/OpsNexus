"""DRF Serializers and OpenAPI schemas for orchestration endpoints."""

from rest_framework import serializers


class DocumentUploadResponseSerializer(serializers.Serializer):
    """Response returned upon successful document upload and background dispatch."""

    status = serializers.CharField(
        default="processing",
        help_text="Status of the upload background processing job.",
    )
    document_id = serializers.UUIDField(
        help_text="Unique identifier of the newly created Document."
    )


class DocumentChatRequestSerializer(serializers.Serializer):
    """Request payload for the document RAG chat & model arena endpoint."""

    question = serializers.CharField(
        required=True,
        allow_blank=False,
        help_text="The question or prompt to ask about the specified document.",
    )
    compare = serializers.BooleanField(
        required=False,
        default=False,
        help_text=(
            "If true, runs concurrent inference on both Groq (Llama-3 70B) "
            "and Gemini Flash, comparing responses and execution latency."
        ),
    )


class RetrievedContextSnippetSerializer(serializers.Serializer):
    """Vector search context snippet retrieved from document memory."""

    text = serializers.CharField(
        help_text="Text content of the retrieved document chunk."
    )
    metadata = serializers.DictField(
        required=False,
        help_text="Metadata including document ID, file name, and source.",
    )
    distance = serializers.FloatField(
        required=False,
        allow_null=True,
        help_text="Cosine/L2 distance from query embedding.",
    )


class ModelInferenceResultSerializer(serializers.Serializer):
    """Individual model execution result and performance metrics."""

    model_name = serializers.CharField(help_text="Display name of the model.")
    provider = serializers.CharField(
        help_text="Provider name (e.g., 'gemini', 'groq')."
    )
    response = serializers.CharField(
        help_text="Synthesized answer text from the model."
    )
    execution_time_ms = serializers.IntegerField(
        help_text="Inference execution latency in milliseconds."
    )
    status = serializers.CharField(help_text="Execution status: 'success' or 'error'.")
    is_simulated = serializers.BooleanField(
        required=False,
        default=False,
        help_text="True if simulated fallback response was used.",
    )
    error = serializers.CharField(
        required=False, allow_null=True, help_text="Error message if inference failed."
    )


class ModelComparisonResultsSerializer(serializers.Serializer):
    """Container for multi-model arena comparison results."""

    groq = ModelInferenceResultSerializer(
        help_text="Groq (Llama-3 70B) inference result."
    )
    gemini = ModelInferenceResultSerializer(help_text="Gemini Flash inference result.")


class DocumentChatResponseSerializer(serializers.Serializer):
    """Complete response from the document RAG chat / arena endpoint."""

    compare = serializers.BooleanField(
        help_text="Whether multi-model comparison mode was enabled."
    )
    question = serializers.CharField(help_text="The user's queried question.")
    retrieved_context = RetrievedContextSnippetSerializer(
        many=True, help_text="List of relevant document context chunks retrieved."
    )
    result = ModelInferenceResultSerializer(
        required=False,
        help_text="Single model response (present when compare=False).",
    )
    results = ModelComparisonResultsSerializer(
        required=False,
        help_text="Multi-model comparison responses (present when compare=True).",
    )
    faster_model = serializers.CharField(
        required=False,
        allow_null=True,
        help_text="Provider with the lowest latency ('groq' or 'gemini').",
    )
    time_diff_ms = serializers.IntegerField(
        required=False,
        help_text="Difference in execution time between providers in milliseconds.",
    )
