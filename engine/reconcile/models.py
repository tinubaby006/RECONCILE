from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Optional


class ColumnRole(str, Enum):
    MATCH_KEY = "match_key"
    ENTITY = "entity"
    DATE = "date"
    AMOUNT = "amount"
    COMPARE = "compare"
    IGNORE = "ignore"


class RecordStatus(str, Enum):
    MATCHED = "matched"
    DISCREPANCY = "discrepancy"
    NEEDS_REVIEW = "needs_review"
    MISSING_IN_B = "missing_in_b"
    MISSING_IN_A = "missing_in_a"
    DUPLICATE = "duplicate"


@dataclass
class ColumnMeta:
    name: str
    inferred_type: str  # "string", "numeric", "date", "id"
    non_null_count: int
    unique_count: int
    sample_values: list[Any] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DatasetMeta:
    file_path: str
    file_name: str
    file_type: str  # "csv", "xlsx", "json"
    total_rows: int
    sheets: list[str] = field(default_factory=list)
    active_sheet: Optional[str] = None
    columns: list[ColumnMeta] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_path": self.file_path,
            "file_name": self.file_name,
            "file_type": self.file_type,
            "total_rows": self.total_rows,
            "sheets": self.sheets,
            "active_sheet": self.active_sheet,
            "columns": [c.to_dict() for c in self.columns],
        }


@dataclass
class ColumnMapping:
    col_a: str
    col_b: Optional[str]
    role: str  # ColumnRole
    confidence: float = 1.0
    status: str = "mapped"  # "mapped", "unmapped", "ignored"
    sample_a: Optional[str] = None
    sample_b: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FieldDifference:
    field: str
    val_a: Any
    val_b: Any
    diff_type: str  # "amount_delta", "date_diff", "text_mismatch", "missing"
    delta: Optional[float] = None
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CandidateMatch:
    candidate_id: str
    record_b: dict[str, Any]
    score: float  # 0.0 - 1.0 (or percentage 0 - 100)
    source_b: str
    entity_b: Optional[str] = None
    amount_b: Optional[float] = None
    date_b: Optional[str] = None
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ReconciliationRecord:
    id: str
    status: str  # RecordStatus
    status_label: str
    entity: str
    reference: str
    record_a: Optional[dict[str, Any]] = None
    record_b: Optional[dict[str, Any]] = None
    source_a: Optional[str] = None
    source_b: Optional[str] = None
    amount_a: Optional[float] = None
    amount_b: Optional[float] = None
    amount_diff: Optional[float] = None
    date_a: Optional[str] = None
    date_b: Optional[str] = None
    differences: list[FieldDifference] = field(default_factory=list)
    candidates: list[CandidateMatch] = field(default_factory=list)
    confidence_score: Optional[float] = None
    user_override: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "status": self.status,
            "status_label": self.status_label,
            "entity": self.entity,
            "reference": self.reference,
            "record_a": self.record_a,
            "record_b": self.record_b,
            "source_a": self.source_a,
            "source_b": self.source_b,
            "amount_a": self.amount_a,
            "amount_b": self.amount_b,
            "amount_diff": self.amount_diff,
            "date_a": self.date_a,
            "date_b": self.date_b,
            "differences": [d.to_dict() for d in self.differences],
            "candidates": [c.to_dict() for c in self.candidates],
            "confidence_score": self.confidence_score,
            "user_override": self.user_override,
        }


@dataclass
class ReconciliationSummary:
    total_a: int = 0
    total_b: int = 0
    total_records: int = 0
    matched_count: int = 0
    discrepancies_count: int = 0
    missing_in_b_count: int = 0
    missing_in_a_count: int = 0
    duplicates_count: int = 0
    needs_review_count: int = 0
    total_variance: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
