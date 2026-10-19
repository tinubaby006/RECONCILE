from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Any, Optional, Tuple
import pandas as pd
from dateutil.parser import parse as parse_date

from reconcile.models import ColumnMeta, DatasetMeta


class BaseLoader(ABC):
    """Abstract base class for all dataset loaders."""

    @abstractmethod
    def load(
        self, file_path: str, **kwargs
    ) -> Tuple[DatasetMeta, pd.DataFrame]:
        """Loads dataset from file_path into a pandas DataFrame and returns metadata and data."""
        pass

    @abstractmethod
    def inspect(self, file_path: str, **kwargs) -> DatasetMeta:
        """Inspects file structure without full parsing where possible."""
        pass

    @staticmethod
    def infer_column_type(series: pd.Series) -> str:
        """Heuristically infers the general column type: 'numeric', 'date', 'id', or 'string'."""
        clean_series = series.dropna().astype(str).str.strip()
        if clean_series.empty:
            return "string"

        # Check numeric
        numeric_count = 0
        for val in clean_series.head(50):
            # Strip standard currency symbols and commas
            v = val.replace("$", "").replace("€", "").replace("£", "").replace("₹", "").replace(",", "")
            # check parenthesized negative
            if v.startswith("(") and v.endswith(")"):
                v = "-" + v[1:-1]
            try:
                float(v)
                numeric_count += 1
            except ValueError:
                pass

        if numeric_count >= min(len(clean_series), 50) * 0.8:
            return "numeric"

        # Check date
        date_count = 0
        for val in clean_series.head(50):
            if len(val) >= 6 and any(c in val for c in ["-", "/", ".", " "]):
                try:
                    parse_date(val, fuzzy=False)
                    date_count += 1
                except Exception:
                    pass

        if date_count >= min(len(clean_series), 50) * 0.8:
            return "date"

        # Check ID (alphanumeric pattern, high uniqueness)
        if series.name:
            col_name_lower = str(series.name).lower()
            if any(term in col_name_lower for term in ["id", "ref", "key", "num", "code", "invoice", "trans"]):
                return "id"

        return "string"

    @classmethod
    def build_metadata(
        cls,
        file_path: str,
        file_type: str,
        df: pd.DataFrame,
        sheets: Optional[list[str]] = None,
        active_sheet: Optional[str] = None,
    ) -> DatasetMeta:
        """Builds DatasetMeta from a loaded DataFrame."""
        file_name = os.path.basename(file_path)
        columns_meta: list[ColumnMeta] = []

        # Filter out internal tracking columns
        data_cols = [c for c in df.columns if not str(c).startswith("_source_")]

        for col in data_cols:
            series = df[col]
            non_null = int(series.dropna().count())
            unique_count = int(series.nunique())
            inferred = cls.infer_column_type(series)

            # Collect up to 3 non-empty distinct samples
            samples: list[Any] = []
            for val in series.dropna():
                str_val = str(val).strip()
                if str_val and str_val not in ["nan", "None", "NULL"]:
                    if str_val not in samples:
                        samples.append(str_val)
                if len(samples) >= 3:
                    break

            columns_meta.append(
                ColumnMeta(
                    name=str(col),
                    inferred_type=inferred,
                    non_null_count=non_null,
                    unique_count=unique_count,
                    sample_values=samples,
                )
            )

        return DatasetMeta(
            file_path=file_path,
            file_name=file_name,
            file_type=file_type,
            total_rows=len(df),
            sheets=sheets or [],
            active_sheet=active_sheet,
            columns=columns_meta,
        )
