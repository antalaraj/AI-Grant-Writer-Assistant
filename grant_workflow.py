"""Evidence-first grant research and quality-gated report generation.

Quality scores are internal checklist scores, not guarantees of funding success.
The workflow prioritizes official sources, labels uncertainty, audits drafts, and
uses a bounded revision pass without making up missing grant facts.
"""
import json
import logging
import os
import re
from datetime import date
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

GROQ_MODEL = "openai/gpt-oss-120b"
GEMINI_MODEL = "gemini-3.8-flash"
HTTP_TIMEOUT_SECONDS = 60
MAX_REVISION_ATTEMPTS = 1
logger = logging.getLogger(__name__)

OFFICIAL_DOMAIN_HINTS = (
    ".gov.in", ".nic.in", ".gov", "mygov.in", "csr.gov.in",
    "india.gov.in", "education.gov.in", "gujarat.gov.in",
    "niti.gov.in", "mca.gov.in", "ngodarpan.gov.in",
)
LOW_TRUST_DOMAIN_HINTS = (
    "linkedin.com", "medium.com", "wikipedia.org", "grantoria",
    "fundinglandscape.com",
)


def _post_json(url: str, payload: dict, headers: dict | None = None,
               timeout: int = HTTP_TIMEOUT_SECONDS) -> dict:
    body = json.dumps(payload).encode("utf-8")
    request_headers = {
        "Content-Type": "application/json",
        "User-Agent": "AI-Grant-Writer-Assistant/1.1",
    }
    if headers:
        request_headers.update(headers)
    req = Request(url, data=body, headers=request_headers, method="POST")
    try:
        with urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"AI provider returned HTTP {exc.code}: {details[:1000]}") from None
    except (URLError, TimeoutError) as exc:
        raise RuntimeError(f"Could not reach AI provider: {type(exc).__name__}") from None
    except json.JSONDecodeError:
        raise RuntimeError("AI provider returned invalid JSON.") from None


def _groq_chat(system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not configured.")
    data = _post_json(
        "https://api.groq.com/openai/v1/chat/completions",
        {"model": GROQ_MODEL, "temperature": temperature,
         "messages": [{"role": "system", "content": system_prompt},
                      {"role": "user", "content": user_prompt}]},
        {"Authorization": f"Bearer {api_key}"},
    )
    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError):
        raise RuntimeError("Groq returned an unexpected response.") from None


def _gemini_generate(prompt: str, timeout: int = 20) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured.")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    data = _post_json(
        url, {"contents": [{"parts": [{"text": prompt}]}],
              "generationConfig": {"temperature": 0.1}},
        {"x-goog-api-key": api_key}, timeout=timeout,
    )
    try:
        return "\n".join(p.get("text", "") for p in data["candidates"][0]["content"]["parts"]).strip()
    except (KeyError, IndexError, TypeError):
        raise RuntimeError("Gemini returned no usable text.") from None


def _domain(url: str) -> str:
    try:
        return (urlparse(url).hostname or "").lower().removeprefix("www.")
    except ValueError:
        return ""


def _source_tier(url: str) -> str:
    domain = _domain(url)
    if not domain:
        return "No URL"
    if any(hint in domain for hint in LOW_TRUST_DOMAIN_HINTS):
        return "Secondary / low confidence"
    if any(domain == hint or domain.endswith(hint) for hint in OFFICIAL_DOMAIN_HINTS):
        return "Potential official source (verify page)"
    return "Third-party / unverified"


def _mission_terms(mission: str) -> list[str]:
    stop = {"about", "their", "there", "which", "where", "would", "could",
            "should", "with", "from", "that", "this", "have", "help",
            "into", "under", "over", "more", "than", "they", "them"}
    terms = [w.lower() for w in re.findall(r"[A-Za-z]{4,}", mission)
             if w.lower() not in stop]
    # Use distinctive terms only; avoid passing a paragraph as a search query.
    return list(dict.fromkeys(terms))[:5]


def _search_grants(org_type: str, mission: str, today: str) -> str:
    try:
        from ddgs import DDGS
    except ImportError:
        raise RuntimeError("The ddgs search dependency is not installed.") from None

    terms = " ".join(_mission_terms(mission))
    queries = [
        f'"{org_type}" grant application official India {today}',
        f'India Gujarat grants {terms} NGO official application',
        f'site:gov.in {terms} scheme grant application',
        f'site:gujarat.gov.in {terms} grant scheme',
        f'India CSR foundation funding {terms} official NGO',
        f'site:ngodarpan.gov.in grant NGO scheme',
    ]
    found, seen = [], set()
    with DDGS() as search:
        for query in queries:
            try:
                for item in search.text(query, max_results=5) or []:
                    url = (item.get("href") or item.get("url") or "").strip()
                    if not url or url in seen:
                        continue
                    seen.add(url)
                    found.append({
                        "title": item.get("title", "Untitled result"),
                        "url": url,
                        "domain": _domain(url),
                        "source_tier": _source_tier(url),
                        "snippet": (item.get("body", "") or "")[:350],
                        "verification_status": "Search result only; page not independently verified",
                    })
            except Exception as exc:
                logger.warning("Search query failed (%s).", type(exc).__name__)

    # Official-looking domains first; this is source triage, not proof of validity.
    found.sort(key=lambda x: (
        0 if x["source_tier"] == "Potential official source (verify page)" else
        2 if x["source_tier"] == "Secondary / low confidence" else 1,
        x["domain"],
    ))
    if not found:
        found = [{
            "title": "No search results available", "url": "", "domain": "",
            "source_tier": "No URL",
            "snippet": "Search returned no usable results. Do not invent grants.",
            "verification_status": "No evidence",
        }]
    logger.info("Grant search completed with %d unique result records.", len(found))
    return json.dumps(found[:10], ensure_ascii=False, indent=2)


