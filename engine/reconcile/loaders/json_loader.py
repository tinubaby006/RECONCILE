from __future__ import annotations

import json
import os
from typing import Any, Optional, Tuple
import pandas as pd

from reconcile.loaders.base import BaseLoader
from reconcile.models import DatasetMeta


class JsonLoader(BaseLoader):
    """Loader for JSON arrays, nested records, and JSON-Lines files."""

    def _extract_records(self, data: Any) -> list[dict[str, Any]]:
        """Extracts a list of flat or semi-flat dictionary records from parsed JSON."""
        if isinstance(data, list):
            records = [item for item in data if isinstance(item, dict)]
            if records:
                return records
            raise ValueError("JSON array does not contain object records.")

        if isinstance(data, dict):
            # Check common wrapper keys
            for key in ["records", "data", "items", "results", "rows"]:
                if key in data and isinstance(data[key], list):
                    return self._extract_records(data[key])

            # Check if dict values are themselves records
            sub_dicts = [v for v in data.values() if isinstance(v, dict)]
            if len(sub_dicts) > 1:
                return sub_dicts

            # If it's a single record, return as a 1-item list
            return [data]

        raise ValueError("Unsupported JSON structure: expected list of records or dictionary.")

    def inspect(self, file_path: str, **kwargs) -> DatasetMeta:
        meta, _ = self.load(file_path, nrows=50)
        return meta

    def load(
        self, file_path: str, nrows: Optional[int] = None, **kwargs
    ) -> Tuple[DatasetMeta, pd.DataFrame]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        records: list[dict[str, Any]] = []
        # Try standard JSON first
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                records = self._extract_records(data)
        except Exception:
            # Fallback to JSONL / NDJSON
            records = []
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line_str = line.strip()
                    if line_str:
                        records.append(json.loads(line_str))

        if nrows is not None:
            records = records[:nrows]

        # Normalize nested structures into flattened columns
        df = pd.json_normalize(records)
        # Convert all to string to preserve original formatting
        df = df.astype(str).replace("nan", "")

        file_name = os.path.basename(file_path)
        # 1-based index for JSON records
        df["_source_file"] = file_name
        df["_source_row"] = (df.index + 1).astype(int)
        df["_source_sheet"] = None

        meta = self.build_metadata(file_path=file_path, file_type="json", df=df)
        return meta, df
