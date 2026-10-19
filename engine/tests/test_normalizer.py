from datetime import date
from reconcile.matching.normalizer import Normalizer


def test_normalize_text():
    assert Normalizer.normalize_text("  ACME   CORP  ") == "acme corp"
    assert Normalizer.normalize_text("") == ""
    assert Normalizer.normalize_text(None) == ""


def test_normalize_id():
    assert Normalizer.normalize_id("INV-2024-8841") == "inv20248841"
    assert Normalizer.normalize_id("REF# 8841/HDFC") == "ref8841hdfc"
    assert Normalizer.normalize_id("") == ""
    assert Normalizer.normalize_id(None) == ""


def test_extract_numbers_from_id():
    assert Normalizer.extract_numbers_from_id("INV-2024-8841") == "20248841"
    assert Normalizer.extract_numbers_from_id("REF8841") == "8841"
    assert Normalizer.extract_numbers_from_id("ABC") == ""


def test_normalize_entity_name():
    assert Normalizer.normalize_entity_name("Acme Industrial Solutions Ltd") == "acme industrial"
    assert Normalizer.normalize_entity_name("ACME INDUS LTD") == "acme industrial"
    assert Normalizer.normalize_entity_name("Globex Corp.") == "globex"
    assert Normalizer.normalize_entity_name("Umbrella Corporation LLC") == "umbrella"
    assert Normalizer.normalize_entity_name("Initech Pvt Ltd") == "initech"


def test_normalize_amount():
    assert Normalizer.normalize_amount(12500) == 12500.0
    assert Normalizer.normalize_amount("12500.50") == 12500.50
    assert Normalizer.normalize_amount("₹12,500.00") == 12500.00
    assert Normalizer.normalize_amount("$ 1,234.56") == 1234.56
    assert Normalizer.normalize_amount("(450.00)") == -450.00
    assert Normalizer.normalize_amount("-450.00") == -450.00
    assert Normalizer.normalize_amount("450.00 CR") == -450.00
    assert Normalizer.normalize_amount("450.00 DR") == 450.00
    assert Normalizer.normalize_amount("") is None
    assert Normalizer.normalize_amount(None) is None
    assert Normalizer.normalize_amount("N/A") is None


def test_normalize_date():
    assert Normalizer.normalize_date("2024-09-15") == date(2024, 9, 15)
    assert Normalizer.normalize_date("15/09/2024") == date(2024, 9, 15)
    assert Normalizer.normalize_date("Sep 15, 2024") == date(2024, 9, 15)
    assert Normalizer.normalize_date("2024.09.15") == date(2024, 9, 15)
    assert Normalizer.normalize_date("") is None
    assert Normalizer.normalize_date(None) is None
    assert Normalizer.normalize_date("invalid-date") is None


def test_date_diff_days():
    d1 = date(2024, 9, 15)
    d2 = date(2024, 9, 17)
    assert Normalizer.date_diff_days(d1, d2) == 2
    assert Normalizer.date_diff_days(d2, d1) == 2
    assert Normalizer.date_diff_days(d1, d1) == 0
    assert Normalizer.date_diff_days(d1, None) is None
