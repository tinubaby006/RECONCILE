import math
import numpy as np
import pandas as pd
from datetime import date

from reconcile.matching.matcher import Matcher
from reconcile.matching.normalizer import Normalizer
from reconcile.matching.reconciler import Reconciler
from reconcile.models import ColumnMapping, ColumnRole, RecordStatus


def test_no_false_positive_on_shared_digits():
    """Verify that records sharing numeric digits (e.g. PO-2024 and INVOICE-2024)

    never establish an automatic confirmed match, even if amounts and entities are similar.
    """
    df_a = pd.DataFrame([
        {"ID": "PO-2024", "Vendor": "Supplier Alpha", "Amount": "100.00"}
    ])
    df_a["_source_file"] = "ledger.csv"
    df_a["_source_row"] = [2]
    df_a["_source_sheet"] = None

    df_b = pd.DataFrame([
        {"Ref": "INVOICE-2024", "Vendor": "Supplier Alpha", "Amount": "100.00"}
    ])
    df_b["_source_file"] = "bank.csv"
    df_b["_source_row"] = [2]
    df_b["_source_sheet"] = None

    mappings = [
        ColumnMapping(col_a="ID", col_b="Ref", role=ColumnRole.MATCH_KEY.value),
        ColumnMapping(col_a="Vendor", col_b="Vendor", role=ColumnRole.ENTITY.value),
        ColumnMapping(col_a="Amount", col_b="Amount", role=ColumnRole.AMOUNT.value),
    ]

    reconciler = Reconciler()
    summary, records, _ = reconciler.reconcile(df_a, df_b, mappings)

    assert len(records) == 1
    # MUST NOT be automatically confirmed as MATCHED!
    assert records[0].status != RecordStatus.MATCHED.value
    # It must be marked as NEEDS_REVIEW so the user makes the decision
    assert records[0].status == RecordStatus.NEEDS_REVIEW.value
    assert "Needs Review" in records[0].status_label


def test_null_and_nan_keys_never_match():
    """Verify that two records with NaN, None, or empty keys never match each other."""
    df_a = pd.DataFrame([
        {"Key": np.nan, "Company": "Acme", "Amount": "500.00"},
        {"Key": "", "Company": "Beta", "Amount": "600.00"},
        {"Key": "None", "Company": "Gamma", "Amount": "700.00"},
    ])
    df_a["_source_file"] = "a.csv"
    df_a["_source_row"] = [2, 3, 4]
    df_a["_source_sheet"] = None

    df_b = pd.DataFrame([
        {"Key": np.nan, "Company": "Acme", "Amount": "500.00"},
        {"Key": "-", "Company": "Beta", "Amount": "600.00"},
    ])
    df_b["_source_file"] = "b.csv"
    df_b["_source_row"] = [2, 3]
    df_b["_source_sheet"] = None

    mappings = [
        ColumnMapping(col_a="Key", col_b="Key", role=ColumnRole.MATCH_KEY.value),
        ColumnMapping(col_a="Company", col_b="Company", role=ColumnRole.ENTITY.value),
        ColumnMapping(col_a="Amount", col_b="Amount", role=ColumnRole.AMOUNT.value),
    ]

    reconciler = Reconciler()
    summary, records, _ = reconciler.reconcile(df_a, df_b, mappings)

    # None of the unkeyed records should be matched on empty keys!
    exact_matches = [r for r in records if r.status == RecordStatus.MATCHED.value and not r.candidates]
    assert len(exact_matches) == 0


def test_normalizer_edge_cases():
    """Verify edge case handling for amounts, dates, and identifiers."""
    # Amount tests
    assert Normalizer.normalize_amount(float("nan")) is None
    assert Normalizer.normalize_amount(None) is None
    assert Normalizer.normalize_amount("NaN") is None
    assert Normalizer.normalize_amount("( -450.00 )") == -450.00
    assert Normalizer.normalize_amount("(₹ 12,500.00)") == -12500.00
    assert Normalizer.normalize_amount("$ 1,000.00 CR") == -1000.00
    assert Normalizer.normalize_amount("€ 500.00 DR") == 500.00
    assert Normalizer.normalize_amount("0.00") == 0.0
    assert Normalizer.normalize_amount(0) == 0.0

    # Date sanity tests
    assert Normalizer.normalize_date("REF8841") is None
    assert Normalizer.normalize_date("12345") is None
    assert Normalizer.normalize_date("2024-09-15") == date(2024, 9, 15)
    assert Normalizer.normalize_date("15/09/2024") == date(2024, 9, 15)
    assert Normalizer.normalize_date("31-12-2023") == date(2023, 12, 31)
    assert Normalizer.normalize_date(np.nan) is None
    assert Normalizer.normalize_date("") is None

    # ID tests
    assert Normalizer.normalize_id(np.nan) == ""
    assert Normalizer.normalize_id(None) == ""
    assert Normalizer.normalize_id("nan") == ""
    assert Normalizer.normalize_id("null") == ""
    assert Normalizer.normalize_id("INV-00123") == "inv00123"


