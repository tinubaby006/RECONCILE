from __future__ import annotations

import math
import re
from datetime import date, datetime
from typing import Any, Optional
from dateutil.parser import parse as parse_date


class Normalizer:
    """Safe, deterministic normalization utilities for text, numbers, and dates."""

    # Common corporate entity designators
    ENTITY_SUFFIXES = [
        r"\b(pvt\s+ltd|private\s+limited|pvt|ltd|limited)\b",
        r"\b(inc|incorporated|corp|corporation|llc|llp|gmbh|sa|plc)\b",
        r"\b(solutions|services|enterprises|technologies|group|holdings)\b",
        r"\b(co|company)\b",
    ]

    NULL_STRINGS = {"nan", "none", "null", "undefined", "n/a", "na", "-", ""}

    @classmethod
    def is_null_or_empty(cls, val: Any) -> bool:
        """Checks whether a value is None, NaN, or a null-like placeholder string."""
        if val is None:
            return True
        if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
            return True
        s = str(val).strip().lower()
        return s in cls.NULL_STRINGS

    @classmethod
    def normalize_text(cls, text: Optional[str]) -> str:
        """Standard text normalization: strips extra whitespace, lowercases. Returns empty string for nulls."""
        if cls.is_null_or_empty(text):
            return ""
        return " ".join(str(text).strip().split()).lower()

    @classmethod
    def normalize_id(cls, text: Optional[str]) -> str:
        """Normalizes identifiers/keys: removes symbols and whitespace. Returns empty string for nulls."""
        if cls.is_null_or_empty(text):
            return ""
        cleaned = re.sub(r"[^a-zA-Z0-9]", "", str(text)).lower()
        if cleaned in cls.NULL_STRINGS:
            return ""
        return cleaned

    @classmethod
    def extract_numbers_from_id(cls, text: Optional[str]) -> str:
        """Extracts the numeric sequence from an ID for candidate scoring (e.g. 'INV-8841' -> '8841')."""
        if cls.is_null_or_empty(text):
            return ""
        nums = re.findall(r"\d+", str(text))
        return "".join(nums)

    @classmethod
    def normalize_entity_name(cls, name: Optional[str]) -> str:
        """Normalizes company/entity names for comparison, stripping legal suffixes."""
        if cls.is_null_or_empty(name):
            return ""
        text = cls.normalize_text(name)
        # Strip punctuation
        text = re.sub(r"[^\w\s]", " ", text)
        for pattern in cls.ENTITY_SUFFIXES:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)
        # Standardize common abbreviations
        text = re.sub(r"\bindus\b", "industrial", text, flags=re.IGNORECASE)
        return " ".join(text.split()).strip()

    @classmethod
    def normalize_amount(cls, val: Any) -> Optional[float]:
        """Normalizes monetary amount strings/numbers to a clean float rounded to 2 decimals."""
        if cls.is_null_or_empty(val):
            return None

        if isinstance(val, (int, float)):
            if math.isnan(val) or math.isinf(val):
                return None
            return round(float(val), 2)

        s = str(val).strip()

        # Check for accounting negative notations: (450.00), -450, 450 CR
        is_negative = False
        if s.startswith("(") and s.endswith(")"):
            is_negative = True
            s = s[1:-1].strip()
        elif s.startswith("-") or s.endswith("-"):
            is_negative = True
        elif "cr" in s.lower():
            is_negative = True

        # Strip currency symbols, spaces, commas, letters
        cleaned = re.sub(r"[^\d.]", "", s)
        if not cleaned:
            return None

        try:
            amount = abs(float(cleaned))
            return round(-amount if is_negative else amount, 2)
        except ValueError:
            return None

    @classmethod
    def normalize_date(cls, val: Any) -> Optional[date]:
        """Parses a date string or datetime into a datetime.date object with strict sanity validation."""
        if cls.is_null_or_empty(val):
            return None

        if isinstance(val, datetime):
            return val.date()
        if isinstance(val, date):
            return val

        s = str(val).strip()
        # Must contain typical date delimiters (-, /, ., space) or be an 8-digit date string
        has_delim = any(c in s for c in ["-", "/", ".", " "])
        is_digit_date = s.isdigit() and len(s) == 8

        if not (has_delim or is_digit_date):
            return None

        try:
            dt = parse_date(s, fuzzy=False)
            # Enforce reasonable historical/modern transaction year boundary (1900 - 2100)
            if 1900 <= dt.year <= 2100:
                return dt.date()
            return None
        except Exception:
            return None

    @classmethod
    def date_diff_days(cls, d1: Optional[date], d2: Optional[date]) -> Optional[int]:
        """Calculates absolute difference between two dates in days."""
        if d1 is None or d2 is None:
            return None
        return abs((d1 - d2).days)
