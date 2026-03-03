# modules/validators.py

import pandas as pd
from pathlib import Path

from utils import errhandler
from helpers import find_column

class Validator:
    def __init__(
        self,
        file_path: str = "",
        case_num_column = None,  # Changed to accept any type
        citation_column = None   # Changed to accept any type
    ):
        self.file_path = Path(file_path)
        
        # Convert to string and handle potential integer inputs
        if case_num_column is not None:
            self.case_num_column = str(case_num_column).strip()
        else:
            self.case_num_column = ""
            
        if citation_column is not None:
            self.citation_column = str(citation_column).strip()
        else:
            self.citation_column = ""

    def file_exists(self) -> bool:
        """
        Function to check if the provided file exists
        """

        if not self.file_path.exists():
            print(f"❌ The provided file path does not exist.\nFile path given: {self.file_path}\n")
            return False

        print("✅ The provided file path exists")
        return True

    def create_sheet(self):
        try:
            if self.file_path.suffix == ".xlsx":
                sheet = pd.read_excel(self.file_path)
            elif self.file_path.suffix == ".csv":
                sheet = pd.read_csv(self.file_path)
            else:
                print(f"❌ Unsupported file format: {self.file_path.suffix}")
                return None

        except Exception as e:
            errhandler(e, log="create_sheet", path="validator")
            return None

        else:
            print(f"✅ A sheet has been parsed for the uploaded {self.file_path.suffix.upper()} document")
            return sheet

    def check_annotations(
        self,
        sheet = None
    ) -> bool:
        """
        Function to check if file has relevant keywords
        """

        if sheet is None:
            return None

        # Convert columns to strings for comparison
        sheet_columns = [str(col).strip() for col in sheet.columns]

        if self.case_num_column not in sheet_columns:
            found = find_column(sheet, ['Case Number', 'Case No', 'Case #', 'case_number', 'case no', 'case number'])
            if found:
                print(f"⚠️ User column '{self.case_num_column}' not found. Auto-detected '{found}'.")
                self.case_num_column = found
            else:
                print(f"❌ Column '{self.case_num_column}' not found.")
                print(f"Available columns: {', '.join(sheet_columns[:10])}")
                return False

        if self.citation_column not in sheet_columns:
            found = find_column(sheet, ['Citation', 'Cit', 'Reference', 'citation', 'case name', 'case_name'])
            if found:
                print(f"⚠️ User column '{self.citation_column}' not found. Auto-detected '{found}'.")
                self.citation_column = found
            else:
                print(f"❌ Column '{self.citation_column}' not found.")
                print(f"Available columns: {', '.join(sheet_columns[:10])}")
                return False

        return True