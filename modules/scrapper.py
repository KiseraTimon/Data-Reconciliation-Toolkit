# modules/scrapper.py

import requests
from bs4 import BeautifulSoup
from utils import errhandler, syshandler
from helpers import clean_citation, clean_citation_text, get_court_type

from pathlib import Path
from typing import Optional
import urllib.parse
from difflib import SequenceMatcher
from datetime import datetime
import openpyxl
from openpyxl.styles import PatternFill, Font
import json

import time

project_path = Path("..")
pages_path = project_path / "pages"

class Scrapper:
    def __init__(
        self,
        session = None,
        auth_url: str = "",
        url: str = "",
        keyword: str = "",
        data: list | None = None,
        username: str = "",
        password: str = "",
    ):
        self.session = session or requests.Session()
        self.auth_url = auth_url or "https://ilaw.kra.go.ke/ilaw/users/login"
        self.url = url or f"https://ilaw.kra.go.ke/ilaw/search/universal/1?keyword="
        self.data = data
        self.username = username
        self.password = password

    def authenticator(self) -> bool:
        self.payload = {
            'username': self.username,
            'password': self.password,
            "hashPart": "",
            "redirect_to": "",
            "login": "Sign In"
        }
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
            "Referer": self.auth_url
        }

        try:
            response = self.session.post(self.auth_url, data=self.payload, headers=self.headers)
        except Exception as e:
            errhandler(e, log="authenticator", path="scrapper")
            return False
        else:
            if response.status_code == 200 and "sign-in-container" not in response.text:
                print("✅ Logged in successfully!")
                return True
            else:
                print("❌ Log in attempt failed. Check credentials.")
                return False

    def extractor(self) -> Optional[list]:
        final_results = []
        print(f"⌛ Starting extraction for {len(self.data)} records...")

        self.headers = {
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        self.payload = {"dataType": "litigation_data"}

        for i, item in enumerate(self.data):
            # RATE LIMITING: 2s break/10 requests
            if i > 0 and i % 10 == 0:
                time.sleep(2)


            safe_keyword = urllib.parse.quote(item['keyword'])
            query_url = f"{self.url}{safe_keyword}"
            print(f"🔎 Searching: {item['keyword']}...")

            try:
                response = self.session.post(query_url, data=self.payload, headers=self.headers)
                if response.status_code != 200:
                    print(f"⚠️ HTTP Error {response.status_code}")
                    continue

                try:
                    json_data = response.json()
                except json.JSONDecodeError:
                    # Checking if session expired
                    if "sign-in-container" in response.text.lower():
                        print("⚠️ Session expired. Re-authenticating...")
                        if self.authenticator():
                            # Retry the request once
                            response = self.session.post(query_url, data=self.payload, headers=self.headers)
                            try:
                                json_data = response.json()
                            except:
                                print("❌ Retry failed. Moving to next.")
                                continue
                        else:
                            print("❌ Re-authentication failed. Stopping extraction.")
                            break
                    else:
                        print(f"❌ Invalid JSON response (Server Error?)")
                        continue


                html_string = json_data.get('html', '')
                soup = BeautifulSoup(html_string, 'html.parser')

                found_matches = []
                for row in soup.find_all('tr'):
                    cols = row.find_all('td')
                    if len(cols) >= 4:
                        span_tag = cols[1].find('span', class_='tooltipTable')
                        citation = span_tag.get('tooltiptitle')
                        if not citation:
                            citation = span_tag.get_text(strip=True)

                        internal_ref = cols[2].get_text(strip=True)
                        assignee = cols[3].get_text(strip=True)

                        match_entry = {
                            "kra_citation": citation.encode('ascii', 'ignore').decode().strip(),
                            "kra_ref": internal_ref.encode('ascii', 'ignore').decode().strip().upper(),
                            "kra_assignee": assignee.encode('ascii', 'ignore').decode().strip().upper()
                        }
                        found_matches.append(match_entry)

                result_entry = {
                    "excel_row": item.get('excel_row'),
                    "original_case": item['case_number'],
                    "case_name": item['citation'],
                    "search_keyword": item['keyword'],
                    "matches_found": len(found_matches),
                    "matches": found_matches
                }
                final_results.append(result_entry)

            except Exception as e:
                errhandler(f"Error processing {item['keyword']}: {e}", log="extractor", path="scrapper")
                continue

        return final_results

    def comparator(self, extracted_data: list) -> list:
        print(f"\n⚖️  Comparing {len(extracted_data)} records against KRA results...")
        reconciled_data = []

        for item in extracted_data:
            sheet_citation_raw = str(item.get('case_name', '')).upper()
            sheet_case = item.get('original_case', 'Unknown')

            # Strategies
            sheet_tokens = clean_citation(sheet_citation_raw)
            sheet_string = clean_citation_text(sheet_citation_raw)
            sheet_court = get_court_type(sheet_case)

            matches = item.get('matches', [])

            print(f"\n🏁 Reconciling: [{sheet_case}] {sheet_string}")

            best_match_details = {}
            confidence = 0.0

            if not matches:
                status = "NOT FOUND"
                print(f"❌ No matches found in system.")
            else:
                status = "MISMATCH"
                best_ratio = 0.0

                for match in matches:
                    kra_citation_raw = str(match.get('kra_citation', '')).upper()
                    kra_court = get_court_type(kra_citation_raw)

                    if sheet_court != 'NA' and kra_court != 'NA':
                        if sheet_court != kra_court:
                            continue

                    # Score A: Token Match
                    kra_tokens = clean_citation(kra_citation_raw)
                    token_ratio = 0.0
                    if sheet_tokens and kra_tokens:
                        matched_count = 0
                        for s_t in sheet_tokens:
                            best_w = 0.0
                            for k_t in kra_tokens:
                                sim = SequenceMatcher(None, s_t, k_t).ratio()
                                if sim > best_w: best_w = sim
                            if best_w > 0.85: matched_count += 1
                        token_ratio = matched_count / len(sheet_tokens)

                    # Score B: String Match
                    kra_string = clean_citation_text(kra_citation_raw)
                    string_ratio = SequenceMatcher(None, sheet_string, kra_string).ratio()

                    final_ratio = max(token_ratio, string_ratio)

                    if final_ratio > best_ratio:
                        best_ratio = final_ratio
                        best_match_details = match

                confidence = round(best_ratio * 100, 2)

                if confidence >= 85:
                    status = "VERIFIED MATCH"
                elif confidence >= 50:
                    status = "REVIEW REQUIRED"
                else:
                    status = "MISMATCH"

                print(f"📊 Result: {status} ({confidence}%)")

            item['status'] = status
            item['confidence_score'] = f"{confidence}%"
            item['best_match_kra_ref'] = best_match_details.get('kra_ref', 'N/A')
            item['best_match_kra_citation'] = best_match_details.get('kra_citation', 'N/A')

            reconciled_data.append(item)

        print("\n✅ Comparison complete.")
        return reconciled_data

    def report(self, data: list | None = None, file_path: str = "") -> bool:
        """
        Highlights the ORIGINAL document and adds Status/Match columns.
        """
        if not data or not file_path:
            print("⚠️ Missing data or file path for reporting.")
            return False

        print(f"\n🎨 Generating Enhanced Report based on {file_path}...")

        # Defining Colors (Hex Codes)
        color_not_found = PatternFill(start_color="FF9999", end_color="FF9999", fill_type="solid") # Light Red
        color_mismatch = PatternFill(start_color="FFCC00", end_color="FFCC00", fill_type="solid")  # Orange
        color_review = PatternFill(start_color="99CCFF", end_color="99CCFF", fill_type="solid")    # Light Blue
        color_verified = PatternFill(start_color="F0FFF0", end_color="F0FFF0", fill_type="solid")  # Honeydew

        try:
            # Load the Original Workbook
            wb = openpyxl.load_workbook(file_path)
            ws = wb.active

            # Determining New Column Indices
            last_col = ws.max_column
            status_col = last_col + 1
            match_col = last_col + 2

            # 4. Write Headers
            ws.cell(row=1, column=status_col, value="Reconciliation Status").font = Font(bold=True)
            ws.cell(row=1, column=match_col, value="Closest KRA Match").font = Font(bold=True)

            # Iterating Data
            for item in data:
                row_idx = item.get('excel_row')
                status = item.get('status')
                best_match = item.get('best_match_kra_citation', 'N/A')

                if not row_idx: continue

                # Writing New Data to the row
                ws.cell(row=row_idx, column=status_col, value=status)
                ws.cell(row=row_idx, column=match_col, value=best_match)

                # Determining Highlight Color
                fill_color = None
                if status == "NOT FOUND":
                    fill_color = color_not_found
                elif status == "MISMATCH":
                    fill_color = color_mismatch
                elif status == "REVIEW REQUIRED":
                    fill_color = color_review
                elif status == "VERIFIED MATCH":
                    fill_color = color_verified

                # Applying Highlight to the Whole Row (Existing cols + New cols)
                if fill_color:
                    # Iterating from col 1 to our new last column
                    for col in range(1, match_col + 1):
                        ws.cell(row=row_idx, column=col).fill = fill_color

            # Saves5
            timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
            parent_path = Path(".")
            save_dir = parent_path / "reports"
            save_dir.mkdir(parents=True, exist_ok=True)

            original_name = Path(file_path).stem
            output_path = save_dir / f"{original_name}_RECONCILED_{timestamp}.xlsx"

            wb.save(output_path)
            print(f"✅ Report saved to: {output_path.resolve()}")
            return True

        except Exception as e:
            errhandler(e, log="report", path="scrapper")
            return False