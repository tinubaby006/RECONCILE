import pandas as pd
from reconcile.matching.reconciler import Reconciler
from reconcile.models import ColumnMapping, ColumnRole, RecordStatus


def build_sample_data():
    data_a = [
        # 1. Exact match with no discrepancies
        {"Inv_ID": "INV-100", "Company": "Alpha Corp", "Date": "2024-09-01", "Total": "1000.00"},
        # 2. Exact key with Amount discrepancy (-50.00)
        {"Inv_ID": "INV-200", "Company": "Beta Corp", "Date": "2024-09-05", "Total": "2000.00"},
        # 3. Exact key with Date discrepancy (2 days)
        {"Inv_ID": "INV-300", "Company": "Gamma LLC", "Date": "2024-09-10", "Total": "3000.00"},
        # 4. Fuzzy match / Needs Review (INV-2024-8841 vs REF8841 with amount delta and abbreviation)
        {"Inv_ID": "INV-2024-8841", "Company": "Acme Industrial Solutions Ltd", "Date": "2024-09-15", "Total": "12500.00"},
        # 5. Missing in B
        {"Inv_ID": "INV-500", "Company": "Epsilon Inc", "Date": "2024-09-25", "Total": "5000.00"},
        # 6 & 7. Duplicate keys in A
        {"Inv_ID": "INV-DUP", "Company": "Zeta Ltd", "Date": "2024-09-28", "Total": "600.00"},
        {"Inv_ID": "INV-DUP", "Company": "Zeta Ltd", "Date": "2024-09-28", "Total": "600.00"},
    ]

    data_b = [
        # Counterpart to #1: Exact match
        {"Ref_No": "INV-100", "Beneficiary": "Alpha Corp", "ValDate": "2024-09-01", "Amount": "1000.00"},
        # Counterpart to #2: Amount discrepancy (1,950 vs 2,000)
        {"Ref_No": "INV-200", "Beneficiary": "Beta Corp", "ValDate": "2024-09-05", "Amount": "1950.00"},
        # Counterpart to #3: Date discrepancy (2024-09-12 vs 2024-09-10)
        {"Ref_No": "INV-300", "Beneficiary": "Gamma LLC", "ValDate": "2024-09-12", "Amount": "3000.00"},
        # Primary candidate for #4 (ACME INDUS LTD with amount delta 12,050 vs 12,500)
        {"Ref_No": "REF8841", "Beneficiary": "ACME INDUS LTD", "ValDate": "2024-09-17", "Amount": "12050.00"},
        # Alternative candidate for #4
        {"Ref_No": "REF8841-ALT", "Beneficiary": "ACME INDUSTRIAL", "ValDate": "2024-09-28", "Amount": "12500.00"},
        # Counterpart to #6 & #7: Duplicate key counterpart
        {"Ref_No": "INV-DUP", "Beneficiary": "Zeta Ltd", "ValDate": "2024-09-28", "Amount": "600.00"},
        # 8. Missing in A (Orphan record in B)
        {"Ref_No": "BANK-ORPHAN-01", "Beneficiary": "Mystery Vendor", "ValDate": "2024-09-30", "Amount": "999.00"},
    ]

    df_a = pd.DataFrame(data_a)
    df_a["_source_file"] = "ledger.xlsx"
    df_a["_source_row"] = list(range(2, len(data_a) + 2))
    df_a["_source_sheet"] = "Sheet1"

    df_b = pd.DataFrame(data_b)
    df_b["_source_file"] = "bank.csv"
    df_b["_source_row"] = list(range(2, len(data_b) + 2))
    df_b["_source_sheet"] = None

    mappings = [
        ColumnMapping(col_a="Inv_ID", col_b="Ref_No", role=ColumnRole.MATCH_KEY.value),
        ColumnMapping(col_a="Company", col_b="Beneficiary", role=ColumnRole.ENTITY.value),
        ColumnMapping(col_a="Date", col_b="ValDate", role=ColumnRole.DATE.value),
        ColumnMapping(col_a="Total", col_b="Amount", role=ColumnRole.AMOUNT.value),
    ]

    return df_a, df_b, mappings


def test_reconciliation_workflow():
    df_a, df_b, mappings = build_sample_data()
    reconciler = Reconciler()

    summary, records, grouped = reconciler.reconcile(df_a, df_b, mappings)

    # 1. Verify record statuses
    rec_by_ref = {r.reference: r for r in records}

    # INV-100: Matched
    assert "INV-100" in rec_by_ref
    assert rec_by_ref["INV-100"].status == RecordStatus.MATCHED.value
    assert len(rec_by_ref["INV-100"].differences) == 0

    # INV-200: Discrepancy (-50.00 delta)
    assert "INV-200" in rec_by_ref
    r_200 = rec_by_ref["INV-200"]
    assert r_200.status == RecordStatus.DISCREPANCY.value
    assert r_200.amount_diff == -50.00
    assert any(d.field == "amount" and d.delta == -50.00 for d in r_200.differences)

    # INV-300: Discrepancy due to date
    assert "INV-300" in rec_by_ref
    r_300 = rec_by_ref["INV-300"]
    assert r_300.status == RecordStatus.DISCREPANCY.value
    assert any(d.field == "date" for d in r_300.differences)

    # INV-2024-8841: Needs Review with candidate matches
    assert "INV-2024-8841" in rec_by_ref
    r_8841 = rec_by_ref["INV-2024-8841"]
    assert r_8841.status == RecordStatus.NEEDS_REVIEW.value
    assert len(r_8841.candidates) >= 1
    assert r_8841.candidates[0].score >= 60.0

    # INV-500: Missing in B
    assert "INV-500" in rec_by_ref
    assert rec_by_ref["INV-500"].status == RecordStatus.MISSING_IN_B.value
    assert rec_by_ref["INV-500"].record_b is None

    # INV-DUP: Duplicate
    assert "INV-DUP" in rec_by_ref
    assert rec_by_ref["INV-DUP"].status == RecordStatus.DUPLICATE.value

    # Orphan record in B: Missing in A
    assert "BANK-ORPHAN-01" in rec_by_ref
    r_orphan = rec_by_ref["BANK-ORPHAN-01"]
    assert r_orphan.status == RecordStatus.MISSING_IN_A.value
    assert r_orphan.record_a is None

    # 2. Verify summary metrics
    assert summary.total_a == 7
    assert summary.total_b == 7
    assert summary.matched_count == 1
    assert summary.discrepancies_count == 2
    assert summary.needs_review_count == 1
    assert summary.missing_in_b_count == 1
    assert summary.missing_in_a_count == 2
    assert summary.duplicates_count == 2
    assert summary.total_variance > 0

    # 3. Verify entity grouping
    assert "Acme Industrial Solutions Ltd" in grouped
    assert len(grouped["Acme Industrial Solutions Ltd"]) == 1


def test_user_overrides():
    df_a, df_b, mappings = build_sample_data()
    reconciler = Reconciler()

    # Pass overrides: confirm INV-200 and mark INV-300 as unmatched
    overrides = {
        "rec_a_3": {"action": "confirm"},
        "rec_a_4": {"action": "unmatched"},
    }

    summary, records, _ = reconciler.reconcile(df_a, df_b, mappings, user_overrides=overrides)
    rec_by_id = {r.id: r for r in records}

    assert rec_by_id["rec_a_3"].status == RecordStatus.MATCHED.value
    assert rec_by_id["rec_a_3"].user_override == "confirmed"

    assert rec_by_id["rec_a_4"].status == RecordStatus.MISSING_IN_B.value
    assert rec_by_id["rec_a_4"].user_override == "unmatched"
