from __future__ import annotations

from typing import Any, Callable, Optional
import pandas as pd

from reconcile.matching.matcher import Matcher
from reconcile.matching.normalizer import Normalizer
from reconcile.models import (
    ColumnMapping,
    ColumnRole,
    RecordStatus,
    ReconciliationRecord,
    ReconciliationSummary,
)


class Reconciler:
    """Orchestrates end-to-end dataset reconciliation, grouping, and discrepancy detection."""

    def __init__(
        self,
        amount_tolerance: float = 0.01,
        date_tolerance_days: int = 7,
        entity_similarity_threshold: float = 70.0,
    ):
        self.matcher = Matcher(
            amount_tolerance=amount_tolerance,
            date_tolerance_days=date_tolerance_days,
            entity_similarity_threshold=entity_similarity_threshold,
        )

    def reconcile(
        self,
        df_a: pd.DataFrame,
        df_b: pd.DataFrame,
        mappings: list[ColumnMapping],
        user_overrides: Optional[dict[str, dict[str, Any]]] = None,
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ) -> tuple[ReconciliationSummary, list[ReconciliationRecord], dict[str, list[ReconciliationRecord]]]:
        """Performs full reconciliation between df_a and df_b using mappings and optional overrides."""
        if progress_callback:
            progress_callback(5, "Analyzing column roles...")

        # 1. Extract role mappings
        key_a, key_b = None, None
        ent_a, ent_b = None, None
        amt_a, amt_b = None, None
        dt_a, dt_b = None, None
        compare_cols: list[tuple[str, str]] = []

        for m in mappings:
            if m.status == "ignored" or not m.col_b:
                continue
            if m.role == ColumnRole.MATCH_KEY.value and not key_a:
                key_a, key_b = m.col_a, m.col_b
            elif m.role == ColumnRole.ENTITY.value and not ent_a:
                ent_a, ent_b = m.col_a, m.col_b
            elif m.role == ColumnRole.AMOUNT.value and not amt_a:
                amt_a, amt_b = m.col_a, m.col_b
            elif m.role == ColumnRole.DATE.value and not dt_a:
                dt_a, dt_b = m.col_a, m.col_b
            elif m.role == ColumnRole.COMPARE.value:
                compare_cols.append((m.col_a, m.col_b))

        rows_a = df_a.to_dict(orient="records")
        rows_b = df_b.to_dict(orient="records")

        if progress_callback:
            progress_callback(15, f"Indexing Dataset B ({len(rows_b)} records)...")

        # 2. Index Dataset B & Count Keys for Duplicates
        b_key_index: dict[str, list[dict[str, Any]]] = {}
        b_key_counts: dict[str, int] = {}

        for r_b in rows_b:
            if key_b:
                raw_k_b = str(r_b.get(key_b, "")).strip()
                norm_k_b = Normalizer.normalize_id(raw_k_b)
                if norm_k_b:
                    b_key_index.setdefault(norm_k_b, []).append(r_b)
                    b_key_counts[norm_k_b] = b_key_counts.get(norm_k_b, 0) + 1

        matched_b_indices: set[int] = set()
        records: list[ReconciliationRecord] = []

        # Track key occurrences in A to detect duplicates in A
        a_key_counts: dict[str, int] = {}
        if key_a:
            for r_a in rows_a:
                raw_k_a = str(r_a.get(key_a, "")).strip()
                k = Normalizer.normalize_id(raw_k_a)
                if k:
                    a_key_counts[k] = a_key_counts.get(k, 0) + 1

        total_a = len(rows_a)
        if progress_callback:
            progress_callback(30, f"Reconciling records from Dataset A ({total_a} rows)...")

        # 3. Match each record in A
        unmatched_a_indices: list[int] = []

        for i, r_a in enumerate(rows_a):
            if i % 100 == 0 and progress_callback and total_a > 0:
                pct = int(30 + (i / total_a) * 45)
                progress_callback(pct, f"Processing record {i+1} of {total_a}...")

            rec_id = f"rec_a_{r_a.get('_source_row', i+1)}"
            ref_val = str(r_a.get(key_a, "")) if key_a else f"Row #{r_a.get('_source_row', i+1)}"
            ent_val = str(r_a.get(ent_a, "Unknown Entity")) if ent_a else "Unassigned"
            amt_val_a = Normalizer.normalize_amount(r_a.get(amt_a)) if amt_a else None
            dt_val_a = str(Normalizer.normalize_date(r_a.get(dt_a))) if dt_a else None

            source_a_label = f"Row #{r_a.get('_source_row', i+1)}"
            if r_a.get("_source_sheet"):
                source_a_label = f"{r_a['_source_sheet']} {source_a_label}"

            raw_k_a = str(r_a.get(key_a, "")).strip() if key_a else ""
            norm_k_a = Normalizer.normalize_id(raw_k_a) if raw_k_a else ""
            is_dup_a = bool(norm_k_a and a_key_counts.get(norm_k_a, 0) > 1)

            # Strict Level 1 Deterministic Match: Exact normalized key equality only
            candidates_in_b = b_key_index.get(norm_k_a, []) if norm_k_a else []
            available_b = [r for r in candidates_in_b if id(r) not in matched_b_indices]
            selected_b: Optional[dict[str, Any]] = None

            if available_b:
                selected_b = available_b[0]
                matched_b_indices.add(id(selected_b))
            elif candidates_in_b:
                # Key matched but all corresponding B records were already matched -> Duplicate Key
                selected_b = candidates_in_b[0]

            if selected_b:
                source_b_label = f"Row #{selected_b.get('_source_row', '?')}"
                if selected_b.get("_source_sheet"):
                    source_b_label = f"{selected_b['_source_sheet']} {source_b_label}"

                amt_val_b = Normalizer.normalize_amount(selected_b.get(amt_b)) if amt_b else None
                dt_val_b = str(Normalizer.normalize_date(selected_b.get(dt_b))) if dt_b else None
                amt_delta = round(amt_val_b - amt_val_a, 2) if (amt_val_a is not None and amt_val_b is not None) else None

                diffs = self.matcher.compare_records(
                    row_a=r_a,
                    row_b=selected_b,
                    key_col_a=key_a,
                    key_col_b=key_b,
                    entity_col_a=ent_a,
                    entity_col_b=ent_b,
                    amount_col_a=amt_a,
                    amount_col_b=amt_b,
                    date_col_a=dt_a,
                    date_col_b=dt_b,
                    compare_cols=compare_cols,
                )

                if is_dup_a or len(candidates_in_b) > 1:
                    status = RecordStatus.DUPLICATE.value
                    status_label = "Duplicate Key"
                elif diffs:
                    status = RecordStatus.DISCREPANCY.value
                    status_label = "Discrepancy"
                else:
                    status = RecordStatus.MATCHED.value
                    status_label = "Matched"

                records.append(
                    ReconciliationRecord(
                        id=rec_id,
                        status=status,
                        status_label=status_label,
                        entity=ent_val,
                        reference=ref_val,
                        record_a=r_a,
                        record_b=selected_b,
                        source_a=source_a_label,
                        source_b=source_b_label,
                        amount_a=amt_val_a,
                        amount_b=amt_val_b,
                        amount_diff=amt_delta,
                        date_a=dt_val_a,
                        date_b=dt_val_b,
                        differences=diffs,
                        candidates=[],
                        confidence_score=1.0 if not diffs else 0.9,
                    )
                )
            else:
                unmatched_a_indices.append(i)

        # 3.2 Level 2 Candidate Matching for unkeyed/unmatched A rows
        for idx_a in unmatched_a_indices:
            r_a = rows_a[idx_a]
            rec_id = f"rec_a_{r_a.get('_source_row', idx_a+1)}"
            ref_val = str(r_a.get(key_a, "")) if key_a else f"Row #{r_a.get('_source_row', idx_a+1)}"
            ent_val = str(r_a.get(ent_a, "Unknown Entity")) if ent_a else "Unassigned"
            amt_val_a = Normalizer.normalize_amount(r_a.get(amt_a)) if amt_a else None
            dt_val_a = str(Normalizer.normalize_date(r_a.get(dt_a))) if dt_a else None

            source_a_label = f"Row #{r_a.get('_source_row', idx_a+1)}"
            if r_a.get("_source_sheet"):
                source_a_label = f"{r_a['_source_sheet']} {source_a_label}"

            unmatched_b_pool = [r for r in rows_b if id(r) not in matched_b_indices]
            candidate_matches = []

            for r_b in unmatched_b_pool:
                cand = self.matcher.score_candidate(
                    row_a=r_a,
                    row_b=r_b,
                    key_col_a=key_a,
                    key_col_b=key_b,
                    entity_col_a=ent_a,
                    entity_col_b=ent_b,
                    amount_col_a=amt_a,
                    amount_col_b=amt_b,
                    date_col_a=dt_a,
                    date_col_b=dt_b,
                )
                if cand:
                    candidate_matches.append(cand)

            candidate_matches.sort(key=lambda c: c.score, reverse=True)

            if candidate_matches:
                top_cand = candidate_matches[0]
                matched_b_indices.add(id(top_cand.record_b))

                diffs = self.matcher.compare_records(
                    row_a=r_a,
                    row_b=top_cand.record_b,
                    key_col_a=key_a,
                    key_col_b=key_b,
                    entity_col_a=ent_a,
                    entity_col_b=ent_b,
                    amount_col_a=amt_a,
                    amount_col_b=amt_b,
                    date_col_a=dt_a,
                    date_col_b=dt_b,
                    compare_cols=compare_cols,
                )

                amt_val_b = top_cand.amount_b
                amt_delta = round(amt_val_b - amt_val_a, 2) if (amt_val_a is not None and amt_val_b is not None) else None

                # Check for ambiguity (multiple viable candidates with close scores)
                is_ambiguous = len(candidate_matches) > 1 and (candidate_matches[0].score - candidate_matches[1].score) < 10.0
                status_lbl = (
                    f"Needs Review • Ambiguous ({len(candidate_matches)} Candidates)"
                    if is_ambiguous
                    else f"Needs Review • {int(top_cand.score)}% Match"
                )

                records.append(
                    ReconciliationRecord(
                        id=rec_id,
                        status=RecordStatus.NEEDS_REVIEW.value,
                        status_label=status_lbl,
                        entity=ent_val,
                        reference=ref_val,
                        record_a=r_a,
                        record_b=top_cand.record_b,
                        source_a=source_a_label,
                        source_b=top_cand.source_b,
                        amount_a=amt_val_a,
                        amount_b=amt_val_b,
                        amount_diff=amt_delta,
                        date_a=dt_val_a,
                        date_b=top_cand.date_b,
                        differences=diffs,
                        candidates=candidate_matches,
                        confidence_score=top_cand.score / 100.0,
                    )
                )
            else:
                # No match or viable candidate in B -> Missing in B
                records.append(
                    ReconciliationRecord(
                        id=rec_id,
                        status=RecordStatus.MISSING_IN_B.value,
                        status_label="Missing from Dataset B",
                        entity=ent_val,
                        reference=ref_val,
                        record_a=r_a,
                        record_b=None,
                        source_a=source_a_label,
                        source_b=None,
                        amount_a=amt_val_a,
                        amount_b=None,
                        amount_diff=-amt_val_a if amt_val_a is not None else None,
                        date_a=dt_val_a,
                        date_b=None,
                        differences=[],
                        candidates=[],
                        confidence_score=0.0,
                    )
                )

        if progress_callback:
            progress_callback(80, "Finding orphan records in Dataset B...")

        # 4. Check for records in B that were never matched (Missing in A or Duplicate in B)
        for j, r_b in enumerate(rows_b):
            if id(r_b) not in matched_b_indices:
                rec_id = f"rec_b_{r_b.get('_source_row', j+1)}"
                ref_val = str(r_b.get(key_b, "")) if key_b else f"Row #{r_b.get('_source_row', j+1)}"
                ent_val = str(r_b.get(ent_b, "Unknown Entity")) if ent_b else "Unassigned"
                amt_val_b = Normalizer.normalize_amount(r_b.get(amt_b)) if amt_b else None
                dt_val_b = str(Normalizer.normalize_date(r_b.get(dt_b))) if dt_b else None

                source_b_label = f"Row #{r_b.get('_source_row', j+1)}"
                if r_b.get("_source_sheet"):
                    source_b_label = f"{r_b['_source_sheet']} {source_b_label}"

                raw_k_b = str(r_b.get(key_b, "")).strip() if key_b else ""
                norm_k_b = Normalizer.normalize_id(raw_k_b) if raw_k_b else ""
                is_dup_b = bool(norm_k_b and b_key_counts.get(norm_k_b, 0) > 1)

                status = RecordStatus.DUPLICATE.value if is_dup_b else RecordStatus.MISSING_IN_A.value
                status_label = "Duplicate Key in Dataset B" if is_dup_b else "Missing from Dataset A"

                records.append(
                    ReconciliationRecord(
                        id=rec_id,
                        status=status,
                        status_label=status_label,
                        entity=ent_val,
                        reference=ref_val,
                        record_a=None,
                        record_b=r_b,
                        source_a=None,
                        source_b=source_b_label,
                        amount_a=None,
                        amount_b=amt_val_b,
                        amount_diff=amt_val_b,
                        date_a=None,
                        date_b=dt_val_b,
                        differences=[],
                        candidates=[],
                        confidence_score=0.0,
                    )
                )

        # 5. Apply User Overrides with strict record conservation (no dropped records)
        if user_overrides:
            new_orphan_b_records = []
            for rec in records:
                if rec.id in user_overrides:
                    ovr = user_overrides[rec.id]
                    action = ovr.get("action")
                    if action == "confirm":
                        rec.status = RecordStatus.MATCHED.value
                        rec.status_label = "Confirmed Match"
                        rec.user_override = "confirmed"
                    elif action == "unmatched":
                        # Detach record_b and re-introduce it as an orphan in B so it is never dropped
                        if rec.record_b:
                            orphan_b = rec.record_b
                            new_b_id = f"rec_b_{orphan_b.get('_source_row', 'detached')}"
                            source_b_lbl = f"Row #{orphan_b.get('_source_row', '?')}"
                            if orphan_b.get("_source_sheet"):
                                source_b_lbl = f"{orphan_b['_source_sheet']} {source_b_lbl}"

                            new_orphan_b_records.append(
                                ReconciliationRecord(
                                    id=new_b_id,
                                    status=RecordStatus.MISSING_IN_A.value,
                                    status_label="Missing from Dataset A",
                                    entity=str(orphan_b.get(ent_b, "Unknown Entity")) if ent_b else "Unassigned",
                                    reference=str(orphan_b.get(key_b, "")) if key_b else source_b_lbl,
                                    record_a=None,
                                    record_b=orphan_b,
                                    source_a=None,
                                    source_b=source_b_lbl,
                                    amount_a=None,
                                    amount_b=Normalizer.normalize_amount(orphan_b.get(amt_b)) if amt_b else None,
                                    amount_diff=Normalizer.normalize_amount(orphan_b.get(amt_b)) if amt_b else None,
                                    date_a=None,
                                    date_b=str(Normalizer.normalize_date(orphan_b.get(dt_b))) if dt_b else None,
                                    differences=[],
                                    candidates=[],
                                    confidence_score=0.0,
                                )
                            )

                        rec.status = RecordStatus.MISSING_IN_B.value
                        rec.status_label = "Marked Unmatched"
                        rec.record_b = None
                        rec.source_b = None
                        rec.amount_b = None
                        rec.amount_diff = -rec.amount_a if rec.amount_a else None
                        rec.user_override = "unmatched"

                    elif action == "switch_candidate":
                        target_cid = ovr.get("candidate_id")
                        matching_cands = [c for c in rec.candidates if c.candidate_id == target_cid]
                        if matching_cands:
                            selected_cand = matching_cands[0]
                            # If previously paired, release previous record_b as an orphan
                            old_b = rec.record_b
                            if old_b and id(old_b) != id(selected_cand.record_b):
                                old_b_id = f"rec_b_{old_b.get('_source_row', 'detached')}"
                                old_source_lbl = f"Row #{old_b.get('_source_row', '?')}"
                                if old_b.get("_source_sheet"):
                                    old_source_lbl = f"{old_b['_source_sheet']} {old_source_lbl}"

                                new_orphan_b_records.append(
                                    ReconciliationRecord(
                                        id=old_b_id,
                                        status=RecordStatus.MISSING_IN_A.value,
                                        status_label="Missing from Dataset A",
                                        entity=str(old_b.get(ent_b, "Unknown Entity")) if ent_b else "Unassigned",
                                        reference=str(old_b.get(key_b, "")) if key_b else old_source_lbl,
                                        record_a=None,
                                        record_b=old_b,
                                        source_a=None,
                                        source_b=old_source_lbl,
                                        amount_a=None,
                                        amount_b=Normalizer.normalize_amount(old_b.get(amt_b)) if amt_b else None,
                                        amount_diff=Normalizer.normalize_amount(old_b.get(amt_b)) if amt_b else None,
                                        date_a=None,
                                        date_b=str(Normalizer.normalize_date(old_b.get(dt_b))) if dt_b else None,
                                        differences=[],
                                        candidates=[],
                                        confidence_score=0.0,
                                    )
                                )

                            # Remove candidate from records list if it was previously listed as an orphan
                            target_b_row = selected_cand.record_b.get("_source_row")
                            records = [
                                r for r in records
                                if not (r.record_b and r.record_b.get("_source_row") == target_b_row and r.record_a is None)
                            ]

                            rec.record_b = selected_cand.record_b
                            rec.source_b = selected_cand.source_b
                            rec.amount_b = selected_cand.amount_b
                            rec.date_b = selected_cand.date_b
                            rec.amount_diff = (
                                round(rec.amount_b - rec.amount_a, 2)
                                if (rec.amount_a is not None and rec.amount_b is not None)
                                else None
                            )
                            rec.status = RecordStatus.MATCHED.value
                            rec.status_label = "Confirmed Match"
                            rec.user_override = "switched_candidate"

            records.extend(new_orphan_b_records)

        if progress_callback:
            progress_callback(95, "Calculating metrics and grouping by entity...")

        # 6. Compute summary counts and total variance
        summary = ReconciliationSummary(
            total_a=len(rows_a),
            total_b=len(rows_b),
            total_records=len(records),
        )

        for r in records:
            if r.status == RecordStatus.MATCHED.value:
                summary.matched_count += 1
            elif r.status == RecordStatus.DISCREPANCY.value:
                summary.discrepancies_count += 1
                if r.amount_diff:
                    summary.total_variance += abs(r.amount_diff)
            elif r.status == RecordStatus.NEEDS_REVIEW.value:
                summary.needs_review_count += 1
                if r.amount_diff:
                    summary.total_variance += abs(r.amount_diff)
            elif r.status == RecordStatus.MISSING_IN_B.value:
                summary.missing_in_b_count += 1
                if r.amount_a:
                    summary.total_variance += abs(r.amount_a)
            elif r.status == RecordStatus.MISSING_IN_A.value:
                summary.missing_in_a_count += 1
                if r.amount_b:
                    summary.total_variance += abs(r.amount_b)
            elif r.status == RecordStatus.DUPLICATE.value:
                summary.duplicates_count += 1
                if r.amount_diff:
                    summary.total_variance += abs(r.amount_diff)

        summary.total_variance = round(summary.total_variance, 2)

        # 7. Group records by entity
        grouped_by_entity: dict[str, list[ReconciliationRecord]] = {}
        for r in records:
            ent = r.entity or "Unassigned"
            grouped_by_entity.setdefault(ent, []).append(r)

        if progress_callback:
            progress_callback(100, "Reconciliation complete.")

        return summary, records, grouped_by_entity
