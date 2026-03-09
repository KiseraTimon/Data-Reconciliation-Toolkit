# modules/scanner.py
# Fixed: formats eJuris keywords as "E{number} of {year}"
# Handles case numbers like HCCOMMITA/E017/2026 → "E017 of 2026"

import pandas as pd
import re
from utils import errhandler


class Scanner:
    def __init__(self, case_num_column, citation_column):
        self.case_num_column = case_num_column
        self.citation_column = citation_column
        self.file_data = []

    def count_records(self, sheet=None) -> int:
        if sheet is None:
            print("⚠️ The sheet is empty")
            return 0
        print("✅ Records counted successfully")
        return len(sheet)

    # ─────────────────────────────────────────────────────────────────────────
    # Core fix: build the correct eJuris keyword
    # Input:  HCCOMMITA/E017/2026
    # Output: E017 of 2026
    # ─────────────────────────────────────────────────────────────────────────
    @staticmethod
    def build_ejuris_keyword(case_num: str, citation: str = "") -> str:
        """
        Extract E-number and year from any case number format and return
        "E{number} of {year}" — exactly what eJuris search expects.

        Examples:
          HCCOMMITA/E017/2026  →  E017 of 2026
          HCCHRPET/E046/2026   →  E046 of 2026
          E017/2026            →  E017 of 2026
          E017 2026            →  E017 of 2026
          1403/2023            →  E1403 of 2023
          E017 of 2026         →  E017 of 2026  (already correct)
        """
        s = case_num.strip()

        # ── Already correct: E017 of 2026 ────────────────────────────────────
        m = re.match(r'^(E\d+)\s+of\s+(\d{4})$', s, re.IGNORECASE)
        if m:
            return f"{m.group(1).upper()} of {m.group(2)}"

        # ── Pattern: anything/E{num}/{year}  e.g. HCCOMMITA/E017/2026 ────────
        m = re.search(r'/(E\d+)/(\d{4})', s, re.IGNORECASE)
        if m:
            return f"{m.group(1).upper()} of {m.group(2)}"

        # ── Pattern: E{num}/{year}  e.g. E017/2026 ───────────────────────────
        m = re.match(r'^(E\d+)[/\-_](\d{4})$', s, re.IGNORECASE)
        if m:
            return f"{m.group(1).upper()} of {m.group(2)}"

        # ── Pattern: E{num} {year}  e.g. E017 2026 ───────────────────────────
        m = re.match(r'^(E\d+)\s+(\d{4})$', s, re.IGNORECASE)
        if m:
            return f"{m.group(1).upper()} of {m.group(2)}"

        # ── Pattern: E{num} alone — pull year from citation ──────────────────
        m = re.match(r'^(E\d+)$', s, re.IGNORECASE)
        if m:
            yr = re.search(r'\b(20\d{2}|19\d{2})\b', citation)
            year = yr.group(0) if yr else ""
            return f"{m.group(1).upper()} of {year}" if year else m.group(1).upper()

        # ── Pattern: plain number/year  e.g. 1403/2026 ───────────────────────
        m = re.match(r'^(\d+)[/\-_\s]+(\d{4})$', s)
        if m:
            return f"E{m.group(1)} of {m.group(2)}"

        # ── Fallback: extract any E+digits and any 4-digit year in the string ─
        e_match  = re.search(r'E(\d+)', s, re.IGNORECASE)
        yr_match = re.search(r'\b(20\d{2}|19\d{2})\b', s)
        if e_match and yr_match:
            return f"E{e_match.group(1)} of {yr_match.group(1)}"

        # ── Fallback: any digits + year ───────────────────────────────────────
        nums  = re.findall(r'\d+', s)
        years  = [n for n in nums if re.match(r'^(19|20)\d{2}$', n)]
        non_yr = [n for n in nums if n not in years]
        if non_yr and years:
            return f"E{non_yr[-1]} of {years[-1]}"

        # ── Cannot parse ──────────────────────────────────────────────────────
        print(f"⚠️  Could not parse '{s}' into E{{num}} of {{year}} — using raw value")
        return s if s else citation

    def file_extractor(self, sheet=None):
        """
        Extract records from the uploaded file.
        Keyword is always formatted as "E{number} of {year}" for eJuris.
        """
        if sheet is None:
            print("❌ No sheet provided")
            return None

        extracted_data = []

        try:
            for idx, row in sheet.iterrows():
                case_num_raw = row.get(self.case_num_column, "")
                citation_raw = row.get(self.citation_column, "")

                case_num = "" if pd.isna(case_num_raw) else str(case_num_raw).strip()
                citation = "" if pd.isna(citation_raw) else str(citation_raw).strip()

                if not case_num and not citation:
                    continue

                keyword = self.build_ejuris_keyword(case_num, citation)

                record = {
                    "excel_row":   idx + 2,
                    "case_number": case_num.upper(),
                    "citation":    re.sub(r'\s+', ' ', citation).upper(),
                    "keyword":     keyword,
                }

                extracted_data.append(record)
                print(f"Row {idx+2}: Case: {case_num}, Citation: {citation[:30]}..., Keyword: {keyword}")

            self.file_data = extracted_data
            print(f"✅ Sheet data extraction was successful. Extracted {len(extracted_data)} records.")
            return extracted_data

        except KeyError as e:
            errhandler(f"Column mismatch: {e}", log="file_extractor", path="scanner")
            return []
        except Exception as e:
            errhandler(f"Unexpected error: {e}", log="file_extractor", path="scanner")
            return []