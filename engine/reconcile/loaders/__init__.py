from __future__ import annotations

import os
from typing import Optional, Tuple
import pandas as pd

from reconcile.loaders.base import BaseLoader
from reconcile.loaders.csv_loader import CsvLoader
from reconcile.loaders.excel_loader import ExcelLoader
from reconcile.loaders.json_loader import JsonLoader
from reconcile.models import DatasetMeta


def get_loader(file_path: str) -> BaseLoader:
    ext = os.path.splitext(file_path)[1].lower()
    if ext in [".csv", ".tsv", ".txt"]:
        return CsvLoader()
    elif ext in [".xlsx", ".xlsm", ".xls"]:
        return ExcelLoader()
    elif ext in [".json", ".jsonl", ".ndjson"]:
        return JsonLoader()
    else:
        raise ValueError(f"Unsupported file format: {ext}")


def load_dataset(
    file_path: str,
    sheet_name: Optional[str] = None,
    nrows: Optional[int] = None,
) -> Tuple[DatasetMeta, pd.DataFrame]:
    loader = get_loader(file_path)
    return loader.load(file_path, sheet_name=sheet_name, nrows=nrows)


def inspect_dataset(
    file_path: str,
    sheet_name: Optional[str] = None,
) -> DatasetMeta:
    loader = get_loader(file_path)
    return loader.inspect(file_path, sheet_name=sheet_name)
