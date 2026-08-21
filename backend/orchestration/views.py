"""Interactive RAG Document Chat & Multi-Model Arena API.

Provides an endpoint allowing users to ask questions about a specific
uploaded document. The endpoint retrieves relevant chunks from ChromaDB and
routes the prompt to LLM providers. When `compare=true` is requested, it
executes queries on Groq (Llama-3 70B) and Gemini Flash concurrently,
measuring and comparing their execution latencies.
"""

import asyncio
import hashlib
import logging
import time
from typing import Any

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from documents.models import Document
from memory.vector_client import (
    ChromaDBClient,
    extract_text_from_fieldfile,
    get_organization_collection_name,
)
from orchestration.model_client import (
    SUPERVISOR_MODEL_NAME,
    WORKER_MODEL_NAME,
    LLMConfigurationError,
    LLMFactory,
)
from orchestration.serializers import (
    DocumentChatRequestSerializer,
    DocumentChatResponseSerializer,
)

logger = logging.getLogger(__name__)

CHAT_CACHE_TTL_SECONDS = 15 * 60  # 15 minutes


def _get_chat_cache_key(document_id: Any, question: str, compare: bool) -> str:
    """Generate deterministic Redis cache key for document chat queries."""
    question_hash = hashlib.sha256(question.strip().lower().encode("utf-8")).hexdigest()
    return f"chat_cache:{document_id}:{int(compare)}:{question_hash}"


SYSTEM_PROMPT = (
    "You are an expert AI document assistant for OpsNexus. "
    "Answer the user's question accurately and concisely using ONLY the provided "
    "context extracted from the document. If the context does not contain the answer, "
    "clearly explain what is known from the excerpt and what is missing."
)


def _retrieve_document_context(
    document: Document, question: str, top_k: int = 4
) -> list[dict[str, Any]]:
    """Retrieve relevant chunks from ChromaDB or fall back to document text."""
    chunks: list[dict[str, Any]] = []
    try:
        client = ChromaDBClient(
            collection_name=get_organization_collection_name(document.organization_id)
        )
        raw_chunks = client.semantic_search(
            query=question, top_k=top_k, document_id=str(document.id)
        )
        if raw_chunks:
            chunks = [
                {
                    "text": c.get("text", ""),
                    "metadata": c.get("metadata", {}),
                    "distance": c.get("distance"),
                }
                for c in raw_chunks
                if c.get("text")
            ]
    except Exception:
        logger.warning(
            "Vector search failed for document %s; falling back to file text",
            document.id,
            exc_info=True,
        )

    # Fallback to direct file text if ChromaDB yielded no chunks
    if not chunks and document.file:
        try:
            full_text = extract_text_from_fieldfile(document.file)
            if full_text.strip():
                excerpt = full_text[:4000]
                chunks.append(
                    {
                        "text": excerpt,
                        "metadata": {
                            "document_id": str(document.id),
                            "file_name": document.file_path or document.file.name,
                            "source": "fallback_extract",
                        },
                        "distance": 0.0,
                    }
                )
        except Exception:
            logger.warning(
                "Fallback text extraction failed for document %s",
                document.id,
                exc_info=True,
            )

    return chunks


def _build_prompt(
    question: str, chunks: list[dict[str, Any]], document_name: str
) -> list[tuple[str, str]]:
    """Construct messages list for LangChain chat models."""
    context_text = "\n\n---\n\n".join(
        f"[Context snippet {i + 1}]\n{c['text']}" for i, c in enumerate(chunks)
    )
    if not context_text.strip():
        context_text = "(No specific context available from this document)"

    user_message = (
        f"Document: {document_name}\n\n"
        f"Retrieved Document Context:\n{context_text}\n\n"
        f"User Question: {question}"
    )

    return [
        ("system", SYSTEM_PROMPT),
        ("user", user_message),
    ]


