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
                # Convert to string and handle NaN/None values
                case_num_raw = row.get(self.case_num_column, "")
                citation_raw = row.get(self.citation_column, "")
                
                # Handle different data types
                if pd.isna(case_num_raw):
                    case_num = ""
                else:
                    case_num = str(case_num_raw).strip()
                
                if pd.isna(citation_raw):
                    citation = ""
                else:
                    citation = str(citation_raw).strip()

                # Skip empty rows
                if not case_num and not citation:
                    continue

                # Preparing Keyword - try to extract meaningful search terms
                keyword = case_num
                
                # If case_num looks like a number only, use citation for search
                if case_num.isdigit() and citation:
                    keyword = citation
                elif case_num and "/" in case_num:
                    # Handle case numbers like "TAT/123/2023"
                    clean_parts = case_num.replace(".", "").split("/")
                    if len(clean_parts) >= 2:
                        keyword = f"{clean_parts[-2]} {clean_parts[-1]}"
                elif case_num and len(case_num) < 5 and citation:
                    # If case number is too short, use citation
                    keyword = citation

                record = {
                    "excel_row": idx + 2,  # +2 because Excel rows start at 1 and header is row 1
                    "case_number": case_num.upper(),
                    "citation": re.sub(r'\s+', ' ', citation).upper(),
                    "keyword": keyword.upper()
                }
                
                if case_num or citation:  # Only add if there's some data
                    extracted_data.append(record)
                    print(f"Row {idx+2}: Case: {case_num}, Citation: {citation[:30]}..., Keyword: {keyword}")

            # Updating internal state
            self.file_data = extracted_data

            print(f"✅ Sheet data extraction was successful. Extracted {len(extracted_data)} records.")
            return extracted_data

        except KeyError as e:
            errhandler(f"Column mismatch during extraction:\n{e}", log="file_extractor", path="scanner")
            return []
        except Exception as e:
            errhandler(f"Unexpected error during extraction:\n{e}", log="file_extractor", path="scanner")
            return []