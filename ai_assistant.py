"""
AI Assistant for Data Reconciliation Toolkit
Provides intelligent assistance and speeds up reconciliation tasks
"""

import json
import random
from datetime import datetime
from typing import Optional, List, Dict, Any
import re

class AIAssistant:
    """
    AI-powered assistant for legal data reconciliation
    """

    def __init__(self):
        self.name = "KRA (Intelligent Records Reconciliation Assistant)"
        self.version = "1.0.0"
        self.context = {}
        self.response_templates = self._load_templates()
        self.knowledge_base = self._load_knowledge_base()

    def _load_templates(self):
        """Load response templates"""
        return {
            "greeting": [
                "Hello! I'm {name}, your legal reconciliation assistant. How can I help you today?",
                "Hi there! {name} at your service. Ready to assist with your reconciliation tasks.",
                "Greetings! I'm {name}. What would you like to know about the reconciliation process?"
            ],
            "farewell": [
                "Goodbye! Feel free to ask if you need any help.",
                "See you later! I'm always here when you need assistance.",
                "Take care! Don't hesitate to return if you have more questions."
            ],
            "help": [
                "I can help you with:\n" +
                "• Understanding reconciliation results\n" +
                "• Explaining status types (VERIFIED MATCH, REVIEW REQUIRED, MISMATCH, NOT FOUND)\n" +
                "• Guiding you through the reconciliation process\n" +
                "• Analyzing data patterns\n" +
                "• Generating insights from your reports\n\n" +
                "What would you like to know?"
            ],
            "status_explanation": {
                "VERIFIED MATCH": "A **VERIFIED MATCH** means our system found a corresponding record in the KRA database with high confidence (≥85%). The case details align closely with what's in the system.",
                "REVIEW REQUIRED": "**REVIEW REQUIRED** indicates a potential match with moderate confidence (50-84%). The system found similar records, but you should manually verify before accepting.",
                "MISMATCH": "**MISMATCH** means we found records in the KRA system, but they don't align well with your data (confidence <50%). The case might be incorrectly cited or using different naming conventions.",
                "NOT FOUND": "**NOT FOUND** means no matching records were discovered in the KRA database. This could be due to:\n• Case not yet in the system\n• Incorrect case number format\n• Very recent filings not yet indexed"
            },
            "process_guide": [
                "The reconciliation process has 4 main steps:\n\n" +
                "1️⃣ **Upload** - Upload your Excel or CSV file containing case data\n" +
                "2️⃣ **Mapping** - Map your columns to Case Number and Citation fields\n" +
                "3️⃣ **Processing** - System searches KRA database and analyzes matches\n" +
                "4️⃣ **Results** - Review findings and export reports\n\n" +
                "Would you like details on any specific step?",

                "Here's how reconciliation works:\n\n" +
                "• **Scanner** extracts case numbers and citations from your file\n" +
                "• **Scrapper** securely logs into KRA iLaw system and searches each case\n" +
                "• **Comparator** uses fuzzy matching algorithms to find best matches\n" +
                "• **Reporter** generates color-coded Excel reports with status indicators\n\n" +
                "The system uses token-based and string-based matching for accuracy."
            ],
            "confidence_explanation": "The **confidence score** is calculated using two methods:\n\n" +
                                     "1️⃣ **Token Match**: Compares meaningful words (ignoring common terms like 'VS', 'KENYA', 'KRA')\n" +
                                     "2️⃣ **String Match**: Compares the cleaned citation text as a whole\n\n" +
                                     "The higher of these two scores becomes the final confidence percentage.\n\n" +
                                     "**Thresholds:**\n" +
                                     "• ≥85%: VERIFIED MATCH ✅\n" +
                                     "• 50-84%: REVIEW REQUIRED ⚠️\n" +
                                     "• <50%: MISMATCH ❌",

            "quick_analysis": "Based on your current data:\n\n" +
                             "• Total records: {total}\n" +
                             "• Verified matches: {verified} ({verified_pct:.1f}%)\n" +
                             "• Needs review: {review} ({review_pct:.1f}%)\n" +
                             "• Issues found: {issues} ({issues_pct:.1f}%)\n\n" +
                             "Would you like me to suggest which cases to prioritize for review?",

            "default": "I understand you're asking about '{query}'. Could you please provide more details or rephrase your question? You can ask me about reconciliation statuses, process steps, confidence scores, or request data analysis."
        }

    def _load_knowledge_base(self):
        """Load knowledge base about legal terms and common issues"""
        return {
            "common_issues": [
                "**Missing case numbers**: Ensure your Case Number column contains values",
                "**Format mismatches**: KRA system expects case numbers in format like 'TAT 123 OF 2023'",

                "**Special characters**: Remove or clean special characters in citations",
                "**Partial data**: Make sure both Case Number and Citation columns are filled"
            ],
            "tips": [
                "💡 **Tip**: Use consistent case number formatting for better matches",
                "💡 **Tip**: The system automatically handles common variations like 'vs' vs 'versus'",
                "💡 **Tip**: Review REQUIRED cases first - they're most likely to be correct with minor issues",
                "💡 **Tip**: Export reports regularly for audit trail purposes",
                "💡 **Tip**: Check the confidence score details to understand why a case was flagged"
            ],
            "legal_terms": {
                "TAT": "Tax Appeals Tribunal - handles tax disputes",
                "HC": "High Court of Kenya",
                "CA": "Court of Appeal",
                "SU": "Supreme Court",
                "KRA": "Kenya Revenue Authority - the respondent in most tax cases"
            }
        }

    def get_response(self, query: str, data: Optional[List[Dict]] = None) -> str:
        """
        Get AI response based on user query and optional data context
        """
        query = query.lower().strip()

        # Update context with current data if provided
        if data:
            self.context['current_data'] = data
            self.context['data_summary'] = self._summarize_data(data)

        # Check for greetings
        if any(word in query for word in ['hello', 'hi', 'hey', 'greetings']):
            return random.choice(self.response_templates["greeting"]).format(name=self.name)

        # Check for farewell
        if any(word in query for word in ['bye', 'goodbye', 'see you', 'farewell']):
            return random.choice(self.response_templates["farewell"])

        # Check for help
        if query in ['help', 'what can you do', 'capabilities', '?']:
            return self.response_templates["help"]

        # Status explanations
        if any(word in query for word in ['verified', 'match']):
            return self.response_templates["status_explanation"]["VERIFIED MATCH"]

        if any(word in query for word in ['review', 'required', 'needs review']):
            return self.response_templates["status_explanation"]["REVIEW REQUIRED"]

        if any(word in query for word in ['mismatch', 'not matching']):
            return self.response_templates["status_explanation"]["MISMATCH"]

        if any(word in query for word in ['not found', 'missing']):
            return self.response_templates["status_explanation"]["NOT FOUND"]

        # Process guide
        if any(word in query for word in ['process', 'how to', 'how does', 'steps']):
            return random.choice(self.response_templates["process_guide"])

        # Confidence explanation
        if any(word in query for word in ['confidence', 'score', 'percentage']):
            return self.response_templates["confidence_explanation"]

        # Analysis request
        if any(word in query for word in ['analyze', 'summary', 'overview', 'stats']):
            if 'data_summary' in self.context:
                summary = self.context['data_summary']
                return self.response_templates["quick_analysis"].format(**summary)
            else:
                return "I'd be happy to analyze your data! Please run a reconciliation first or upload a report."

        # Tips request
        if any(word in query for word in ['tip', 'tips', 'advice', 'suggestion']):
            return random.choice(self.knowledge_base["tips"])

        # Common issues
        if any(word in query for word in ['issue', 'problem', 'trouble', 'error']):
            return "Here are common issues users encounter:\n\n" + "\n".join(self.knowledge_base["common_issues"])

        # Unmatched cases
        if any(word in query for word in ['unmatched', 'unverified', 'pending']):
            if 'current_data' in self.context:
                unmatched = [d for d in self.context['current_data'] 
                           if d.get('status') not in ['VERIFIED MATCH']]
                if unmatched:
                    response = f"I found {len(unmatched)} cases that need attention:\n\n"
                    for i, case in enumerate(unmatched[:5]):
                        response += f"• **{case.get('original_case', 'Unknown')}** - {case.get('status', 'Unknown')} ({case.get('confidence_score', 'N/A')})\n"
                    if len(unmatched) > 5:
                        response += f"\n...and {len(unmatched) - 5} more cases. Would you like to see them all?"
                    return response
                else:
                    return "Great news! All your cases are verified matches. No action needed."
            else:
                return "I don't have any data to analyze. Please run a reconciliation first."

        # Specific case query
        if 'case' in query or 'number' in query:
            # Try to extract case number from query
            case_match = re.search(r'[A-Z]+\s*\d+\s*[A-Z]*\s*\d*', query.upper())
            if case_match and 'current_data' in self.context:
                case_num = case_match.group()
                for case in self.context['current_data']:
                    if case_num in case.get('original_case', '').upper():
                        return self._get_case_details(case)
                return f"I couldn't find case '{case_num}' in your current data. Please check the number or try a different one."

        # Default response
        return self.response_templates["default"].format(query=query)

    def _summarize_data(self, data: List[Dict]) -> Dict:
        """Generate summary statistics from data"""
        total = len(data)
        verified = sum(1 for d in data if d.get('status') == 'VERIFIED MATCH')
        review = sum(1 for d in data if d.get('status') == 'REVIEW REQUIRED')
        mismatch = sum(1 for d in data if d.get('status') == 'MISMATCH')
        not_found = sum(1 for d in data if d.get('status') == 'NOT FOUND')

        return {
            'total': total,
            'verified': verified,
            'verified_pct': (verified / total * 100) if total > 0 else 0,
            'review': review,
            'review_pct': (review / total * 100) if total > 0 else 0,
            'issues': mismatch + not_found,
            'issues_pct': ((mismatch + not_found) / total * 100) if total > 0 else 0
        }

    def _get_case_details(self, case: Dict) -> str:
        """Get detailed information about a specific case"""
        details = f"**Case Details:**\n\n"
        details += f"• **Case Number**: {case.get('original_case', 'N/A')}\n"
        details += f"• **Citation**: {case.get('case_name', 'N/A')}\n"
        details += f"• **Status**: {case.get('status', 'N/A')}\n"
        details += f"• **Confidence**: {case.get('confidence_score', 'N/A')}\n"
        details += f"• **Best Match**: {case.get('best_match_kra_citation', 'N/A')}\n"
        details += f"• **KRA Reference**: {case.get('best_match_kra_ref', 'N/A')}\n\n"

        if case.get('matches'):
            details += f"**Total matches found**: {len(case.get('matches', []))}\n"

        return details

    def generate_report_summary(self, data: List[Dict]) -> str:
        """Generate a natural language summary of reconciliation results"""
        summary = self._summarize_data(data)

        report = f"📊 **Reconciliation Report Summary**\n\n"
        report += f"Processed **{summary['total']}** records on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n\n"

        report += f"✅ **Verified Matches**: {summary['verified']} ({summary['verified_pct']:.1f}%)\n"
        report += f"⚡ **These cases are ready for closing or further processing.**\n\n"

        if summary['review'] > 0:
            report += f"⚠️ **Review Required**: {summary['review']} ({summary['review_pct']:.1f}%)\n"
            report += f"**Priority cases to review:**\n"
            # Add sample cases needing review
            review_cases = [d for d in data if d.get('status') == 'REVIEW REQUIRED'][:3]
            for case in review_cases:
                report += f"  • {case.get('original_case', 'Unknown')} - {case.get('confidence_score', 'N/A')} confidence\n"
            report += "\n"

        if summary['issues'] > 0:
            report += f"❌ **Issues Found**: {summary['issues']} ({summary['issues_pct']:.1f}%)\n"
            report += f"**These cases need investigation:**\n"
            issue_cases = [d for d in data if d.get('status') in ['MISMATCH', 'NOT_FOUND']][:3]
            for case in issue_cases:
                report += f"  • {case.get('original_case', 'Unknown')} - {case.get('status', 'Unknown')}\n"

        report += f"\n💡 **Recommendation**: {'All clear!' if summary['issues'] == 0 else 'Focus on REVIEW REQUIRED cases first, then investigate MISMATCH/ NOT FOUND.'}"

        return report