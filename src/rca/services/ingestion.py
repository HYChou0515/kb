"""Ingestion service — source -> chunks -> LLM extraction -> graph.

Sources supported:
  - Plain text strings (`ingest_text`)
  - Files: .pdf, .txt, .md (`ingest_file`)
  - Directories: walk all supported files (`ingest_directory`)
  - Conversation transcripts (`ingest_conversation`)
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from pypdf import PdfReader

from rca.ports.in_.retain import ExtractionResult
from rca.ports.out.graph import IGraphAdapter
from rca.services.extraction import IExtractionService, render_extraction_for_cognee

logger = logging.getLogger(__name__)

CHUNK_CHAR_TARGET = 6000
CHUNK_CHAR_OVERLAP = 400


@dataclass
class IngestedChunk:
    source_label: str
    text: str
    extraction: ExtractionResult


def _chunk_text(
    text: str, *, target: int = CHUNK_CHAR_TARGET, overlap: int = CHUNK_CHAR_OVERLAP
) -> list[str]:
    text = text.strip()
    if len(text) <= target:
        return [text] if text else []
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + target, len(text))
        if end < len(text):
            snap = text.rfind("\n\n", start, end)
            if snap == -1 or snap < end - 1500:
                snap = text.rfind(". ", start, end)
            if snap != -1 and snap > start + target // 2:
                end = snap + 1
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return [c for c in chunks if c]


def _read_file(path: Path) -> list[tuple[str, str]]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        reader = PdfReader(str(path))
        out: list[tuple[str, str]] = []
        for i, page in enumerate(reader.pages, start=1):
            txt = page.extract_text() or ""
            for j, c in enumerate(_chunk_text(txt), start=1):
                out.append((f"{path.name}#p{i}-c{j}", c))
        return out
    elif suffix in {".txt", ".md", ".rst"}:
        txt = path.read_text(encoding="utf-8", errors="ignore")
        return [
            (f"{path.name}#c{j}", c) for j, c in enumerate(_chunk_text(txt), start=1)
        ]
    else:
        logger.warning("skipping unsupported file: %s", path)
        return []


class IIngestionService(ABC):
    @abstractmethod
    async def ingest_text(
        self,
        text: str,
        *,
        source_label: str = "inline-text",
        dataset: str = "rca",
        node_set: list[str] | None = None,
        run_cognify: bool = True,
    ) -> list[IngestedChunk]: ...

    @abstractmethod
    async def ingest_file(
        self,
        path: Path,
        *,
        dataset: str = "rca",
        node_set: list[str] | None = None,
        run_cognify: bool = True,
    ) -> list[IngestedChunk]: ...

    @abstractmethod
    async def ingest_directory(
        self,
        directory: Path,
        *,
        dataset: str = "rca",
        run_cognify: bool = True,
    ) -> list[IngestedChunk]: ...

    @abstractmethod
    async def ingest_conversation(
        self,
        conversation: Iterable[dict],
        *,
        session_id: str | None = None,
        dataset: str = "rca",
        run_cognify: bool = True,
    ) -> list[IngestedChunk]: ...


class IngestionPipelineService(IIngestionService):
    def __init__(self, extractor: IExtractionService, graph: IGraphAdapter) -> None:
        self.extractor = extractor
        self.graph = graph

    async def ingest_text(
        self,
        text: str,
        *,
        source_label: str = "inline-text",
        dataset: str = "rca",
        node_set: list[str] | None = None,
        run_cognify: bool = True,
    ) -> list[IngestedChunk]:
        chunks_text = _chunk_text(text)
        return await self._ingest_chunks(
            [(f"{source_label}#c{i + 1}", c) for i, c in enumerate(chunks_text)],
            dataset=dataset,
            node_set=node_set,
            run_cognify=run_cognify,
        )

    async def ingest_file(
        self,
        path: Path,
        *,
        dataset: str = "rca",
        node_set: list[str] | None = None,
        run_cognify: bool = True,
    ) -> list[IngestedChunk]:
        chunks = _read_file(path)
        return await self._ingest_chunks(
            chunks,
            dataset=dataset,
            node_set=node_set,
            run_cognify=run_cognify,
        )

    async def ingest_directory(
        self,
        directory: Path,
        *,
        dataset: str = "rca",
        run_cognify: bool = True,
    ) -> list[IngestedChunk]:
        all_chunks: list[tuple[str, str]] = []
        for p in sorted(directory.rglob("*")):
            if p.is_file():
                all_chunks.extend(_read_file(p))
        return await self._ingest_chunks(
            all_chunks, dataset=dataset, run_cognify=run_cognify
        )

    async def ingest_conversation(
        self,
        conversation: Iterable[dict],
        *,
        session_id: str | None = None,
        dataset: str = "rca",
        run_cognify: bool = True,
    ) -> list[IngestedChunk]:
        sid = session_id or datetime.now(timezone.utc).strftime(
            "rca-chat-%Y%m%d-%H%M%S"
        )
        rendered = "\n\n".join(
            f"[{turn.get('role', 'user').upper()}]\n{turn.get('content', '').strip()}"
            for turn in conversation
            if turn.get("content")
        )
        prefaced = (
            "This is a transcript of an RCA discussion in a semiconductor fab. "
            "Extract: (a) confirmed causal relationships, (b) hypotheses ruled out, "
            "(c) any new domain knowledge surfaced. Mark ruled-out hypotheses with "
            "polarity=negative on a relation typed `causes`.\n\n"
            f"{rendered}"
        )
        return await self.ingest_text(
            prefaced,
            source_label=sid,
            dataset=dataset,
            node_set=["rca_conversations"],
            run_cognify=run_cognify,
        )

    async def _ingest_chunks(
        self,
        chunks: list[tuple[str, str]],
        *,
        dataset: str,
        node_set: list[str] | None = None,
        run_cognify: bool,
    ) -> list[IngestedChunk]:
        await self.graph.setup()
        results: list[IngestedChunk] = []
        for label, text in chunks:
            logger.info("extracting: %s (%d chars)", label, len(text))
            extraction = self.extractor.extract(text, source_label=label)
            rendered = render_extraction_for_cognee(extraction, source_label=label)
            await self.graph.remember_text(rendered, dataset=dataset, node_set=node_set)
            await self.graph.remember_text(
                f"# Raw source: {label}\n\n{text}",
                dataset=dataset,
                node_set=node_set,
            )
            results.append(IngestedChunk(label, text, extraction))

        if run_cognify and results:
            logger.info("running cognify on dataset=%s", dataset)
            await self.graph.cognify(dataset=dataset)
        return results
