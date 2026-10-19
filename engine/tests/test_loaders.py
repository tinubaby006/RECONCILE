import json
import tempfile
import os
import openpyxl
import pandas as pd
from reconcile.loaders import inspect_dataset, load_dataset
from reconcile.loaders.csv_loader import CsvLoader
from reconcile.loaders.excel_loader import ExcelLoader
from reconcile.loaders.json_loader import JsonLoader


def test_csv_loader():
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, newline="") as f:
        f.write("Invoice_Ref,Entity,Date,Amount\n")
        f.write("INV-001,Acme Corp,2024-09-01,1500.00\n")
        f.write("INV-002,Globex,2024-09-02,2500.50\n")
        temp_path = f.name

    try:
        loader = CsvLoader()
        meta, df = loader.load(temp_path)

        assert meta.total_rows == 2
        assert meta.file_type == "csv"
        assert len(meta.columns) == 4
        # Verify 1-based row numbering: header is row 1, data rows start at row 2
        assert list(df["_source_row"]) == [2, 3]
        assert df.loc[0, "Invoice_Ref"] == "INV-001"
        assert df.loc[1, "Amount"] == "2500.50"
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_tsv_loader():
    with tempfile.NamedTemporaryFile("w", suffix=".tsv", delete=False, newline="") as f:
        f.write("id\tname\tval\n")
        f.write("1\tAlpha\t100\n")
        f.write("2\tBeta\t200\n")
        temp_path = f.name

    try:
        meta, df = load_dataset(temp_path)
        assert meta.total_rows == 2
        assert df.loc[0, "name"] == "Alpha"
        assert list(df["_source_row"]) == [2, 3]
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_excel_loader():
    wb = openpyxl.Workbook()
    ws1 = wb.active
    ws1.title = "Ledger"
    ws1.append(["Ref", "Vendor", "Total"])
    ws1.append(["L-101", "Supplier A", "5000.00"])
    ws1.append(["L-102", "Supplier B", "7500.00"])

    ws2 = wb.create_sheet(title="Archived")
    ws2.append(["Ref", "Notes"])
    ws2.append(["OLD-1", "Archived row"])

    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
        temp_path = f.name
    wb.save(temp_path)
    wb.close()

    try:
        loader = ExcelLoader()
        meta = loader.inspect(temp_path)
        assert "Ledger" in meta.sheets
        assert "Archived" in meta.sheets
        assert meta.active_sheet == "Ledger"

        # Load specific sheet
        meta_arch, df_arch = loader.load(temp_path, sheet_name="Archived")
        assert meta_arch.active_sheet == "Archived"
        assert meta_arch.total_rows == 1
        assert df_arch.loc[0, "Ref"] == "OLD-1"
        assert df_arch.loc[0, "_source_row"] == 2
        assert df_arch.loc[0, "_source_sheet"] == "Archived"
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_json_loader():
    data = [
        {"trans_id": "T1", "company": "Initech", "amount": 1000},
        {"trans_id": "T2", "company": "Umbrella", "amount": 2000},
    ]
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        temp_path = f.name

    try:
        loader = JsonLoader()
        meta, df = loader.load(temp_path)
        assert meta.total_rows == 2
        assert meta.file_type == "json"
        assert df.loc[0, "trans_id"] == "T1"
        assert list(df["_source_row"]) == [1, 2]
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_json_wrapped_loader():
    data = {
        "status": "success",
        "records": [
            {"id": "R1", "desc": "Item 1"},
            {"id": "R2", "desc": "Item 2"},
        ]
    }
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        temp_path = f.name

    try:
        meta, df = load_dataset(temp_path)
        assert meta.total_rows == 2
        assert df.loc[0, "id"] == "R1"
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
