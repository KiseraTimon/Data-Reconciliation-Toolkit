# helpers/__init__.py

import pandas as pd
import re

# Column Checker
def find_column(df, possible_names):
    """Finds column by checking multiple possible names"""

    for name in possible_names:
        if name in df.columns:
            return name
    return None

# Noise Keywords
def get_noise_words():
    return {
        "VS", "VERSUS", "KENYA", "REVENUE", "AUTHORITY", "KRA",
        "COMMISSIONER", "COMMISIONER", "LEGAL", "NAIROBI", "TAT",
        "HCITA", "HCCOMMITA", "HCC", "NO", "OF", "LIMITED", "LTD",
        "DOMESTIC", "TAXES", "MISC", "AND", "FOR", "CUSTOMS",
        "INVESTIGATION", "BOARD", "SERVICES", "COORDINATION",
        "UNDER", "RECEIVABLE", "IN", "RECEIVERSHIP", "BORDER CONTROL", "BORDER",
        "LARGE AND SMALL", "LARGE & SMALL", "TAXPAYERS"
    }

# Citation Cleaner
def clean_citation(text: str) -> set:
    """
    Returns a SET of unique meaningful words (Order is lost).
    Good for: 'John Doe vs KRA' matching 'KRA vs John Doe'
    """
    if not text:
        return set()

    text = text.upper()

    # Removing Case Numbers & Years
    text = re.sub(r'[A-Z]?\d+\s+OF\s+\d{4}', '', text)
    text = re.sub(r'\d{4}', '', text)

    # Removing special chars
    text = re.sub(r'[^A-Z\s]', '', text)

    words = set(text.split())
    return words - get_noise_words()

def clean_citation_text(text: str) -> str:
    """
    Returns a CLEAN STRING (Order preserved).
    Good for: 'ABCXYZ' matching 'ABC XYZ'
    """
    if not text:
        return ""

    text = text.upper()

    # Removing Case Numbers & Years
    text = re.sub(r'[A-Z]?\d+\s+OF\s+\d{4}', '', text)
    text = re.sub(r'\d{4}', '', text)

    # Removing special chars
    text = re.sub(r'[^A-Z\s]', ' ', text) # Replace with space to prevent accidental mashing

    # Removing noise words using regex to preserve sentence structure
    noise = get_noise_words()
    words = text.split()
    cleaned_words = [w for w in words if w not in noise]

    return " ".join(cleaned_words)

def get_court_type(text: str) -> str:
        """
        Heuristic to identify court type from a case string.
        Returns: 'TAT', 'HC', 'CA', 'SU', or 'NA'
        """
        text = text.upper()

        # 1. Tax Appeals Tribunal
        if any(x in text for x in ['TAT', 'TAX APPEAL', 'TATC', 'TATMISC']):
            return 'TAT'

        # 2. Supreme Court
        if 'SUPREME' in text or 'SCORK' in text:
            return 'SU'

        # 3. Court of Appeal
        if any(x in text for x in ['CACA', 'COURT OF APPEAL']):
            return 'CA'

        # 4. High Court (Catch-all for HC variants)
        # HCCC, HCITA, HCCHRPET, HCCOMM, ELRC, JR, ETC.
        if any(x in text for x in ['HC', 'HIGH COURT', "COMMITA", "HCITA", 'ELRC', 'JR ', 'MISC', 'HRPET', 'CTA']):
            return 'HC'

        return "NA"