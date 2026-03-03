
import re
from difflib import SequenceMatcher
from typing import List, Dict, Optional, Tuple
from helpers import clean_citation, clean_citation_text, get_court_type

class EnhancedReconciler:
    """
    Advanced reconciliation with multiple matching strategies
    """
    
    def __init__(self):
        self.match_thresholds = {
            'exact': 1.0,
            'high': 0.85,
            'medium': 0.70,
            'low': 0.50
        }
    
    def reconcile(self, sheet_data: List[Dict], kra_data: List[Dict]) -> List[Dict]:
        """
        Perform enhanced reconciliation with multiple strategies
        """
        results = []
        
        for sheet_item in sheet_data:
            sheet_citation = str(sheet_item.get('citation', '')).upper()
            sheet_case = sheet_item.get('case_number', 'Unknown')
            
            # Get all available matches from KRA data
            matches = []
            for kra_item in kra_data:
                if kra_item.get('original_case') == sheet_case:
                    matches = kra_item.get('matches', [])
                    break
            
            # Apply multiple matching strategies
            best_match, confidence, strategy = self._find_best_match(
                sheet_citation, sheet_case, matches
            )
            
            # Determine status based on confidence
            status = self._determine_status(confidence)
            
            result = {
                'excel_row': sheet_item.get('excel_row'),
                'original_case': sheet_case,
                'case_name': sheet_citation,
                'search_keyword': sheet_item.get('keyword', ''),
                'matches_found': len(matches),
                'status': status,
                'confidence_score': f"{confidence:.1f}%",
                'confidence_raw': confidence,
                'matching_strategy': strategy,
                'best_match_kra_ref': best_match.get('kra_ref', 'N/A') if best_match else 'N/A',
                'best_match_kra_citation': best_match.get('kra_citation', 'N/A') if best_match else 'N/A',
                'best_match_kra_assignee': best_match.get('kra_assignee', 'N/A') if best_match else 'N/A',
                'matches': matches
            }
            
            results.append(result)
        
        return results
    
    def _find_best_match(self, sheet_citation: str, sheet_case: str, matches: List[Dict]) -> Tuple[Optional[Dict], float, str]:
        """
        Find best match using multiple strategies
        """
        if not matches:
            return None, 0.0, "no_matches"
        
        best_match = None
        best_confidence = 0.0
        best_strategy = ""
        
        for match in matches:
            kra_citation = str(match.get('kra_citation', '')).upper()
            
            # Strategy 1: Exact match (100%)
            if sheet_citation == kra_citation:
                return match, 100.0, "exact_match"
            
            # Strategy 2: Court type filtering + fuzzy matching
            sheet_court = get_court_type(sheet_case)
            kra_court = get_court_type(kra_citation)
            
            # Filter by court type if both are identifiable
            if sheet_court != 'NA' and kra_court != 'NA':
                if sheet_court != kra_court:
                    continue
            
            # Strategy 3: Token-based matching (ignoring order)
            sheet_tokens = clean_citation(sheet_citation)
            kra_tokens = clean_citation(kra_citation)
            
            if sheet_tokens and kra_tokens:
                token_ratio = self._calculate_token_match(sheet_tokens, kra_tokens)
                
                if token_ratio > best_confidence:
                    best_confidence = token_ratio
                    best_match = match
                    best_strategy = "token_match"
            
            # Strategy 4: String-based matching (preserving order)
            sheet_string = clean_citation_text(sheet_citation)
            kra_string = clean_citation_text(kra_citation)
            
            string_ratio = SequenceMatcher(None, sheet_string, kra_string).ratio() * 100
            
            if string_ratio > best_confidence:
                best_confidence = string_ratio
                best_match = match
                best_strategy = "string_match"
        
        return best_match, best_confidence, best_strategy
    
    def _calculate_token_match(self, sheet_tokens: set, kra_tokens: set) -> float:
        """
        Calculate match percentage based on token overlap with fuzzy matching
        """
        if not sheet_tokens:
            return 0.0
        
        matched_count = 0
        
        for s_token in sheet_tokens:
            best_match_ratio = 0.0
            for k_token in kra_tokens:
                # Check for exact match first
                if s_token == k_token:
                    best_match_ratio = 1.0
                    break
                
                # Fuzzy match for similar tokens
                ratio = SequenceMatcher(None, s_token, k_token).ratio()
                if ratio > best_match_ratio:
                    best_match_ratio = ratio
            
            if best_match_ratio >= 0.85:  # Threshold for token match
                matched_count += 1
        
        return (matched_count / len(sheet_tokens)) * 100
    
    def _determine_status(self, confidence: float) -> str:
        """
        Determine status based on confidence score
        """
        if confidence >= 85:
            return "VERIFIED MATCH"
        elif confidence >= 50:
            return "REVIEW REQUIRED"
        elif confidence > 0:
            return "MISMATCH"
        else:
            return "NOT FOUND"
    
    def get_reconciliation_summary(self, results: List[Dict]) -> Dict:
        """
        Generate summary statistics
        """
        total = len(results)
        verified = sum(1 for r in results if r['status'] == 'VERIFIED MATCH')
        review = sum(1 for r in results if r['status'] == 'REVIEW REQUIRED')
        mismatch = sum(1 for r in results if r['status'] == 'MISMATCH')
        not_found = sum(1 for r in results if r['status'] == 'NOT FOUND')
        
        return {
            'total': total,
            'verified': verified,
            'verified_pct': (verified / total * 100) if total else 0,
            'review': review,
            'review_pct': (review / total * 100) if total else 0,
            'mismatch': mismatch,
            'mismatch_pct': (mismatch / total * 100) if total else 0,
            'not_found': not_found,
            'not_found_pct': (not_found / total * 100) if total else 0,
            'avg_confidence': sum(r['confidence_raw'] for r in results) / total if total else 0
        }