def _quality_review(report: str, org_type: str, mission: str, today: str) -> str:
    """Return a structured, evidence-based checklist score and required fixes."""
    return _groq_chat(
        "You are a strict grant-report quality auditor. Be conservative and evidence-led. "
        "Do not award points for confident wording unsupported by evidence. Return valid JSON only.",
        f"""Audit this report for a real applicant.
Date: {today}
Organization type: {org_type}
Mission: {mission}

Score each criterion from 0 to its maximum:
- source quality and direct official URLs (20)
- evidence-backed opportunity status, deadlines, and eligibility (20)
- tailoring to applicant mission and geography (15)
- completeness of all 10 required report sections (15)
- actionable, internally consistent proposal plan (10)
- budget logic without invented costs or unsupported totals (5)
- measurable KPIs with baseline/target/timeframe and labelled assumptions (5)
- risk mitigation and submission roadmap (5)
- clear separation of facts, assumptions, and unknowns (5)

Return JSON with keys total_score (integer 0-100), criteria (object of criterion scores),
critical_issues (array), unsupported_claims (array), missing_sections (array),
required_fixes (array). Do not give a perfect score if any grant is called confirmed open
without explicit official evidence, if third-party sources are presented as official, or
if invented applicant facts/metrics are presented as facts.

REPORT:
{report}""",
        temperature=0.0,
    )


def _parse_review(review: str) -> dict:
    try:
        cleaned = re.sub(r"^\s*```(?:json)?|\`\`\`\s*$", "", review.strip(), flags=re.I)
        data = json.loads(cleaned)
        if not isinstance(data, dict):
            raise ValueError("Review must be an object")
        score = int(data.get("total_score", 0))
        data["total_score"] = max(0, min(100, score))
        return data
    except (ValueError, TypeError, json.JSONDecodeError):
        return {"total_score": 0, "critical_issues": ["Quality review returned invalid JSON."],
                "required_fixes": ["Manually review source quality, eligibility, deadlines, and all sections."]}


