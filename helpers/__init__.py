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

# Citation Cleaner
def clean_citation(text: str) -> set:
        """
        Cleans text and returns a SET of unique meaningful words (Tokens).
        """
        if not text:
            return set()

        text = text.upper()

        # 1. Regex to remove Case Numbers (e.g., E031 OF 2026, 123/2025)
        text = re.sub(r'[A-Z]?\d+\s+OF\s+\d{4}', '', text)

        # 2. Removing loose years
        text = re.sub(r'\d{4}', '', text)

        # 3. Removing special chars
        text = re.sub(r'[^A-Z\s]', '', text)

        # 4. Defining Noise Words to ignore
        noise_words = {
            "VS", "VERSUS", "KENYA", "REVENUE", "AUTHORITY", "KRA", "COMMISSIONER", "COMMISIONER", "COMISSIONER", "COMISIONER", "LEGAL", "NAIROBI", "TAT", "HCITA", "HCCOMMITA", "HCC", "NO", "OF", "LIMITED", "LTD", "DOMESTIC", "TAXES", "MISC", "AND", "FOR", "CUSTOMS", "INVESTIGATION", "INVESTIGATIONS", "I&E", "BOARD SERVICES", "BOARD COORDINATION", "UNDER RECEIVABLE"
        }

        # 5. Creating Token Set
        words = set(text.split())

        # 6. Returning meaningful words only
        clean_tokens = words - noise_words
        return clean_tokens

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