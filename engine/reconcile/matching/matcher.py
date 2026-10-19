from __future__ import annotations

from typing import Any, Optional
from rapidfuzz import fuzz

from reconcile.matching.normalizer import Normalizer
from reconcile.models import CandidateMatch, FieldDifference


class Matcher:
    """Core matching and candidate scoring algorithms."""

    def __init__(
        self,
        amount_tolerance: float = 0.01,
        date_tolerance_days: int = 7,
        entity_similarity_threshold: float = 70.0,
    ):
        self.amount_tolerance = amount_tolerance
        self.date_tolerance_days = date_tolerance_days
        self.entity_similarity_threshold = entity_similarity_threshold

    def compare_records(
        self,
        row_a: dict[str, Any],
        row_b: dict[str, Any],
        key_col_a: Optional[str],
        key_col_b: Optional[str],
        entity_col_a: Optional[str],
        entity_col_b: Optional[str],
        amount_col_a: Optional[str],
        amount_col_b: Optional[str],
        date_col_a: Optional[str],
        date_col_b: Optional[str],
        compare_cols: list[tuple[str, str]],
    ) -> list[FieldDifference]:
        """Compares two matched records across all assigned columns and returns detected differences."""
        diffs: list[FieldDifference] = []

        # 1. Compare Amount
        if amount_col_a and amount_col_b:
            raw_a = row_a.get(amount_col_a)
            raw_b = row_b.get(amount_col_b)
            amt_a = Normalizer.normalize_amount(raw_a)
            amt_b = Normalizer.normalize_amount(raw_b)

            if amt_a is not None and amt_b is not None:
                delta = round(amt_b - amt_a, 2)
                if abs(delta) > self.amount_tolerance:
                    sign_str = f"+{delta:,.2f}" if delta > 0 else f"{delta:,.2f}"
                    diffs.append(
                        FieldDifference(
                            field="amount",
                            val_a=raw_a,
                            val_b=raw_b,
                            diff_type="amount_delta",
                            delta=delta,
                            description=f"Amount difference: {sign_str}",
                        )
                    )
            elif amt_a != amt_b:
                diffs.append(
                    FieldDifference(
                        field="amount",
                        val_a=raw_a,
                        val_b=raw_b,
                        diff_type="amount_delta",
                        delta=None,
                        description="One dataset is missing amount value",
                    )
                )

        # 2. Compare Date
        if date_col_a and date_col_b:
            raw_d_a = row_a.get(date_col_a)
            raw_d_b = row_b.get(date_col_b)
            dt_a = Normalizer.normalize_date(raw_d_a)
            dt_b = Normalizer.normalize_date(raw_d_b)

            if dt_a and dt_b:
                days = Normalizer.date_diff_days(dt_a, dt_b)
                if days is not None and days > 0:
                    diffs.append(
                        FieldDifference(
                            field="date",
                            val_a=str(dt_a),
                            val_b=str(dt_b),
                            diff_type="date_diff",
                            delta=float(days),
                            description=f"{days} day{'s' if days > 1 else ''} difference",
                        )
                    )

        # 3. Compare Entity
        if entity_col_a and entity_col_b:
            ent_a = str(row_a.get(entity_col_a, "")).strip()
            ent_b = str(row_b.get(entity_col_b, "")).strip()
            norm_a = Normalizer.normalize_entity_name(ent_a)
            norm_b = Normalizer.normalize_entity_name(ent_b)

            if norm_a != norm_b and (ent_a or ent_b):
                sim = fuzz.token_sort_ratio(norm_a, norm_b)
                if sim < 95.0:
                    diffs.append(
                        FieldDifference(
                            field="entity",
                            val_a=ent_a,
                            val_b=ent_b,
                            diff_type="text_mismatch",
                            delta=None,
                            description=f"Entity name variance ({sim:.0f}% similarity)",
                        )
                    )

        # 4. Compare other fields
        for col_a_name, col_b_name in compare_cols:
            val_a = str(row_a.get(col_a_name, "")).strip()
            val_b = str(row_b.get(col_b_name, "")).strip()
            if Normalizer.normalize_text(val_a) != Normalizer.normalize_text(val_b):
                diffs.append(
                    FieldDifference(
                        field=col_a_name,
                        val_a=val_a,
                        val_b=val_b,
                        diff_type="text_mismatch",
                        delta=None,
                        description=f"Mismatch in {col_a_name}: '{val_a}' vs '{val_b}'",
                    )
                )

        return diffs

    def score_candidate(
        self,
        row_a: dict[str, Any],
        row_b: dict[str, Any],
        entity_col_a: Optional[str],
        entity_col_b: Optional[str],
        amount_col_a: Optional[str],
        amount_col_b: Optional[str],
        date_col_a: Optional[str],
        date_col_b: Optional[str],
    ) -> Optional[CandidateMatch]:
        """Evaluates whether row_b is a viable candidate for row_a and calculates match confidence score."""
        scores: list[float] = []
        weights: list[float] = []
        reasons: list[str] = []

        # 1. Amount score
        amt_a = Normalizer.normalize_amount(row_a.get(amount_col_a)) if amount_col_a else None
        amt_b = Normalizer.normalize_amount(row_b.get(amount_col_b)) if amount_col_b else None

        if amt_a is not None and amt_b is not None:
            delta = abs(amt_b - amt_a)
            if delta <= self.amount_tolerance:
                scores.append(1.0)
                weights.append(0.4)
                reasons.append("Exact amount")
            elif amt_a != 0 and delta / abs(amt_a) < 0.1:  # within 10%
                scores.append(0.6)
                weights.append(0.4)
                reasons.append(f"Amount delta of {delta:,.2f}")
            else:
                # Big amount difference, heavy penalty unless entity matches exactly
                scores.append(0.0)
                weights.append(0.4)

        # 2. Entity score
        ent_a = str(row_a.get(entity_col_a, "")).strip() if entity_col_a else ""
        ent_b = str(row_b.get(entity_col_b, "")).strip() if entity_col_b else ""
        norm_a = Normalizer.normalize_entity_name(ent_a)
        norm_b = Normalizer.normalize_entity_name(ent_b)

        if norm_a and norm_b:
            ent_sim = fuzz.token_sort_ratio(norm_a, norm_b) / 100.0
            scores.append(ent_sim)
            weights.append(0.4)
            if ent_sim >= 0.9:
                reasons.append("Entity matched")
            elif ent_sim >= 0.7:
                reasons.append(f"Entity fuzzy match ({int(ent_sim*100)}%)")
        elif ent_a and ent_b and ent_a.lower() == ent_b.lower():
            scores.append(1.0)
            weights.append(0.4)
            reasons.append("Entity matched")

        # 3. Date score
        dt_a = Normalizer.normalize_date(row_a.get(date_col_a)) if date_col_a else None
        dt_b = Normalizer.normalize_date(row_b.get(date_col_b)) if date_col_b else None

        if dt_a and dt_b:
            days = Normalizer.date_diff_days(dt_a, dt_b)
            if days == 0:
                scores.append(1.0)
                weights.append(0.2)
                reasons.append("Same date")
            elif days is not None and days <= self.date_tolerance_days:
                date_score = max(0.0, 1.0 - (days / (self.date_tolerance_days * 2)))
                scores.append(date_score)
                weights.append(0.2)
                reasons.append(f"Date difference +{days}d")
            else:
                scores.append(0.0)
                weights.append(0.2)
                if days:
                    reasons.append(f"Delayed by +{days} days")

        if not weights:
            return None

        total_weight = sum(weights)
        combined_score = sum(s * w for s, w in zip(scores, weights)) / total_weight

        # Filter out low-confidence pairs
        if combined_score < 0.55:
            return None

        source_b_row = row_b.get("_source_row", "?")
        source_b_file = row_b.get("_source_file", "")
        source_b_sheet = row_b.get("_source_sheet")
        source_b_label = f"Row #{source_b_row}"
        if source_b_sheet:
            source_b_label = f"{source_b_sheet} {source_b_label}"

        candidate_id = f"cand_{row_b.get('_source_row', id(row_b))}"
        return CandidateMatch(
            candidate_id=candidate_id,
            record_b=row_b,
            score=round(combined_score * 100, 1),
            source_b=source_b_label,
            entity_b=ent_b or None,
            amount_b=amt_b,
            date_b=str(dt_b) if dt_b else None,
            reason=", ".join(reasons),
        )
