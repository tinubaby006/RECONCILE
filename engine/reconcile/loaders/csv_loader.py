from __future__ import annotations

import csv
import os
from typing import Optional, Tuple
import pandas as pd

from reconcile.loaders.base import BaseLoader
from reconcile.models import DatasetMeta


class CsvLoader(BaseLoader):
    """Loader for Comma/Tab/Semicolon-Separated Value files."""

    SUPPORTED_ENCODINGS = ["utf-8", "utf-8-sig", "cp1252", "latin1"]

    def _detect_encoding_and_delimiter(self, file_path: str) -> Tuple[str, str]:
        """Detects encoding and delimiter with fallback options."""
        for enc in self.SUPPORTED_ENCODINGS:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    sample = f.read(4096)
                    if not sample:
                        return enc, ","
                    try:
                        dialect = csv.Sniffer().sniff(sample, delimiters=",\t;|")
                        return enc, dialect.delimiter
                    except Exception:
                        # Fallback heuristic
                        lines = sample.splitlines()
                        first_line = lines[0] if lines else ""
                        counts = {
                            ",": first_line.count(","),
                            "\t": first_line.count("\t"),
                            ";": first_line.count(";"),
                            "|": first_line.count("|"),
                        }
                        best_delim = max(counts, key=counts.get)
                        return enc, best_delim if counts[best_delim] > 0 else ","
            except UnicodeDecodeError:
                continue

        return "utf-8", ","

    def inspect(self, file_path: str, **kwargs) -> DatasetMeta:
        meta, _ = self.load(file_path, nrows=50)
        return meta

    def load(
        self, file_path: str, nrows: Optional[int] = None, **kwargs
    ) -> Tuple[DatasetMeta, pd.DataFrame]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        encoding, delimiter = self._detect_encoding_and_delimiter(file_path)

        df = pd.read_csv(
            file_path,
            delimiter=delimiter,
            encoding=encoding,
            nrows=nrows,
            dtype=str,  # Load as strings initially to preserve exact values and leading zeroes
            keep_default_na=False,
        )

        file_name = os.path.basename(file_path)
        # 1-based row tracking: header is row 1, data rows start at row 2
        df["_source_file"] = file_name
        df["_source_row"] = (df.index + 2).astype(int)
        df["_source_sheet"] = None

        meta = self.build_metadata(file_path=file_path, file_type="csv", df=df)
        return meta, df
