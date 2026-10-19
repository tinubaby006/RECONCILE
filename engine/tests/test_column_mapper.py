from reconcile.mapping.column_mapper import ColumnMapper
from reconcile.models import ColumnMeta, DatasetMeta, ColumnRole


def test_column_mapper_suggestions():
    meta_a = DatasetMeta(
        file_path="ledger.xlsx",
        file_name="ledger.xlsx",
        file_type="xlsx",
        total_rows=10,
        columns=[
            ColumnMeta(name="Invoice_Ref", inferred_type="id", non_null_count=10, unique_count=10, sample_values=["INV-2024-8841"]),
            ColumnMeta(name="Beneficiary_Name", inferred_type="string", non_null_count=10, unique_count=8, sample_values=["Acme Industrial Solutions Ltd"]),
            ColumnMeta(name="Invoice_Date", inferred_type="date", non_null_count=10, unique_count=10, sample_values=["2024-09-15"]),
            ColumnMeta(name="Gross_Amount", inferred_type="numeric", non_null_count=10, unique_count=10, sample_values=["12500.00"]),
            ColumnMeta(name="Internal_Notes", inferred_type="string", non_null_count=5, unique_count=5, sample_values=["Checked"]),
        ]
    )

    meta_b = DatasetMeta(
        file_path="bank.csv",
        file_name="bank.csv",
        file_type="csv",
        total_rows=10,
        columns=[
            ColumnMeta(name="Ref_No", inferred_type="id", non_null_count=10, unique_count=10, sample_values=["REF8841"]),
            ColumnMeta(name="Entity", inferred_type="string", non_null_count=10, unique_count=8, sample_values=["ACME INDUS LTD"]),
            ColumnMeta(name="Value_Date", inferred_type="date", non_null_count=10, unique_count=10, sample_values=["2024-09-17"]),
            ColumnMeta(name="Amount", inferred_type="numeric", non_null_count=10, unique_count=10, sample_values=["12050.00"]),
            ColumnMeta(name="Bank_Branch", inferred_type="string", non_null_count=10, unique_count=3, sample_values=["Downtown"]),
        ]
    )

    mappings = ColumnMapper.suggest_mappings(meta_a, meta_b)
    mapped_dict = {m.col_a: m for m in mappings}

    # Invoice_Ref should map to Ref_No with role match_key
    assert "Invoice_Ref" in mapped_dict
    assert mapped_dict["Invoice_Ref"].col_b == "Ref_No"
    assert mapped_dict["Invoice_Ref"].role == ColumnRole.MATCH_KEY.value

    # Beneficiary_Name should map to Entity with role entity
    assert mapped_dict["Beneficiary_Name"].col_b == "Entity"
    assert mapped_dict["Beneficiary_Name"].role == ColumnRole.ENTITY.value

    # Invoice_Date should map to Value_Date with role date
    assert mapped_dict["Invoice_Date"].col_b == "Value_Date"
    assert mapped_dict["Invoice_Date"].role == ColumnRole.DATE.value

    # Gross_Amount should map to Amount with role amount
    assert mapped_dict["Gross_Amount"].col_b == "Amount"
    assert mapped_dict["Gross_Amount"].role == ColumnRole.AMOUNT.value

    # Internal_Notes should be unmapped
    assert mapped_dict["Internal_Notes"].status == "unmapped"
    assert mapped_dict["Internal_Notes"].col_b is None
