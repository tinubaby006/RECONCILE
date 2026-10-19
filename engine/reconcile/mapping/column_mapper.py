from __future__ import annotations

from typing import Optional
from rapidfuzz import fuzz

from reconcile.models import ColumnMapping, ColumnMeta, ColumnRole, DatasetMeta


class ColumnMapper:
    """Heuristic mapper to automatically suggest matching columns between two datasets."""

    ROLE_KEYWORDS = {
        ColumnRole.MATCH_KEY: [
            "invoice", "inv", "ref", "reference", "id", "trans_id", "transaction",
            "voucher", "doc_no", "bill_no", "key", "number"
        ],
        ColumnRole.ENTITY: [
            "company", "entity", "beneficiary", "customer", "vendor", "client",
            "party", "name", "payee", "payer", "account_name"
        ],
        ColumnRole.DATE: [
            "date", "trans_date", "value_date", "invoice_date", "doc_date",
            "posting_date", "day", "timestamp"
        ],
        ColumnRole.AMOUNT: [
            "amount", "gross", "net", "total", "balance", "value", "sum",
            "debit", "credit", "price", "subtotal"
        ],
    }

    @classmethod
    def _clean_header(cls, name: str) -> str:
        return name.lower().replace("_", " ").replace("-", " ").replace(".", " ").strip()

    @classmethod
    def _infer_role(cls, col_name: str, col_type: str) -> str:
        """Infers the most probable reconciliation role for a column."""
        cleaned = cls._clean_header(col_name)

        # 1. Check Amount (must be numeric or have amount keywords)
        if col_type == "numeric" or any(kw in cleaned for kw in cls.ROLE_KEYWORDS[ColumnRole.AMOUNT]):
            if any(kw in cleaned for kw in cls.ROLE_KEYWORDS[ColumnRole.AMOUNT]):
                return ColumnRole.AMOUNT.value

        # 2. Check Date
        if col_type == "date" or any(kw in cleaned for kw in cls.ROLE_KEYWORDS[ColumnRole.DATE]):
            return ColumnRole.DATE.value

        # 3. Check Match Key
        if any(kw in cleaned for kw in cls.ROLE_KEYWORDS[ColumnRole.MATCH_KEY]):
            return ColumnRole.MATCH_KEY.value

        # 4. Check Entity
        if any(kw in cleaned for kw in cls.ROLE_KEYWORDS[ColumnRole.ENTITY]):
            return ColumnRole.ENTITY.value

        if col_type == "numeric":
            return ColumnRole.AMOUNT.value

        return ColumnRole.COMPARE.value

    @classmethod
    def _compute_column_similarity(
        cls, col_a: ColumnMeta, col_b: ColumnMeta
    ) -> float:
        """Computes a match score (0.0 - 1.0) between two columns based on name, type, and samples."""
        name_a_clean = cls._clean_header(col_a.name)
        name_b_clean = cls._clean_header(col_b.name)

        # Name similarity (weight: 0.5)
        name_ratio = fuzz.token_sort_ratio(name_a_clean, name_b_clean) / 100.0

        # Keyword overlap bonus
        role_a = cls._infer_role(col_a.name, col_a.inferred_type)
        role_b = cls._infer_role(col_b.name, col_b.inferred_type)
        role_bonus = 0.25 if role_a == role_b and role_a != ColumnRole.COMPARE.value else 0.0

        # Type compatibility (weight: 0.25)
        type_score = 0.25 if col_a.inferred_type == col_b.inferred_type else 0.0

        # Sample value similarity bonus
        sample_bonus = 0.0
        if col_a.sample_values and col_b.sample_values:
            overlap = set(str(s).lower() for s in col_a.sample_values) & set(
                str(s).lower() for s in col_b.sample_values
            )
            if overlap:
                sample_bonus = 0.15

        total_score = min(1.0, (name_ratio * 0.5) + type_score + role_bonus + sample_bonus)
        return round(total_score, 2)

    @classmethod
    def suggest_mappings(
        cls, meta_a: DatasetMeta, meta_b: DatasetMeta
    ) -> list[ColumnMapping]:
        """Generates suggested 1-to-1 column mappings from Dataset A to Dataset B."""
        mappings: list[ColumnMapping] = []
        available_b_cols = list(meta_b.columns)

        # Track which roles have already been assigned primary status
        assigned_roles: dict[str, str] = {}

        for col_a in meta_a.columns:
            sample_a_str = ", ".join(str(s) for s in col_a.sample_values[:2]) if col_a.sample_values else None
            best_match: Optional[ColumnMeta] = None
            best_score = 0.0

            for col_b in available_b_cols:
                score = cls._compute_column_similarity(col_a, col_b)
                if score > best_score:
                    best_score = score
                    best_match = col_b

            # Threshold for automatic mapping suggestion is 0.45
            if best_match and best_score >= 0.45:
                role = cls._infer_role(col_a.name, col_a.inferred_type)
                sample_b_str = ", ".join(str(s) for s in best_match.sample_values[:2]) if best_match.sample_values else None

                # Ensure only one primary match_key, entity, amount, date by default
                if role in [ColumnRole.MATCH_KEY.value, ColumnRole.AMOUNT.value, ColumnRole.DATE.value, ColumnRole.ENTITY.value]:
                    if role in assigned_roles:
                        role = ColumnRole.COMPARE.value
                    else:
                        assigned_roles[role] = col_a.name

                mappings.append(
                    ColumnMapping(
                        col_a=col_a.name,
                        col_b=best_match.name,
                        role=role,
                        confidence=best_score,
                        status="mapped",
                        sample_a=sample_a_str,
                        sample_b=sample_b_str,
                    )
                )
                available_b_cols.remove(best_match)
            else:
                role = cls._infer_role(col_a.name, col_a.inferred_type)
                mappings.append(
                    ColumnMapping(
                        col_a=col_a.name,
                        col_b=None,
                        role=role,
                        confidence=0.0,
                        status="unmapped",
                        sample_a=sample_a_str,
                        sample_b=None,
                    )
                )

        return mappings
