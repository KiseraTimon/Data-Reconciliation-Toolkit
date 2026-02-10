# modules/scanner.py

import pandas as pd
import re

from utils import errhandler

class Scanner:
    # Constructor
    def __init__(self, case_num_column, citation_column):
        self.case_num_column = case_num_column
        self.citation_column = citation_column
        self.file_data = []

    # Counting Records
    def count_records(
        self,
        sheet = None
    ) -> int:
        """
        Function to Count Records in the File
        """

        if sheet is None:
            print("⚠️ The sheet is empty")

            return 0

        print("✅ The sheet's items have been successfully counted")

        return len(sheet)

    def file_extractor(
        self,
        sheet = None
    ):
        """
        Function to extract data from uploaded file
        """

        if sheet is None:
            print("❌ A sheet was not provided for file data extraction")

            return None

        extracted_data = []

        try:
            for idx, row in sheet.iterrows():
                case_num = str(row.get(self.case_num_column, ""))
                citation = str(row.get(self.citation_column, ""))

                # Preparing Keyword
                keyword = case_num

                clean_parts = case_num.replace(".", "").split("/")

                if len(clean_parts) >= 2:
                    keyword = f"{clean_parts[-2]} of {clean_parts[-1]}"


                if pd.notna(case_num) and pd.notna(citation):
                    record = {
                        "excel_row": idx + 2,
                        "case_number": case_num.strip().upper(),
                        "citation": re.sub(r'\s+', ' ', citation.strip()).upper(),
                        "keyword": keyword.upper()
                    }
                    extracted_data.append(record)

            # Updating internal state
            self.file_data = extracted_data

            print("✅ Sheet data extraction was successful")

            return extracted_data

        except KeyError as e:
            errhandler(f"Column mismatch during extraction:\n{e}", log="file_extractor", path="scanner")
            return []