def test_duplicate_keys_in_dataset_b():
    """Verify that duplicate keys in Dataset B are accurately detected as duplicates

    and not mislabeled as 'Missing from Dataset A'.
    """
    df_a = pd.DataFrame([
        {"Key": "K1", "Amount": "100.00"}
    ])
    df_a["_source_file"] = "a.csv"
    df_a["_source_row"] = [2]
    df_a["_source_sheet"] = None

    df_b = pd.DataFrame([
        {"Key": "K1", "Amount": "100.00"},
        {"Key": "K1", "Amount": "100.00"},  # Duplicate key in B
    ])
    df_b["_source_file"] = "b.csv"
    df_b["_source_row"] = [2, 3]
    df_b["_source_sheet"] = None

    mappings = [
        ColumnMapping(col_a="Key", col_b="Key", role=ColumnRole.MATCH_KEY.value),
        ColumnMapping(col_a="Amount", col_b="Amount", role=ColumnRole.AMOUNT.value),
    ]

    reconciler = Reconciler()
    summary, records, _ = reconciler.reconcile(df_a, df_b, mappings)

    # Both records associated with K1 should be flagged as DUPLICATE
    dup_records = [r for r in records if r.status == RecordStatus.DUPLICATE.value]
    assert len(dup_records) == 2
    # Neither should be labeled MISSING_IN_A
    missing_a = [r for r in records if r.status == RecordStatus.MISSING_IN_A.value]
    assert len(missing_a) == 0


def test_record_conservation_on_unmatched_override():
    """Verify that when a user marks a candidate match as 'unmatched', the detached

    record from Dataset B is NOT silently dropped, but preserved as an orphan in B.
    """
    df_a = pd.DataFrame([
        {"Key": "INV-A", "Company": "Acme Corp", "Amount": "1000.00"}
    ])
    df_a["_source_file"] = "a.csv"
    df_a["_source_row"] = [2]
    df_a["_source_sheet"] = "Ledger"

    df_b = pd.DataFrame([
        {"Key": "REF-B", "Company": "Acme Inc", "Amount": "1000.00"}
    ])
    df_b["_source_file"] = "b.csv"
    df_b["_source_row"] = [2]
    df_b["_source_sheet"] = "Statement"

    mappings = [
        ColumnMapping(col_a="Key", col_b="Key", role=ColumnRole.MATCH_KEY.value),
        ColumnMapping(col_a="Company", col_b="Company", role=ColumnRole.ENTITY.value),
        ColumnMapping(col_a="Amount", col_b="Amount", role=ColumnRole.AMOUNT.value),
    ]

    reconciler = Reconciler()

    # 1. Run without override -> 1 Needs Review record
    summary_1, records_1, _ = reconciler.reconcile(df_a, df_b, mappings)
    assert len(records_1) == 1
    assert records_1[0].status == RecordStatus.NEEDS_REVIEW.value

    # 2. Run with override: mark as unmatched
    overrides = {"rec_a_2": {"action": "unmatched"}}
    summary_2, records_2, _ = reconciler.reconcile(df_a, df_b, mappings, user_overrides=overrides)

    # After unmatching, there must be TWO records:
    # 1) Record A: Missing in B
    # 2) Record B: Missing in A
    assert len(records_2) == 2

    rec_a = next(r for r in records_2 if r.id == "rec_a_2")
    assert rec_a.status == RecordStatus.MISSING_IN_B.value
    assert rec_a.record_a is not None
    assert rec_a.record_b is None
    assert rec_a.source_a == "Ledger Row #2"

    rec_b = next(r for r in records_2 if r.id != "rec_a_2")
    assert rec_b.status == RecordStatus.MISSING_IN_A.value
    assert rec_b.record_b is not None
    assert rec_b.record_a is None
    assert rec_b.source_b == "Statement Row #2"


