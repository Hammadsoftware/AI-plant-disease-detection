import asyncio
import logging
from collections.abc import Sequence
from urllib.parse import urlparse

import httpx

from app.core.config import Settings
from app.schemas.research import ResearchBundle, ResearchSource, SourceType


logger = logging.getLogger(__name__)


class WebSearchError(RuntimeError):
    pass


class WebSearchNotConfiguredError(WebSearchError):
    pass


class WebSearchService:
    """Configurable live-search boundary that currently supports Tavily."""

    def __init__(self, settings: Settings) -> None:
        self.provider = settings.search_provider
        self.timeout_seconds = settings.search_timeout_seconds
        self.max_results = settings.search_max_results_per_query
        self.max_queries = settings.search_max_queries_per_node
        self._request_slots = asyncio.Semaphore(settings.max_concurrent_search_requests)
        self._api_key = (
            settings.tavily_api_key.get_secret_value().strip()
            if settings.tavily_api_key
            else ""
        )
        self._client = httpx.AsyncClient(
            base_url=settings.tavily_base_url,
            timeout=httpx.Timeout(self.timeout_seconds),
            follow_redirects=False,
            headers={"User-Agent": "plant-disease-evidence-api/2.0"},
        )

    @property
    def configured(self) -> bool:
        return self.provider == "tavily" and bool(self._api_key)

    async def close(self) -> None:
        await self._client.aclose()

    async def check_available(self) -> bool:
        # Tavily has no quota-free readiness endpoint. This reports whether a supported
        # provider is fully configured; request failures are reported per diagnosis.
        return self.configured

    async def search(
        self,
        queries: Sequence[str],
        *,
        topic: str,
    ) -> ResearchBundle:
        selected_queries = [query.strip() for query in queries if query.strip()][: self.max_queries]
        if not self.configured:
            raise WebSearchNotConfiguredError(
                f"The {self.provider} web-search provider is not configured."
            )
        if not selected_queries:
            return ResearchBundle(topic=topic, status="unavailable", errors=["No search query was provided."])

        responses = await asyncio.gather(
            *(self._search_one(query) for query in selected_queries),
            return_exceptions=True,
        )
        sources_by_url: dict[str, tuple[ResearchSource, float]] = {}
        errors: list[str] = []
        for query, response in zip(selected_queries, responses, strict=True):
            if isinstance(response, Exception):
                logger.warning("%s research query failed: %s", topic, type(response).__name__)
                errors.append(f"Live search failed for one {topic} query.")
                continue
            for source, score in response:
                existing = sources_by_url.get(source.url)
                if existing is None or score > existing[1]:
                    sources_by_url[source.url] = (source, score)

        ranked = sorted(
            sources_by_url.values(),
            key=lambda item: (item[0].authoritative, item[1]),
            reverse=True,
        )
        sources = [source for source, _score in ranked[:10]]
        if sources and errors:
            status = "partial"
        elif sources:
            status = "available"
        else:
            status = "unavailable"
        return ResearchBundle(
            topic=topic,
            status=status,
            queries=selected_queries,
            sources=sources,
            errors=errors,
        )

    async def _search_one(self, query: str) -> list[tuple[ResearchSource, float]]:
        if self.provider != "tavily":
            raise WebSearchNotConfiguredError(f"Unsupported search provider: {self.provider}")
        async with self._request_slots:
            response = await self._client.post(
                "/search",
                json={
                "api_key": self._api_key,
                "query": query,
                "topic": "general",
                "search_depth": "advanced",
                "max_results": self.max_results,
                "include_answer": False,
                "include_raw_content": False,
                    "include_images": False,
                },
            )
        response.raise_for_status()
        payload = response.json()
        results = payload.get("results", [])
        if not isinstance(results, list):
            raise WebSearchError("The search provider returned an invalid result list.")

        normalized: list[tuple[ResearchSource, float]] = []
        for item in results:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "").strip()
            url = str(item.get("url") or "").strip()
            snippet = " ".join(str(item.get("content") or "").split())[:1200]
            parsed = urlparse(url)
            if not title or not snippet or parsed.scheme not in {"http", "https"} or not parsed.netloc:
                continue
            source_type, authoritative = classify_source(parsed.hostname or "", title)
            source = ResearchSource(
                title=title[:300],
                url=url,
                source=(parsed.hostname or "unknown").lower(),
                source_type=source_type,
                snippet=snippet,
                query=query,
                authoritative=authoritative,
            )
            try:
                score = float(item.get("score") or 0.0)
            except (TypeError, ValueError):
                score = 0.0
            normalized.append((source, score))
        return normalized


def classify_source(hostname: str, title: str) -> tuple[SourceType, bool]:
    host = hostname.lower().removeprefix("www.")
    title_lower = title.casefold()
    if (
        host.endswith(".gov")
        or ".gov." in host
        or host.endswith("gov.pk")
        or "department of plant protection" in title_lower
    ):
        return "government", True
    if host.endswith(".edu") or ".edu." in host or "extension" in host or "extension" in title_lower:
        return "university_extension", True
    if host == "fao.org" or host.endswith(".fao.org"):
        return "international_organization", True
    if any(name in host for name in ("cgiar.org", "cabi.org", "cimmyt.org", "irri.org", "cipotato.org")):
        return "research_institution", True
    if any(name in host for name in ("doi.org", "sciencedirect.com", "springer.com", "wiley.com")):
        return "peer_reviewed", True
    return "other", False
