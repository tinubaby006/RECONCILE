from __future__ import annotations

import re
from datetime import date, datetime
from typing import Optional, Tuple
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

    @classmethod
    def normalize_text(cls, text: Optional[str]) -> str:
        """Standard text normalization: strips extra whitespace, lowercases."""
        if not text:
            return ""
        return " ".join(str(text).strip().split()).lower()

    @classmethod
    def normalize_id(cls, text: Optional[str]) -> str:
        """Normalizes identifiers/keys: removes symbols, whitespace, leading zeroes."""
        if not text:
            return ""
        cleaned = re.sub(r"[^a-zA-Z0-9]", "", str(text)).lower()
        return cleaned

    @classmethod
    def extract_numbers_from_id(cls, text: Optional[str]) -> str:
        """Extracts the numeric sequence from an ID, useful for matching 'INV-8841' with 'REF8841'."""
        if not text:
            return ""
        nums = re.findall(r"\d+", str(text))
        return "".join(nums)

    @classmethod
    def normalize_entity_name(cls, name: Optional[str]) -> str:
        """Normalizes company/entity names for comparison, stripping legal suffixes."""
        if not name:
            return ""
        text = cls.normalize_text(name)
        # Strip punctuation
        text = re.sub(r"[^\w\s]", " ", text)
        for pattern in cls.ENTITY_SUFFIXES:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)
        # Strip common abbreviation words
        text = re.sub(r"\bindus\b", "industrial", text, flags=re.IGNORECASE)
        return " ".join(text.split()).strip()

    @classmethod
    def normalize_amount(cls, val: Any) -> Optional[float]:
        """Normalizes monetary amount strings/numbers to a clean float rounded to 2 decimals."""
        if val is None or val == "":
            return None

        if isinstance(val, (int, float)):
            return round(float(val), 2)

        s = str(val).strip()
        if not s or s.lower() in ["nan", "none", "null", "-", ""]:
            return None

        # Check for accounting parentheses e.g. (450.00) or (₹450.00)
        is_negative = False
        if s.startswith("(") and s.endswith(")"):
            is_negative = True
            s = s[1:-1]
        elif s.startswith("-") or s.endswith("-"):
            is_negative = True
            s = s.replace("-", "")
        elif "cr" in s.lower():
            is_negative = True
            s = re.sub(r"(?i)cr", "", s)
        elif "dr" in s.lower():
            s = re.sub(r"(?i)dr", "", s)

        # Remove currency symbols and whitespace
        s = re.sub(r"[\$\€\£\₹\¥\s\,]", "", s)

        try:
            amount = float(s)
            return round(-amount if is_negative else amount, 2)
        except ValueError:
            return None

    @classmethod
    def normalize_date(cls, val: Any) -> Optional[date]:
        """Parses a date string or datetime into a datetime.date object."""
        if val is None or val == "":
            return None

        if isinstance(val, datetime):
            return val.date()
        if isinstance(val, date):
            return val

        s = str(val).strip()
        if not s or s.lower() in ["nan", "none", "null"]:
            return None

        try:
            dt = parse_date(s, fuzzy=False)
            return dt.date()
        except Exception:
            try:
                # Fallback to fuzzy parsing
                dt = parse_date(s, fuzzy=True)
                return dt.date()
            except Exception:
                return None

    @classmethod
    def date_diff_days(cls, d1: Optional[date], d2: Optional[date]) -> Optional[int]:
        """Calculates absolute difference between two dates in days."""
        if d1 is None or d2 is None:
            return None
        return abs((d1 - d2).days)
