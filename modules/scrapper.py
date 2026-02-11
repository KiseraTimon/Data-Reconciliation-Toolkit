# modules/scrapper.py

import requests
from bs4 import BeautifulSoup
import requests

from utils import errhandler, syshandler
from helpers import clean_citation, clean_citation_text, get_court_type

from pathlib import Path
from typing import Optional
import urllib.parse
from difflib import SequenceMatcher
from datetime import datetime

project_path = Path("..")
pages_path = project_path / "pages"

class Scrapper:
    # Constructor
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
        """
        Function to handle authentication logic if required
        """

        self.payload = {
            'username': self.username,
            'password': self.password,
            "hashPart": "",      # Usually empty unless redirected
            "redirect_to": "",   # Found in the d-none input
            "login": "Sign In"   # The submit button name/value
        }

        # Headers
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
                print("❌ Log in attempt failed. Check credentials or hidden fields")

                return False


    def extractor(self) -> Optional[list]:
        """
        Iterates through self.data, searches each keyword, and appends results.
        """
        final_results = []

        print(f"⌛ Starting extraction for {len(self.data)} records...")

        self.headers = {
            "X-Requested-With": "XMLHttpRequest", # AJAX Call
            "Content-Type": "application/x-www-form-urlencoded"
        }

        # The script implements the sent 'dataType' in the POST body
        # Valid types: "matter_data", "litigation_data"
        self.payload = {
            "dataType": "litigation_data"
        }

        for item in self.data:
            # 1. URL Encode the keyword safely
            safe_keyword = urllib.parse.quote(item['keyword'])
            query_url = f"{self.url}{safe_keyword}"

            print(f"🔎 Searching: {item['keyword']}...")

            try:
                # 2. Performing Request
                payload = {"dataType": "litigation_data"}
                response = self.session.post(query_url, data=self.payload, headers=self.headers)

                if response.status_code != 200:
                    print(f"❌ Error {response.status_code} for {item['keyword']}")
                    continue

                # 3. Parsing JSON to get HTML
                json_data = response.json()
                html_string = json_data.get('html', '')
                soup = BeautifulSoup(html_string, 'html.parser')

                # 4. Extracting Rows
                rows = soup.find_all('tr')
                found_matches = []

                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 4:
                        span_tag = cols[1].find('span', class_='tooltipTable')

                        # Trying to get the hidden 'tooltiptitle' attribute first
                        citation = span_tag.get('tooltiptitle')

                        # If attribute is missing/empty, fall back to visible text
                        if not citation:
                            citation = span_tag.get_text(strip=True)

                        internal_ref = cols[2].get_text(strip=True)
                        assignee = cols[3].get_text(strip=True)

                        # Cleaning data
                        match_entry = {
                            "kra_citation": citation.encode('ascii', 'ignore').decode().strip(),
                            "kra_ref": internal_ref.encode('ascii', 'ignore').decode().strip().upper(),
                            "kra_assignee": assignee.encode('ascii', 'ignore').decode().strip().upper()
                        }
                        found_matches.append(match_entry)

                # 5. Storing result attached to the original record
                result_entry = {
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

    def comparator(
        self,
        extracted_data: list
    ) -> list:
        print(f"\n⚖️  Comparing {len(extracted_data)} records against KRA results...")
        reconciled_data = []

        for item in extracted_data:
            # 1. Preparing Sheet Data
            sheet_citation_raw = str(item.get('case_name', '')).upper()
            sheet_case = item.get('original_case', 'Unknown')

            # Strategy A: Token Set (Good for scrambled order)
            sheet_tokens = clean_citation(sheet_citation_raw)

            # Strategy B: Clean String (Good for mashed text)
            sheet_string = clean_citation_text(sheet_citation_raw)

            sheet_court = get_court_type(sheet_case)
            matches = item.get('matches', [])

            print(f"\n🏁 Reconciling: [{sheet_case}] {sheet_string}")

            # --- STRICT STATUS DEFAULTS ---
            best_match_details = {}
            confidence = 0.0

            # CASE 1: NOT FOUND (Zero results returned)
            if not matches:
                status = "NOT FOUND"
                print(f"❌ No matches found in system.")

            else:
                # Defaulting to MISMATCH until proven otherwise
                status = "MISMATCH"
                best_ratio = 0.0

                for match in matches:
                    kra_citation_raw = str(match.get('kra_citation', '')).upper()

                    # Check Court Compatibility
                    kra_court = get_court_type(kra_citation_raw)
                    if sheet_court != 'NA' and kra_court != 'NA':
                        if sheet_court != kra_court:
                            continue # Wrong court, skip this specific match

                    # --- SCORING ---

                    # Score A: Fuzzy Token Matching (Word vs Word)
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

                    # Score B: Whole String Matching
                    kra_string = clean_citation_text(kra_citation_raw)
                    string_ratio = SequenceMatcher(None, sheet_string, kra_string).ratio()

                    # FINAL SCORE: Take the higher of the two
                    final_ratio = max(token_ratio, string_ratio)

                    if final_ratio > best_ratio:
                        best_ratio = final_ratio
                        best_match_details = match

                confidence = round(best_ratio * 100, 2)

                # CASE 2, 3, 4: FOUND (Classification based on score)
                if confidence >= 85:
                    status = "VERIFIED MATCH"
                elif confidence >= 50:
                    status = "REVIEW REQUIRED"
                else:
                    status = "MISMATCH"

                print(f"📊 Result: {status} ({confidence}%)")
                if best_match_details:
                    print(f"🥅 Matched: {best_match_details.get('kra_citation', '')}")

            # Update item
            item['status'] = status
            item['confidence_score'] = f"{confidence}%"
            item['best_match_kra_ref'] = best_match_details.get('kra_ref', 'N/A')
            item['best_match_kra_citation'] = best_match_details.get('kra_citation', 'N/A')

            reconciled_data.append(item)

        print("\n✅ Comparison complete.")
        return reconciled_data

    def report(self, data: list | None = None) -> bool:
        """
        Saves the final reconciled data to CSV/Excel
        """
        import pandas as pd
        if not data:
            print("⚠️ No data to save.")
            return False

        df = pd.DataFrame(data)
        # Dropping complex columns
        if 'matches' in df.columns:
            df = df.drop(columns=['matches'])

        # Renaming Columns
        df.rename(
            columns={
                "original_case": "Case Number",
                "case_name": "Citation",
                "search_keyword": "Search Keyword",
                "matches_found": "Matches Found",
                "status": "Status",
                "confidence_score": "Confidence",
                "best_match_kra_ref": "Closest I. Ref Match",
                "best_match_kra_citation": "Closest Citation Match"
            },

            inplace=True
        )

        # Timestamping
        timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")

        # Path Settings for Storing Reports
        parent_path = Path(".")
        save_dir = parent_path / "reports"

        save_dir.mkdir(parents=True, exist_ok=True)

        output_path = save_dir / f"reconciliation_report_{timestamp}.xlsx"
        resolved_output_path = output_path.resolve()

        print(f"\nAttempting to save to: {output_path.resolve()}")

        try:
            df.to_excel(output_path, index=False)

        except Exception as e:
            errhandler(e, log="report", path="scrapper")

            return False
        else:
            syshandler(f"Reconciliation report has been generated & saved to {output_path.resolve()}", log="report", path="scrapper")

            return True

