"""AutoCRUD-managed schemas for the RCA Knowledge Base.

Source-of-truth typed records:

  Lifecycle ───────────────────────
    CaseStudy     a defect case under investigation
    Session       one OpenCode interactive session against a CaseStudy
    RCAReport     the agreed final markdown report (1st-truth tier)

  Knowledge from sessions ─────────
    GlossaryEntry   in-house abbreviations / jargon expert used
    AgentFeedback   where agent was wrong/right vs expert; learning hooks
    DocumentSource  literature primer, conversation_extracted, or imported md

Cognee receives rendered text from these records via the cognee_mirror event
handler — it does NOT store these records itself, only their textual projection
indexed for retrieval.
"""

from __future__ import annotations

from typing import Annotated, Literal

from autocrud import DisplayName, OnDelete, Ref
from autocrud.types import Binary
from msgspec import Struct


# ─── Lifecycle ──────────────────────────────────────────────────────────────

CaseStatus = Literal["active", "closed", "archived"]
SessionStatus = Literal["active", "closed", "abandoned"]


class CaseStudy(Struct):
    """A defect case under investigation. Container for one or many Sessions.

    `workspace_archive` is a tar.gz of the case's persistent state (agent
    notes, draft reports, etc.) — committed at session close, restored at
    session open. Lives on the CaseStudy itself so each commit produces a
    new CaseStudy revision (full audit trail of the workspace evolution).
    """

    title: Annotated[str, DisplayName()]
    description: str
    owner: str = "unknown"
    status: CaseStatus = "active"
    # Optional but useful for filtering / dashboarding
    defect_type: str | None = None
    process_module: str | None = None
    scan_stage: str | None = None
    # Free-form tags for adhoc grouping (lot family, product, severity, ...)
    tags: list[str] = []
    # Snapshot of the workspace files at the most recent session close.
    # AutoCRUD stores the bytes in its blob store; field holds {file_id, size}.
    workspace_archive: Binary | None = None


class Session(Struct):
    """One interactive OpenCode session against a CaseStudy.

    `workspace_path` mimics the v2 PV: a directory committed-back at session
    close.  When a session is closed, transcript extraction creates GlossaryEntry,
    AgentFeedback, and DocumentSource records (linked back via session_id).
    """

    case_study_id: Annotated[str, Ref("case-study", on_delete=OnDelete.cascade)]
    status: SessionStatus = "active"
    opened_at: str = ""                                  # ISO-8601 UTC
    closed_at: str | None = None
    workspace_path: str = ""                             # active dir absolute path
    transcript_path: str | None = None                   # ./transcripts/<case>/<sid>.json
    rca_completed: bool = False                          # reached step 9 with agreed report?
    notes: str = ""                                      # free-form for agent jot-pad


# ─── 1st-truth final report ─────────────────────────────────────────────────


class RCAReport(Struct):
    """The co-authored markdown report agreed at step 9.

    `markdown_content` is the canonical body; `agreed=true` means the expert
    has explicitly signed off. Cognee mirror only ingests when agreed.
    """

    case_study_id: Annotated[str, Ref("case-study")]
    session_id: Annotated[str, Ref("session")]
    markdown_content: str = ""
    agreed: bool = False
    agreed_at: str | None = None
    signed_off_by: str = ""


# ─── 2nd-truth knowledge from sessions ──────────────────────────────────────


GlossaryConfidence = Literal["expert_explicit", "expert_implicit", "guessed"]


class GlossaryEntry(Struct):
    """In-house abbreviation / jargon / internal codename used by the expert.

    Captured at session close from transcript extraction. Lookup pattern
    (e.g. "what does ABC123 mean?") goes through AutoCRUD QB; semantic
    pattern goes through cognee /recall.
    """

    term: Annotated[str, DisplayName()]
    expansion: str
    context: str
    confidence: GlossaryConfidence = "expert_implicit"
    source_session_id: Annotated[
        str | None, Ref("session", on_delete=OnDelete.set_null)
    ] = None
    source_case_study_id: Annotated[
        str | None, Ref("case-study", on_delete=OnDelete.set_null)
    ] = None


FeedbackType = Literal["correction", "confirmation", "clarification"]


class AgentFeedback(Struct):
    """Where the agent's framing/vocabulary/reasoning was wrong or right
    vs. the expert. Used so future sessions can mirror the expert's language.
    """

    type: FeedbackType
    topic: Annotated[str, DisplayName()]
    agent_said: str                                    # condensed from transcript
    expert_correction: str                             # condensed from transcript
    learning_for_agent: str                            # what agent should change
    source_session_id: Annotated[
        str | None, Ref("session", on_delete=OnDelete.set_null)
    ] = None
    source_case_study_id: Annotated[
        str | None, Ref("case-study", on_delete=OnDelete.set_null)
    ] = None


# ─── 3rd-truth source documents ─────────────────────────────────────────────


DocumentKind = Literal[
    "literature",            # textbook excerpt, paper, process spec
    "primer",                # built-in seed corpus (data/primers/*.md)
    "rca_report_md",         # mirrored from RCAReport.markdown_content (1st truth)
    "conversation_extracted",  # rendered glossary/feedback bundle for a session
]


class DocumentSource(Struct):
    """Any document whose full text is ingested into cognee for retrieval.

    AutoCRUD stores the metadata + full text (audit, search, version);
    cognee gets a rendered chunk via the mirror event handler.
    """

    label: Annotated[str, DisplayName()]
    source_kind: DocumentKind
    text: str
    case_study_id: Annotated[
        str | None, Ref("case-study", on_delete=OnDelete.set_null)
    ] = None
    session_id: Annotated[
        str | None, Ref("session", on_delete=OnDelete.set_null)
    ] = None


# Convenience: tuple of all knowledge-bearing model classes that the cognee
# mirror should mirror to KB. CaseStudy / Session are pure lifecycle and never
# get mirrored.
KNOWLEDGE_MODELS = (RCAReport, GlossaryEntry, AgentFeedback, DocumentSource)
LIFECYCLE_MODELS = (CaseStudy, Session)
ALL_MODELS = LIFECYCLE_MODELS + KNOWLEDGE_MODELS