def test_comprehensive_realistic_reconciliation_fixture():
    """Comprehensive fixture testing all 7 reconciliation outcomes simultaneously:

    1. Exact Match (Clean)
    2. Discrepancy (Amount variance)
    3. Discrepancy (Date variance)
    4. Needs Review (Candidate counterpart with score)
    5. Duplicate in A
    6. Duplicate in B
    7. Missing in B
    8. Missing in A
    """
    data_a = [
        # 1. Clean Exact Match
        {"ID": "INV-001", "Entity": "Apple Inc", "Date": "2024-09-01", "Amount": "1000.00"},
        # 2. Amount Discrepancy (-25.00)
        {"ID": "INV-002", "Entity": "Boeing Co", "Date": "2024-09-02", "Amount": "5000.00"},
        # 3. Date Discrepancy (3 days)
        {"ID": "INV-003", "Entity": "Cisco Systems", "Date": "2024-09-05", "Amount": "3000.00"},
        # 4. Needs Review (Different key, fuzzy entity, exact amount)
        {"ID": "INV-004", "Entity": "Delta Airlines Services", "Date": "2024-09-10", "Amount": "4500.00"},
        # 5. Duplicate in A (part 1)
        {"ID": "INV-DUP-A", "Entity": "Echo Corp", "Date": "2024-09-15", "Amount": "700.00"},
        # 6. Duplicate in A (part 2)
        {"ID": "INV-DUP-A", "Entity": "Echo Corp", "Date": "2024-09-15", "Amount": "700.00"},
        # 7. Missing in B
        {"ID": "INV-007", "Entity": "Foxtrot Ltd", "Date": "2024-09-20", "Amount": "800.00"},
    ]

    data_b = [
        # Counterpart to #1
        {"Ref": "INV-001", "Client": "Apple Inc", "TxDate": "2024-09-01", "Total": "1000.00"},
        # Counterpart to #2 (Amount is 4975.00 instead of 5000.00)
        {"Ref": "INV-002", "Client": "Boeing Co", "TxDate": "2024-09-02", "Total": "4975.00"},
        # Counterpart to #3 (Date is 2024-09-08 instead of 2024-09-05)
        {"Ref": "INV-003", "Client": "Cisco Systems", "TxDate": "2024-09-08", "Total": "3000.00"},
        # Candidate for #4 (REF-DELTA-99, Delta Airlines)
        {"Ref": "REF-DELTA-99", "Client": "Delta Airlines", "TxDate": "2024-09-11", "Total": "4500.00"},
        # Counterpart to #5 & #6
        {"Ref": "INV-DUP-A", "Client": "Echo Corp", "TxDate": "2024-09-15", "Total": "700.00"},
        # 8. Duplicate in B (two rows with INV-DUP-B, not in A)
        {"Ref": "INV-DUP-B", "Client": "Golf LLC", "TxDate": "2024-09-25", "Total": "250.00"},
        {"Ref": "INV-DUP-B", "Client": "Golf LLC", "TxDate": "2024-09-25", "Total": "250.00"},
        # 9. Missing in A (Orphan in B)
        {"Ref": "REF-ORPHAN-B", "Client": "Hotel Enterprises", "TxDate": "2024-09-30", "Total": "900.00"},
    ]

    df_a = pd.DataFrame(data_a)
    df_a["_source_file"] = "ledger.xlsx"
    df_a["_source_row"] = list(range(2, len(data_a) + 2))
    df_a["_source_sheet"] = "Ledger"

    df_b = pd.DataFrame(data_b)
    df_b["_source_file"] = "bank.csv"
    df_b["_source_row"] = list(range(2, len(data_b) + 2))
    df_b["_source_sheet"] = None

    mappings = [
        ColumnMapping(col_a="ID", col_b="Ref", role=ColumnRole.MATCH_KEY.value),
        ColumnMapping(col_a="Entity", col_b="Client", role=ColumnRole.ENTITY.value),
        ColumnMapping(col_a="Date", col_b="TxDate", role=ColumnRole.DATE.value),
        ColumnMapping(col_a="Amount", col_b="Total", role=ColumnRole.AMOUNT.value),
    ]

    reconciler = Reconciler()
    summary, records, grouped = reconciler.reconcile(df_a, df_b, mappings)

    by_ref = {r.reference: r for r in records}

    # 1. Clean Match
    assert by_ref["INV-001"].status == RecordStatus.MATCHED.value
    assert len(by_ref["INV-001"].differences) == 0

    # 2. Amount Discrepancy
    assert by_ref["INV-002"].status == RecordStatus.DISCREPANCY.value
    assert by_ref["INV-002"].amount_diff == -25.00

    # 3. Date Discrepancy
    assert by_ref["INV-003"].status == RecordStatus.DISCREPANCY.value
    assert any(d.field == "date" and d.delta == 3.0 for d in by_ref["INV-003"].differences)

    # 4. Needs Review (Candidate)
    assert by_ref["INV-004"].status == RecordStatus.NEEDS_REVIEW.value
    assert len(by_ref["INV-004"].candidates) >= 1

    # 5. Duplicates in A
    assert by_ref["INV-DUP-A"].status == RecordStatus.DUPLICATE.value

    # 6. Duplicates in B
    assert by_ref["INV-DUP-B"].status == RecordStatus.DUPLICATE.value

    # 7. Missing in B
    assert by_ref["INV-007"].status == RecordStatus.MISSING_IN_B.value

    # 8. Missing in A (Orphan)
    assert by_ref["REF-ORPHAN-B"].status == RecordStatus.MISSING_IN_A.value

    # 9. Verify traceability
    for r in records:
        if r.record_a:
            assert r.source_a.startswith("Ledger Row #")
            assert "_source_row" in r.record_a
        if r.record_b:
            assert r.source_b.startswith("Row #")
            assert "_source_row" in r.record_b

    # 10. Summary verification
    assert summary.total_a == 7
    assert summary.total_b == 8
    assert summary.matched_count == 1
    assert summary.discrepancies_count == 2
    assert summary.needs_review_count == 1
    assert summary.missing_in_b_count == 1
    assert summary.missing_in_a_count == 1
    assert summary.duplicates_count == 4  # 2 in A + 2 in B
