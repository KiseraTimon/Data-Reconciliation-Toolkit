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
import re
import traceback

project_path = Path("..")
pages_path = project_path / "pages"

class Scrapper:
    def __init__(
        self,
        session=None,
        auth_url: str = "",
        url: str = "",
        keyword: str = "",
        data: list | None = None,
        username: str = "",
        password: str = "",
    ):
        self.session = session or requests.Session()
        self.auth_url = auth_url or "https://ilaw.kra.go.ke/ilaw/users/login"
        self.url = url or "https://ilaw.kra.go.ke/ilaw/search/universal/1?keyword="
        self.data = data
        self.username = username
        self.password = password

    def authenticator(self) -> bool:
        """Authenticate with KRA iLaw system"""
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
            print(f"🔐 Authenticating to {self.auth_url}...")
            response = self.session.post(self.auth_url, data=self.payload, headers=self.headers)
            print(f"Auth Response Status: {response.status_code}")
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
        """Extract data from KRA iLaw system"""
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
            print(f"\n{'='*50}")
            print(f"🔎 Searching: {item['keyword']} (Row: {item.get('excel_row')})")
            print(f"URL: {query_url}")

            try:
                response = self.session.post(query_url, data=self.payload, headers=self.headers)
                print(f"Response Status: {response.status_code}")
                
                if response.status_code != 200:
                    print(f"⚠️ HTTP Error {response.status_code}")
                    print(f"Response Text: {response.text[:200]}...")
                    continue

                try:
                    json_data = response.json()
                    print(f"JSON Keys: {list(json_data.keys())}")
                    print(f"HTML length: {len(json_data.get('html', ''))}")
                except json.JSONDecodeError as e:
                    print(f"❌ JSON Decode Error: {e}")
                    print(f"Response preview: {response.text[:200]}")
                    
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
                
                # Debug: Print all table rows found
                all_rows = soup.find_all('tr')
                print(f"Total rows found in HTML: {len(all_rows)}")

                found_matches = []
                for row_idx, row in enumerate(all_rows):
                    cols = row.find_all('td')
                    if len(cols) >= 4:
                        if len(cols) >= 4:
                            print(f"\n  Row {row_idx}: Found {len(cols)} columns")
                            
                            # Debug each column
                            for col_idx, col in enumerate(cols):
                                col_text = col.get_text(strip=True)
                                print(f"    Col {col_idx}: {col_text[:50] if col_text else 'Empty'}")
                            
                            span_tag = cols[1].find('span', class_='tooltipTable')
                            if span_tag and span_tag.get('tooltiptitle'):
                                citation = span_tag.get('tooltiptitle')
                            else:
                                citation = cols[1].get_text(strip=True)
                            
                            internal_ref = cols[2].get_text(strip=True)
                            assignee = cols[3].get_text(strip=True)

                            match_entry = {
                                "kra_citation": citation.encode('ascii', 'ignore').decode().strip() if citation else "",
                                "kra_ref": internal_ref.encode('ascii', 'ignore').decode().strip().upper() if internal_ref else "",
                                "kra_assignee": assignee.encode('ascii', 'ignore').decode().strip().upper() if assignee else ""
                            }
                            
                            # Only add if we have at least some data
                            if match_entry["kra_citation"] or match_entry["kra_ref"]:
                                found_matches.append(match_entry)
                                print(f"  ✅ Match found: {citation[:50] if citation else 'No citation'}...")

                result_entry = {
                    "excel_row": item.get('excel_row'),
                    "original_case": item['case_number'],
                    "case_name": item['citation'],
                    "search_keyword": item['keyword'],
                    "matches_found": len(found_matches),
                    "matches": found_matches
                }
                final_results.append(result_entry)
                
                print(f"\n📊 Results for {item['keyword']}: {len(found_matches)} matches found")

            except Exception as e:
                errhandler(f"Error processing {item['keyword']}: {e}", log="extractor", path="scrapper")
                print(f"❌ Exception: {e}")
                traceback.print_exc()
                continue

        print(f"\n{'='*50}")
        print(f"✅ Extraction complete. Total records processed: {len(final_results)}")
        return final_results

    def comparator(self, extracted_data: list) -> list:
        """Compare extracted data with original data"""
        print(f"\n⚖️  Comparing {len(extracted_data)} records against KRA results...")
        reconciled_data = []

        for item in extracted_data:
            sheet_citation_raw = str(item.get('case_name', '')).upper()
            sheet_case = str(item.get('original_case', 'Unknown')).upper()
            
            print(f"\n{'='*50}")
            print(f"🏁 Reconciling: [{sheet_case}] {sheet_citation_raw[:100]}")

            # Strategies
            sheet_tokens = clean_citation(sheet_citation_raw)
            sheet_string = clean_citation_text(sheet_citation_raw)
            sheet_court = get_court_type(sheet_case)

            matches = item.get('matches', [])
            print(f"📊 Found {len(matches)} potential matches in KRA system")

            best_match_details = {}
            confidence = 0.0
            status = "NOT FOUND"

            if not matches:
                print(f"❌ No matches found in system.")
            else:
                best_ratio = 0.0
                best_match_index = -1

                for match_idx, match in enumerate(matches):
                    kra_citation_raw = str(match.get('kra_citation', '')).upper()
                    kra_ref = str(match.get('kra_ref', '')).upper()
                    
                    print(f"\n  Match #{match_idx + 1}:")
                    print(f"    KRA Citation: {kra_citation_raw[:100]}")
                    print(f"    KRA Ref: {kra_ref}")

                    # Court type filtering
                    kra_court = get_court_type(kra_citation_raw)
                    print(f"    Court Type - Sheet: {sheet_court}, KRA: {kra_court}")

                    if sheet_court != 'NA' and kra_court != 'NA':
                        if sheet_court != kra_court:
                            print(f"    ⏭️  Skipping - court type mismatch")
                            continue

                    # Score A: Token Match (ignoring order)
                    kra_tokens = clean_citation(kra_citation_raw)
                    token_ratio = 0.0
                    if sheet_tokens and kra_tokens:
                        # Calculate Jaccard similarity
                        intersection = sheet_tokens.intersection(kra_tokens)
                        union = sheet_tokens.union(kra_tokens)
                        token_ratio = (len(intersection) / len(union)) * 100 if union else 0
                        print(f"    Token Match: {token_ratio:.1f}% (Shared: {len(intersection)}/{len(union)} tokens)")

                    # Score B: String Match (fuzzy)
                    kra_string = clean_citation_text(kra_citation_raw)
                    string_ratio = SequenceMatcher(None, sheet_string, kra_string).ratio() * 100
                    print(f"    String Match: {string_ratio:.1f}%")

                    # Score C: Reference number match
                    ref_ratio = 0
                    if sheet_case and kra_ref:
                        # Extract numbers from both
                        sheet_nums = re.findall(r'\d+', sheet_case)
                        kra_nums = re.findall(r'\d+', kra_ref)
                        
                        if sheet_nums and kra_nums:
                            if sheet_nums[-1] == kra_nums[-1]:  # Match last number (usually case number)
                                ref_ratio = 100
                                print(f"    Reference Match: 100% (Number match)")
                            else:
                                print(f"    Reference Match: 0% (Numbers don't match)")

                    # Combined score (weighted)
                    final_ratio = max(
                        token_ratio * 0.4 + string_ratio * 0.6,  # Weighted combination
                        token_ratio,  # Pure token
                        string_ratio,  # Pure string
                        ref_ratio  # Reference match
                    )
                    
                    print(f"    Final Ratio: {final_ratio:.1f}%")

                    if final_ratio > best_ratio:
                        best_ratio = final_ratio
                        best_match_details = match
                        best_match_index = match_idx
                        print(f"    ⭐ New best match!")

                confidence = round(best_ratio, 2)

                # Determine status based on confidence
                if confidence >= 80:
                    status = "VERIFIED MATCH"
                elif confidence >= 60:
                    status = "REVIEW REQUIRED"
                elif confidence >= 30:
                    status = "MISMATCH"
                else:
                    status = "NOT FOUND"

                print(f"\n📊 Best Match #{best_match_index + 1 if best_match_index >= 0 else 'N/A'}: {status} ({confidence}%)")
                if best_match_details:
                    print(f"   Best KRA Citation: {best_match_details.get('kra_citation', 'N/A')[:100]}")
                    print(f"   Best KRA Ref: {best_match_details.get('kra_ref', 'N/A')}")

            item['status'] = status
            item['confidence_score'] = f"{confidence}%"
            item['confidence_raw'] = confidence
            item['best_match_kra_ref'] = best_match_details.get('kra_ref', 'N/A') if best_match_details else 'N/A'
            item['best_match_kra_citation'] = best_match_details.get('kra_citation', 'N/A') if best_match_details else 'N/A'
            item['best_match_kra_assignee'] = best_match_details.get('kra_assignee', 'N/A') if best_match_details else 'N/A'

            reconciled_data.append(item)

        print("\n" + "="*50)
        print("✅ Comparison complete.")
        
        # Print summary
        status_counts = {}
        for item in reconciled_data:
            status = item.get('status', 'UNKNOWN')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print("\n📊 Summary:")
        for status, count in status_counts.items():
            print(f"  {status}: {count}")
        
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
        color_not_found = PatternFill(start_color="FF9999", end_color="FF9999", fill_type="solid")  # Light Red
        color_mismatch = PatternFill(start_color="FFCC00", end_color="FFCC00", fill_type="solid")   # Orange
        color_review = PatternFill(start_color="99CCFF", end_color="99CCFF", fill_type="solid")     # Light Blue
        color_verified = PatternFill(start_color="F0FFF0", end_color="F0FFF0", fill_type="solid")   # Honeydew

        try:
            # Check if file exists
            if not Path(file_path).exists():
                print(f"❌ File not found: {file_path}")
                return False
                
            # Load the Original Workbook
            wb = openpyxl.load_workbook(file_path)
            ws = wb.active

            # Determining New Column Indices
            last_col = ws.max_column
            status_col = last_col + 1
            match_col = last_col + 2

            # Write Headers
            ws.cell(row=1, column=status_col, value="Reconciliation Status").font = Font(bold=True)
            ws.cell(row=1, column=match_col, value="Closest KRA Match").font = Font(bold=True)

            # Iterating Data
            for item in data:
                row_idx = item.get('excel_row')
                status = item.get('status')
                best_match = item.get('best_match_kra_citation', 'N/A')

                if not row_idx:
                    continue

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

            # Save
            timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
            parent_path = Path(".")
            save_dir = parent_path / "reports"
            save_dir.mkdir(parents=True, exist_ok=True)

            original_name = Path(file_path).stem
            output_path = save_dir / f"{original_name}_RECONCILED_{timestamp}.xlsx"

            wb.save(output_path)
            print(f"✅ Report saved to: {output_path.resolve()}")
            
            # Clean up temp file if it's a temp file
            if "temp" in file_path and Path(file_path).exists():
                try:
                    Path(file_path).unlink()
                except:
                    pass
                    
            return True

        except Exception as e:
            errhandler(e, log="report", path="scrapper")
            print(f"❌ Error generating report: {e}")
            return False