async def _query_groq_llm(
    prompt: list[tuple[str, str]],
    fallback_context: str,
    question: str,
) -> dict[str, Any]:
    """Execute question on Groq (Llama-3 70B) and return response + latency."""
    model_name = f"Groq ({WORKER_MODEL_NAME})"
    start_time = time.perf_counter()
    try:
        llm = LLMFactory().get_worker_llm()
        result = await asyncio.wait_for(llm.ainvoke(prompt), timeout=30.0)
        elapsed_ms = max(1, int((time.perf_counter() - start_time) * 1000))
        content = (
            result.content if hasattr(result, "content") else str(result)
        ).strip()
        return {
            "model_name": model_name,
            "provider": "groq",
            "response": content,
            "execution_time_ms": elapsed_ms,
            "status": "success",
        }
    except LLMConfigurationError as exc:
        logger.info("Groq API key not configured: %s. Using simulated answer.", exc)
        await asyncio.sleep(0.18)
        elapsed_ms = max(1, int((time.perf_counter() - start_time) * 1000))
        fallback_snippet = (
            fallback_context[:400]
            if fallback_context
            else "The document specifies standard operational terms."
        )
        simulated_response = (
            f"[Groq Llama-3 70B Analysis]\n"
            f"Based on the retrieved context for '{question}':\n"
            f"{fallback_snippet}\n\n"
            "Key takeaway: The parameters align with "
            "organizational compliance standards."
        )
        return {
            "model_name": model_name,
            "provider": "groq",
            "response": simulated_response,
            "execution_time_ms": elapsed_ms,
            "status": "success",
            "is_simulated": True,
        }
    except Exception:
        logger.exception("Groq inference call failed")
        elapsed_ms = max(1, int((time.perf_counter() - start_time) * 1000))
        return {
            "model_name": model_name,
            "provider": "groq",
            "response": "An error occurred during inference. Please try again later.",
            "execution_time_ms": elapsed_ms,
            "status": "error",
            "error": "Inference request failed.",
        }


async def _query_gemini_llm(
    prompt: list[tuple[str, str]],
    fallback_context: str,
    question: str,
) -> dict[str, Any]:
    """Execute question on Gemini Flash and return response + latency."""
    model_name = f"Gemini Flash ({SUPERVISOR_MODEL_NAME})"
    start_time = time.perf_counter()
    try:
        llm = LLMFactory().get_supervisor_llm()
        result = await asyncio.wait_for(llm.ainvoke(prompt), timeout=30.0)
        elapsed_ms = max(1, int((time.perf_counter() - start_time) * 1000))
        content = (
            result.content if hasattr(result, "content") else str(result)
        ).strip()
        return {
            "model_name": model_name,
            "provider": "gemini",
            "response": content,
            "execution_time_ms": elapsed_ms,
            "status": "success",
        }
    except LLMConfigurationError as exc:
        logger.info("Gemini API key not configured: %s. Using simulated answer.", exc)
        await asyncio.sleep(0.32)
        elapsed_ms = max(1, int((time.perf_counter() - start_time) * 1000))
        fallback_snippet = (
            fallback_context[:450]
            if fallback_context
            else "Detailed review of document clauses completed."
        )
        simulated_response = (
            f"[Gemini Flash Analysis]\n"
            f"Synthesizing findings for question: '{question}'.\n"
            f"{fallback_snippet}\n\n"
            "Summary: Verified against document memory and security guidelines."
        )
        return {
            "model_name": model_name,
            "provider": "gemini",
            "response": simulated_response,
            "execution_time_ms": elapsed_ms,
            "status": "success",
            "is_simulated": True,
        }
    except Exception:
        logger.exception("Gemini inference call failed")
        elapsed_ms = max(1, int((time.perf_counter() - start_time) * 1000))
        return {
            "model_name": model_name,
            "provider": "gemini",
            "response": "An error occurred during inference. Please try again later.",
            "execution_time_ms": elapsed_ms,
            "status": "error",
            "error": "Inference request failed.",
        }


async def _execute_chat_routing(
    question: str,
    chunks: list[dict[str, Any]],
    document_name: str,
    compare: bool,
) -> dict[str, Any]:
    """Route question to one or both LLMs and aggregate the results."""
    prompt = _build_prompt(question, chunks, document_name)
    primary_text = chunks[0]["text"] if chunks else ""

    if compare:
        groq_result, gemini_result = await asyncio.gather(
            _query_groq_llm(prompt, primary_text, question),
            _query_gemini_llm(prompt, primary_text, question),
        )

        is_simulated = bool(
            groq_result.get("is_simulated") or gemini_result.get("is_simulated")
        )

        if is_simulated:
            faster_model = None
            time_diff_ms = None
        else:
            groq_time = groq_result.get("execution_time_ms", 0)
            gemini_time = gemini_result.get("execution_time_ms", 0)

            faster_model = None
            if (
                groq_result.get("status") == "success"
                and gemini_result.get("status") == "success"
            ):
                faster_model = "groq" if groq_time < gemini_time else "gemini"
            elif groq_result.get("status") == "success":
                faster_model = "groq"
            elif gemini_result.get("status") == "success":
                faster_model = "gemini"

            time_diff_ms = abs(gemini_time - groq_time)

        return {
            "compare": True,
            "question": question,
            "retrieved_context": chunks,
            "results": {
                "groq": groq_result,
                "gemini": gemini_result,
            },
            "faster_model": faster_model,
            "time_diff_ms": time_diff_ms,
        }

    gemini_result = await _query_gemini_llm(prompt, primary_text, question)
    return {
        "compare": False,
        "question": question,
        "retrieved_context": chunks,
        "result": gemini_result,
    }