def generate_grant_report(org_type: str, mission: str) -> str:
    """Search, validate, draft, score, and revise a grant strategy report."""
    today = date.today().isoformat()
    logger.info("Grant workflow stage=search started.")
    sources = _search_grants(org_type, mission, today)

    logger.info("Grant workflow stage=research started.")
    research = _groq_chat(
        "You are an evidence-first grant researcher. Use only supplied search records. "
        "Never invent a grant, funder, deadline, amount, eligibility rule, or URL. "
        "A search snippet is not proof that a call is open. Prefer primary official sources.",
        f"""Current date: {today}
Applicant type: {org_type}
Mission: {mission}
Search records (unverified):
{sources}

Return up to 5 leads in a table-like structured list. For each include exact program/funder
name only when supported, URL exactly as supplied, source tier, evidence excerpt, geography,
applicant eligibility, deadline, award amount, status, fit rationale, and unknowns.
Allowed status labels: "Verified open" only if supplied evidence explicitly confirms a current
open call and deadline; "Potential lead"; "Closed/expired" only if evidence says so;
"Eligibility unclear"; "Insufficient evidence". Do not infer eligibility from mission fit.
If no credible lead exists, say no verified matching call was found. List the most useful
official pages to check next without claiming they were verified.""",
    )

    try:
        logger.info("Grant workflow stage=gemini_validation started.")
        validation = _gemini_generate(
            f"""Act as an independent skeptical reviewer. Do not claim you browsed or opened pages.
Date: {today}; applicant type: {org_type}; mission: {mission}
Research:
{research}
Identify unsupported claims, expired/missing deadlines, applicant-type/geography mismatch,
missing official evidence, and status-label errors. For every lead, require direct official
evidence before "Verified open". Return concise corrections. Mark unknowns explicitly."""
        )
    except Exception as exc:
        logger.warning("Gemini validation unavailable (%s).", type(exc).__name__)
        validation = ("INDEPENDENT SECOND-PASS UNAVAILABLE. Treat all leads as unverified; "
                      "do not label any opportunity Verified open or eligible without direct "
                      "official evidence. Verify eligibility, deadline, amount, and URL manually.")

    system = (
        "You are a senior grant strategist and meticulous editor. Produce useful, polished "
        "Markdown, grounded in evidence. Never fabricate facts, citations, grant terms, budget "
        "numbers, outcomes, or applicant history. Label proposed targets as illustrative and "
        "requiring applicant approval. If research is weak, say so and give a research plan."
    )
    prompt = f"""Create a comprehensive Grant Strategy Report.
Current date: {today}
Organization type: {org_type}
Mission: {mission}

RESEARCH EVIDENCE:
{research}

VALIDATION:
{validation}

Use exactly these sections and keep them substantive:
## 1. Executive Summary
## 2. Organizational Overview
## 3. Problem Statement
## 4. Proposed Solution & Innovation
## 5. Funder Value Proposition
## 6. 1-Page Proposal Skeleton (Headings + Bullet Points)
## 7. Budget Logic Overview
## 8. Impact Metrics & KPIs
## 9. Risk & Mitigation
## 10. 5-Step Submission Roadmap
## 11. Grant Opportunity Evidence Table
## 12. Sources and Verification Checklist

Rules:
- Explicitly say when no matching open call is verified; never imply that a lead is open merely
  because it appeared in search.
- In section 11 include program/funder, URL, source tier, status, evidence available, fit,
  deadline/amount only if supported, and verification needed.
- Cite each grant-specific factual claim with its source URL inline. Do not cite generic articles
  as proof of a current grant call.
- Use "Not provided by applicant" for missing organizational facts; do not invent registration,
  track record, staff, partnerships, or prior outcomes.
- Proposed KPIs must be labelled "illustrative targets—confirm with applicant"; state baseline,
  measurement method, frequency, and timeframe where possible. Do not promise impact.
- Budget must be a structure, not fabricated rupee amounts. Include categories and explain that
  figures require local quotations and funder rules.
- Include applicant eligibility, geography, deadline, award size, matching funds, required
  documents, and official application link in the verification checklist.
- Avoid US-only sources unless the applicant explicitly seeks US funding.
- Provide clear next actions even if no verified opportunity is found."""

    logger.info("Grant workflow stage=initial_report started.")
    report = _groq_chat(system, prompt, temperature=0.15)

    # The draft is the deliverable. Auditing and revision are enhancements, so
    # rate limits or malformed audit output must never turn a usable draft into HTTP 500.
    review_data = {
        "total_score": None,
        "critical_issues": ["Automated quality audit could not be completed; manual review required."],
        "required_fixes": ["Verify official grant pages, eligibility, deadlines, and all factual claims."],
        "unsupported_claims": [],
    }
    audit_succeeded = False
    try:
        logger.info("Grant workflow stage=quality_audit started.")
        review_text = _quality_review(report, org_type, mission, today)
        parsed_review = _parse_review(review_text)
        if parsed_review.get("total_score", 0) > 0 and isinstance(parsed_review.get("required_fixes", []), list):
            review_data = parsed_review
            audit_succeeded = True
    except Exception as exc:
        # In particular, Groq 429/TPM errors must not trigger another expensive call.
        logger.warning("Quality audit unavailable (%s); keeping original draft.", type(exc).__name__)

    if audit_succeeded:
        logger.info("Report quality audit score=%s/100.", review_data["total_score"])
    else:
        logger.info("Report quality audit unavailable; score not calculated.")

    # Only revise after a successful audit, and never lose the original draft if
    # the optional revision call fails. One short attempt avoids a retry storm.
    if audit_succeeded and review_data["total_score"] < 95:
        logger.info("Grant workflow stage=quality_revision started.")
        try:
            fixes = review_data.get("required_fixes", [])[:6]
            critical = review_data.get("critical_issues", [])[:6]
            compact_report = report[:9000]
            revised = _groq_chat(
                system,
                f"""Improve this grant report. Apply only these highest-priority fixes:
{json.dumps({"critical_issues": critical, "required_fixes": fixes}, ensure_ascii=False)}
Do not invent facts or grant details. Keep all 12 report sections, source URLs, and uncertainty labels.
Return the complete revised Markdown report.

CURRENT REPORT:
{compact_report}""",
                temperature=0.1,
            )
            if revised and len(revised) > 1000:
                report = revised
            else:
                logger.warning("Revision response was unexpectedly short; keeping original draft.")
        except Exception as exc:
            logger.warning("Quality revision unavailable (%s); keeping original draft.", type(exc).__name__)

    # Append transparent QA information; never imply the score guarantees funding success.
    qa = {
        "internal_checklist_score": review_data.get("total_score") if audit_succeeded else None,
        "score_interpretation": "Automated checklist estimate, not a guarantee of accuracy, eligibility, or funding success. Null means the audit could not run.",
        "critical_issues": review_data.get("critical_issues", []) if review_data else [],
        "remaining_fixes": review_data.get("required_fixes", []) if review_data else [],
        "unsupported_claims_flagged": review_data.get("unsupported_claims", []) if review_data else [],
    }
    report += "\n\n## 13. Automated Quality Audit\n\n"
    report += "This is an internal checklist score, not a guarantee of funding success. "
    report += "Human verification of official funder pages is required before submission.\n\n"
    report += "```json\n" + json.dumps(qa, ensure_ascii=False, indent=2) + "\n```\n"
    logger.info("Grant workflow completed; final checklist score=%s/100.",
                qa["internal_checklist_score"])
    return report
