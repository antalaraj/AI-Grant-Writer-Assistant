import json
import unittest

from grant_workflow import _normalize_report_structure


class ReportStructureTests(unittest.TestCase):
    def setUp(self):
        self.sources = json.dumps([
            {
                "title": "Official Gujarat Health Department funding page",
                "url": "https://gujarat.gov.in/health/funding",
                "domain": "gujarat.gov.in",
                "source_tier": "Potential official source (verify page)",
            },
            {
                "title": "CSR healthcare opportunities list",
                "url": "https://example.org/health-grants",
                "domain": "example.org",
                "source_tier": "Third-party / unverified",
            },
        ])

    def test_empty_opportunity_table_is_populated_from_search_urls(self):
        report = """## 1. Executive Summary
Summary.
## 2. Organizational Overview
Overview.
## 3. Problem Statement
Problem.
## 4. Proposed Solution & Innovation
Solution.
## 5. Funder Value Proposition
Value.
## 6. 1-Page Proposal Skeleton (Headings + Bullet Points)
Skeleton.
## 7. Budget Logic Overview
Budget.
## 8. Impact Metrics & KPIs
KPIs.
## 9. Risk & Mitigation
Risks.
## 10. 5-Step Submission Roadmap
Roadmap.
## 11. Grant Opportunity Evidence Table
| # |
"""
        result = _normalize_report_structure(report, self.sources)
        self.assertIn("[Open source](https://gujarat.gov.in/health/funding)", result)
        self.assertIn("[Open source](https://example.org/health-grants)", result)
        self.assertIn("Unverified lead", result)
        self.assertIn("12. Sources and Verification Checklist", result)
        self.assertNotIn("| # |", result)

    def test_does_not_claim_search_results_are_verified_open_grants(self):
        result = _normalize_report_structure(
            "## 11. Grant Opportunity Evidence Table\n| # |\n",
            self.sources,
        )
        self.assertIn("not confirmed grant calls", result.lower())
        self.assertIn("Unverified lead", result)
        self.assertNotIn("| Verified open |", result)

    def test_section_12_is_added_before_section_13(self):
        report = """## 1. Executive Summary
Summary.
## 11. Grant Opportunity Evidence Table
| # |
## 13. Automated Quality Audit
Audit.
"""
        result = _normalize_report_structure(report, self.sources)
        self.assertLess(result.index("## 12. Sources and Verification Checklist"),
                        result.index("## 13. Automated Quality Audit"))

    def test_valid_alternate_heading_does_not_get_duplicate_placeholder(self):
        report = """## 1. Executive Summary
Summary.
## 2. Organizational Overview
Overview.
## 3. Problem Statement
Problem.
## 4. Proposed Solution & Innovation
Solution.
## 5. Funder Value Proposition
Value.
## 6. 1-Page Proposal Skeleton (Headings + Bullet Points)
This is real skeleton content, not a missing section.
## 7. Budget Logic Overview
Budget.
## 8. Impact Metrics & KPIs
KPIs.
## 9. Risk & Mitigation
Risks.
## 10. 5-Step Submission Roadmap
Roadmap.
## 11. Grant Opportunity Evidence Table
| # |
## 12. Sources and Verification Checklist
Checklist.
"""
        result = _normalize_report_structure(report, self.sources)
        self.assertEqual(result.count("## 6. 1-Page Proposal Skeleton"), 1)
        self.assertEqual(result.count("## 10. 5-Step Submission Roadmap"), 1)
        self.assertNotIn("This section was missing from the generated draft", result)

    def test_missing_section_is_inserted_once_in_numeric_order(self):
        report = """## 1. Executive Summary
Summary.
## 2. Organizational Overview
Overview.
## 4. Proposed Solution & Innovation
Solution.
## 11. Grant Opportunity Evidence Table
| # |
"""
        result = _normalize_report_structure(report, self.sources)
        self.assertEqual(result.count("## 3. Problem Statement"), 1)
        self.assertLess(result.index("## 3. Problem Statement"),
                        result.index("## 4. Proposed Solution & Innovation"))

    def test_portal_sources_are_not_labelled_as_open_grants(self):
        portal_sources = json.dumps([{
            "title": "National CSR Exchange Portal",
            "url": "https://www.csrxchange.gov.in/Frontend/",
            "domain": "csrxchange.gov.in",
            "source_tier": "Official Government of India portal",
            "record_type": "portal",
            "verification_status": "Portal only; no matching open call verified",
        }])
        result = _normalize_report_structure(
            "## 11. Grant Opportunity Evidence Table\n| # |\n",
            portal_sources,
        )
        self.assertIn("Portal only; no call verified", result)
        self.assertNotIn("| Verified open |", result)
        self.assertIn("csrxchange.gov.in", result)


if __name__ == "__main__":
    unittest.main()
