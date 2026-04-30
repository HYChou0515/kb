"""stale_notify — detect and log warnings for stale CaseStudy records.

A case is "stale" when:
  - status = "active"
  - created_time > stale_days ago
  - no agreed RCAReport exists for the case

Notification is log-based (WARNING level). CaseStudy.last_stale_notify_at
gates re-notification: a case is skipped if it was notified within the
notify_interval_days window.
"""

from __future__ import annotations

import datetime as dt
import logging
from dataclasses import dataclass

from autocrud.types import (
    DataSearchCondition,
    DataSearchGroup,
    DataSearchLogicOperator,
    DataSearchOperator,
    ResourceMetaSearchQuery,
    ResourceMetaSearchSort,
    ResourceMetaSortDirection,
    ResourceMetaSortKey,
)
from msgspec import structs

from rca.domain.case_study import CaseStudy
from rca.ports.out.autocrud import IAutoCrudWrapper

logger = logging.getLogger(__name__)

STALE_DAYS_DEFAULT = 7
NOTIFY_INTERVAL_DAYS_DEFAULT = 3


@dataclass
class StaleCaseInfo:
    case_id: str
    title: str
    created_time: dt.datetime
    last_stale_notify_at: str | None


def find_stale_cases(
    autocrud: IAutoCrudWrapper,
    *,
    stale_days: int = STALE_DAYS_DEFAULT,
) -> list[StaleCaseInfo]:
    """Return active CaseStudy records older than stale_days with no agreed report."""
    case_rm = autocrud.case_study_mgr()
    query = ResourceMetaSearchQuery(
        conditions=[
            DataSearchGroup(
                operator=DataSearchLogicOperator.and_op,
                conditions=[
                    DataSearchCondition(
                        field_path="status",
                        operator=DataSearchOperator.equals,
                        value="active",
                    ),
                ],
            )
        ],
        sorts=[
            ResourceMetaSearchSort(
                key=ResourceMetaSortKey.created_time,
                direction=ResourceMetaSortDirection.ascending,
            )
        ],
        limit=1000,
    )
    now = dt.datetime.now(dt.UTC)
    cutoff = now - dt.timedelta(days=stale_days)

    stale: list[StaleCaseInfo] = []
    for item in case_rm.list_resources(query):
        info = getattr(item, "info", None)
        data = getattr(item, "data", None)
        if info is None or not isinstance(data, CaseStudy):
            continue
        created_time: dt.datetime = info.created_time
        if created_time > cutoff:
            continue
        case_id: str = info.resource_id
        if _has_agreed_report(case_id, autocrud):
            continue
        stale.append(
            StaleCaseInfo(
                case_id=case_id,
                title=data.title,
                created_time=created_time,
                last_stale_notify_at=data.last_stale_notify_at,
            )
        )
    return stale


def notify_stale_cases(
    autocrud: IAutoCrudWrapper,
    *,
    stale_days: int = STALE_DAYS_DEFAULT,
    notify_interval_days: int = NOTIFY_INTERVAL_DAYS_DEFAULT,
) -> int:
    """Log warnings for stale cases and update last_stale_notify_at.

    Skips cases notified within notify_interval_days. Returns count notified.
    """
    stale = find_stale_cases(autocrud, stale_days=stale_days)
    now = dt.datetime.now(dt.UTC)
    interval = dt.timedelta(days=notify_interval_days)
    notified = 0

    case_rm = autocrud.case_study_mgr()
    for info in stale:
        if info.last_stale_notify_at:
            last = dt.datetime.fromisoformat(info.last_stale_notify_at)
            if last.tzinfo is None:
                last = last.replace(tzinfo=dt.UTC)
            if now - last < interval:
                logger.debug(
                    "stale case %s: notified %s ago — skipping (interval=%dd)",
                    info.case_id,
                    now - last,
                    notify_interval_days,
                )
                continue

        age_days = (now - info.created_time).total_seconds() / 86400
        logger.warning(
            "STALE CASE: case=%s title=%r — no agreed report after %.0f days. "
            "User should be prompted to submit a final report.",
            info.case_id,
            info.title,
            age_days,
        )

        case_resource = case_rm.get(info.case_id)
        new_case = structs.replace(
            case_resource.data, last_stale_notify_at=now.isoformat()
        )
        case_rm.update(info.case_id, new_case, user="system", now=now)
        notified += 1

    return notified


# ─── helpers ─────────────────────────────────────────────────────────────────


def _has_agreed_report(case_id: str, autocrud: IAutoCrudWrapper) -> bool:
    report_rm = autocrud.rca_report_mgr()
    query = ResourceMetaSearchQuery(
        conditions=[
            DataSearchGroup(
                operator=DataSearchLogicOperator.and_op,
                conditions=[
                    DataSearchCondition(
                        field_path="case_study_id",
                        operator=DataSearchOperator.equals,
                        value=case_id,
                    ),
                    DataSearchCondition(
                        field_path="agreed",
                        operator=DataSearchOperator.equals,
                        value=True,
                    ),
                ],
            )
        ],
        limit=1,
    )
    for _ in report_rm.list_resources(query):
        return True
    return False
