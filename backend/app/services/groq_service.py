import asyncio
import json
import logging
import time

from groq import APIConnectionError, APIStatusError, APITimeoutError, AsyncGroq
from langchain_core.exceptions import OutputParserException
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from pydantic import ValidationError

from app.agents.prompts import GROQ_SYSTEM_PROMPT
from app.core.config import Settings
from app.schemas.diagnosis import DiseaseExplanation


logger = logging.getLogger(__name__)

_ELLIPSIS = "..."


class GroqServiceError(RuntimeError):
    pass


class GroqNotConfiguredError(GroqServiceError):
    pass


class GroqUnavailableError(GroqServiceError):
    pass


class GroqTimeoutError(GroqServiceError):
    pass


class GroqInvalidResponseError(GroqServiceError):
    pass


class GroqService:
    """Groq synthesis service; it never performs retrieval itself."""

    def __init__(self, settings: Settings) -> None:
        self.model = settings.groq_model
        self.timeout_seconds = settings.groq_timeout_seconds
        self.health_timeout_seconds = settings.groq_health_timeout_seconds
        self.health_cache_seconds = settings.groq_health_cache_seconds
        self.max_payload_chars = settings.groq_max_payload_chars
        self._configured = settings.groq_configured
        self._api_key = (
            settings.groq_api_key.get_secret_value().strip() if settings.groq_api_key else ""
        )
        self._health_checked_at = 0.0
        self._health_available = False
        self._generation_slots = asyncio.Semaphore(settings.max_concurrent_groq_requests)
        self._health_lock = asyncio.Lock()
        self._client = (
            AsyncGroq(
                api_key=self._api_key,
                base_url=settings.groq_base_url,
                timeout=self.health_timeout_seconds,
                max_retries=0,
            )
            if self._configured
            else None
        )
        self._chain = None
        if self._configured:
            parser = PydanticOutputParser(pydantic_object=DiseaseExplanation)
            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", GROQ_SYSTEM_PROMPT + "\n\n{format_instructions}"),
                    (
                        "human",
                        "Synthesize only the supplied prediction and validated evidence. "
                        "Return one JSON object and no markdown.\n\n{evidence_context}\n\n{retry_instruction}",
                    ),
                ]
            ).partial(format_instructions=parser.get_format_instructions())
            llm = ChatGroq(
                api_key=self._api_key,
                base_url=settings.groq_base_url,
                model=self.model,
                temperature=0,
                max_tokens=settings.groq_max_tokens,
                timeout=self.timeout_seconds,
                max_retries=settings.groq_max_retries,
                **(
                    {"reasoning_effort": settings.groq_reasoning_effort}
                    if settings.groq_reasoning_effort
                    else {}
                ),
            )
            self._chain = prompt | llm | parser

    @property
    def configured(self) -> bool:
        return self._configured

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()

    async def check_available(self) -> bool:
        if not self._configured or self._client is None:
            return False
        now = time.monotonic()
        if now - self._health_checked_at < self.health_cache_seconds:
            return self._health_available
        async with self._health_lock:
            now = time.monotonic()
            if now - self._health_checked_at < self.health_cache_seconds:
                return self._health_available
            self._health_available = False
            try:
                response = await asyncio.wait_for(
                    self._client.models.list(),
                    timeout=self.health_timeout_seconds,
                )
                model_ids = {str(getattr(item, "id", "") or "") for item in response.data}
                self._health_available = self.model in model_ids
            except Exception:
                self._health_available = False
            self._health_checked_at = time.monotonic()
            return self._health_available

    async def generate_explanation(self, evidence_payload: dict) -> DiseaseExplanation:
        if not self._configured or self._chain is None:
            raise GroqNotConfiguredError("The Groq explanation service is not configured.")
        evidence_context, trimmed = self._fit_payload(evidence_payload)
        if trimmed:
            logger.warning(
                "Condensed the evidence payload to %d characters for Groq; %d source(s) omitted",
                len(evidence_context),
                trimmed,
            )
        for attempt in range(2):
            retry_instruction = ""
            if attempt == 1:
                retry_instruction = (
                    "The previous output failed schema validation. Copy source objects exactly, "
                    "do not add facts, and include every required field."
                )
            try:
                async with self._generation_slots:
                    result = await asyncio.wait_for(
                        self._chain.ainvoke(
                            {
                                "evidence_context": evidence_context,
                                "retry_instruction": retry_instruction,
                            }
                        ),
                        timeout=self.timeout_seconds,
                    )
                return DiseaseExplanation.model_validate(result)
            except (OutputParserException, ValidationError) as exc:
                if attempt == 1:
                    raise GroqInvalidResponseError(
                        "Groq returned invalid structured output after one retry."
                    ) from exc
            except (TimeoutError, asyncio.TimeoutError, APITimeoutError) as exc:
                raise GroqTimeoutError("The Groq explanation request timed out.") from exc
            except (APIConnectionError, APIStatusError) as exc:
                raise GroqUnavailableError("The Groq explanation service is unavailable.") from exc
            except GroqServiceError:
                raise
            except Exception as exc:
                raise GroqUnavailableError("The Groq explanation service is unavailable.") from exc
        raise GroqInvalidResponseError("Groq returned invalid structured output.")

    def _fit_payload(self, payload: dict) -> tuple[str, int]:
        """Keep the request inside the provider request-size limit.

        Groq rejects oversized requests with HTTP 413 well below the advertised
        context window, so the evidence is condensed deterministically. The
        condensed copy is only what the model sees; the caller keeps validating
        the returned explanation against the complete evidence set.
        """
        for max_sources, snippet_chars in (
            (24, 1400),
            (16, 1100),
            (12, 900),
            (10, 700),
            (8, 600),
            (6, 450),
            (4, 350),
            (3, 250),
        ):
            condensed, omitted = self._condense(payload, max_sources, snippet_chars)
            context = json.dumps(condensed, ensure_ascii=False, indent=2)
            if len(context) <= self.max_payload_chars:
                return context, omitted
        condensed, omitted = self._condense(payload, 2, 200)
        return json.dumps(condensed, ensure_ascii=False, indent=2), omitted

    def _condense(
        self, payload: dict, max_sources: int, snippet_chars: int
    ) -> tuple[dict, int]:
        evidence = payload.get("validated_evidence")
        if not isinstance(evidence, dict):
            return payload, 0

        sources = [item for item in evidence.get("sources", []) if isinstance(item, dict)]
        kept, omitted = self._select_sources(sources, max_sources)

        condensed_sources = []
        for source in kept:
            item = dict(source)
            snippet = " ".join(str(item.get("snippet", "")).split())
            if len(snippet) > snippet_chars:
                item["snippet"] = snippet[:snippet_chars].rstrip() + _ELLIPSIS
            condensed_sources.append(item)

        categories: dict[str, list[str]] = {}
        for claim in evidence.get("claims", []):
            if not isinstance(claim, dict):
                continue
            category = str(claim.get("category", "unknown"))
            for url in claim.get("source_urls", []):
                if url in {source.get("url") for source in kept}:
                    categories.setdefault(category, [])
                    if url not in categories[category]:
                        categories[category].append(str(url))

        condensed = dict(payload)
        condensed["validated_evidence"] = {
            "status": evidence.get("status"),
            "evidence_by_category": categories,
            "sources": condensed_sources,
            "disagreements": evidence.get("disagreements", []),
            "warnings": evidence.get("warnings", []),
            "note": (
                "Each source snippet is the only supplied evidence text. Cite these "
                "sources exactly and never introduce text that is not present in them."
            ),
        }
        return condensed, omitted

    @staticmethod
    def _select_sources(sources: list[dict], max_sources: int) -> tuple[list[dict], int]:
        if len(sources) <= max_sources:
            return sources, 0
        ranked = sorted(
            enumerate(sources),
            key=lambda pair: (not bool(pair[1].get("authoritative")), pair[0]),
        )
        chosen_indices = {index for index, _ in ranked[:max_sources]}
        kept = [source for index, source in enumerate(sources) if index in chosen_indices]
        return kept, len(sources) - len(kept)