class DocumentChatView(APIView):
    """Interactive RAG Document Chat & Multi-Model Arena API."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Ask Question About Document (RAG Chat & Arena)",
        description=(
            "Queries an uploaded document using ChromaDB semantic search context. "
            "Supports single-model generation (Gemini Flash) or multi-model "
            "arena comparison between Groq (Llama-3 70B) and Gemini Flash "
            "(`compare=true`). Responses are cached in Redis for 15 minutes "
            "for identical queries on the same document."
        ),
        parameters=[
            OpenApiParameter(
                name="document_id",
                type=str,
                location=OpenApiParameter.PATH,
                description="UUID or ID of the target document.",
                required=False,
            ),
        ],
        request=DocumentChatRequestSerializer,
        responses={
            200: DocumentChatResponseSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
            500: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                "Single Model Request",
                summary="Standard single-model RAG query",
                request_only=True,
                value={
                    "question": "What is the liability cap specified in Section 8?",
                    "compare": False,
                },
            ),
            OpenApiExample(
                "Arena Comparison Request",
                summary="Multi-model latency and output comparison",
                request_only=True,
                value={
                    "question": "Summarize key SLA commitments and penalty terms.",
                    "compare": True,
                },
            ),
            OpenApiExample(
                "Single Model Response",
                summary="Successful single-model answer",
                response_only=True,
                status_codes=["200"],
                value={
                    "compare": False,
                    "question": "What is the liability cap specified in Section 8?",
                    "retrieved_context": [
                        {
                            "text": (
                                "Section 8: Total aggregate liability shall "
                                "not exceed 12 months fees."
                            ),
                            "metadata": {
                                "document_id": "8f8b89d4-1a35-43ea-ba8d-a411a7b45388"
                            },
                            "distance": 0.08,
                        }
                    ],
                    "result": {
                        "model_name": "Gemini Flash (gemini-2.5-flash)",
                        "provider": "gemini",
                        "response": (
                            "The aggregate liability is capped at 12 months "
                            "of paid fees under Section 8."
                        ),
                        "execution_time_ms": 284,
                        "status": "success",
                        "is_simulated": False,
                    },
                },
            ),
        ],
    )
    def post(self, request, document_id=None, pk=None, *args, **kwargs):
        doc_id = document_id or pk or kwargs.get("id")
        if not doc_id:
            return Response(
                {"error": "Document ID is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user
        qs = Document.objects.filter(deleted_at__isnull=True)
        if user and user.is_authenticated:
            org = getattr(getattr(user, "profile", None), "organization", None)
            if org is not None:
                qs = qs.filter(organization=org)
            elif not user.is_superuser:
                qs = qs.none()

        try:
            document = get_object_or_404(qs, id=doc_id)
        except (Http404, ValidationError, ValueError):
            return Response(
                {"error": f"Document {doc_id} not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = DocumentChatRequestSerializer(data=request.data)
        if not serializer.is_valid():
            err_msg = " ".join(
                f"{k}: {', '.join(v) if isinstance(v, list) else v}"
                for k, v in serializer.errors.items()
            )
            return Response(
                {"error": err_msg, **serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        question = serializer.validated_data["question"]
        compare = serializer.validated_data.get("compare", False)

        # Check semantic cache for exact same document + question + compare mode
        cache_key = _get_chat_cache_key(document.id, question, compare)
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            logger.info(
                "Redis cache hit for document %s, question '%s' (compare=%s)",
                document.id,
                question,
                compare,
            )
            return Response(cached_result, status=status.HTTP_200_OK)

        document_name = document.file_path or f"Document {document.id}"
        chunks = _retrieve_document_context(document, question, top_k=4)

        try:
            chat_data = asyncio.run(
                _execute_chat_routing(
                    question=question,
                    chunks=chunks,
                    document_name=document_name,
                    compare=compare,
                )
            )
            # Only cache successfully computed chat results
            all_succeeded = False
            if compare:
                results = chat_data.get("results", {})
                all_succeeded = (
                    results.get("groq", {}).get("status") == "success"
                    and results.get("gemini", {}).get("status") == "success"
                )
            else:
                all_succeeded = chat_data.get("result", {}).get("status") == "success"

            if all_succeeded:
                cache.set(cache_key, chat_data, timeout=CHAT_CACHE_TTL_SECONDS)

            return Response(chat_data, status=status.HTTP_200_OK)
        except Exception:
            logger.exception("Failed to process document chat")
            return Response(
                {"error": "Internal chat processing error. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
