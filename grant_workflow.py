"""Lightweight grant-writing workflow for Vercel serverless deployment.

Uses direct provider HTTP APIs instead of CrewAI/LangChain to keep the
Python function bundle below Vercel's 500 MB limit.
"""
import json
import logging
import os
from datetime import date
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

GROQ_MODEL = "openai/gpt-oss-120b"
GEMINI_MODEL = "gemini-3.8-flash"
HTTP_TIMEOUT_SECONDS = 90
logger = logging.getLogger(__name__)


def _post_json(
    url: str,
    payload: dict,
    headers: dict | None = None,
    timeout: int = HTTP_TIMEOUT_SECONDS,
) -> dict:
    """POST JSON and return the decoded response with useful API errors."""
    body = json.dumps(payload).encode("utf-8")
    request_headers = {
        "Content-Type": "application/json",
        # Groq's Cloudflare edge rejects urllib's default Python-urllib user agent
        # with HTTP 403 / error 1010. Identify this application explicitly.
        "User-Agent": "AI-Grant-Writer-Assistant/1.0",
    }
    if headers:
        request_headers.update(headers)
    req = Request(url, data=body, headers=request_headers, method="POST")
    try:
        with urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        # Provider responses can contain request details; never include secrets.
        raise RuntimeError(
            f"AI provider returned HTTP {exc.code}: {details[:1200]}"
        ) from None
    except (URLError, TimeoutError) as exc:
        raise RuntimeError(f"Could not reach AI provider: {exc}") from None
    except json.JSONDecodeError:
        raise RuntimeError("AI provider returned an invalid JSON response.") from None


def _groq_chat(system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not configured.")
    data = _post_json(
        "https://api.groq.com/openai/v1/chat/completions",
        {
            "model": GROQ_MODEL,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        },
        {"Authorization": f"Bearer {api_key}"},
    )
    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError):
        raise RuntimeError("Groq returned an unexpected chat-completion response.") from None


def _gemini_generate(prompt: str, timeout: int = 25) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured.")
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent"
    )
    data = _post_json(
        url,
        {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1},
        },
        {"x-goog-api-key": api_key},
        timeout=timeout,
    )
    try:
        parts = data["candidates"][0]["content"]["parts"]
        return "\n".join(part.get("text", "") for part in parts).strip()
    except (KeyError, IndexError, TypeError):
        feedback = data.get("promptFeedback", {}).get("blockReason", "unknown response")
        raise RuntimeError(f"Gemini returned no usable text ({feedback}).") from None


def _search_grants(org_type: str, mission: str, today: str) -> str:
    """Find recent candidate grants using DuckDuckGo, without LangChain."""
    try:
        from ddgs import DDGS
    except ImportError as exc:
        raise RuntimeError("The ddgs search dependency is not installed.") from exc

    # Keep search queries short and focused. Sending the full mission text to
    # search engines produces noisy URLs and less relevant results.
    queries = [
        f"{org_type} grant funding opportunity official deadline {today}",
        f"India Gujarat NGO education grants official application {today}",
        f"CSR education funding India official NGO application",
    ]
    found = []
    seen_urls = set()
    with DDGS() as search:
        for query in queries:
            try:
                results = search.text(query, max_results=5)
                for item in results or []:
                    url = item.get("href") or item.get("url") or ""
                    if not url or url in seen_urls:
                        continue
                    seen_urls.add(url)
                    found.append({
                        "title": item.get("title", "Untitled result"),
                        "url": url,
                        "snippet": item.get("body", ""),
                    })
            except Exception as exc:
                found.append({
                    "title": "Search query warning",
                    "url": "",
                    "snippet": f"Search did not complete for one query: {type(exc).__name__}",
                })
    if not found:
        # Search may return zero results in a serverless environment. Continue
        # without evidence rather than failing before the AI workflow can run.
        logger.warning("Grant search returned zero results; continuing without web evidence.")
        found.append({
            "title": "No search results available",
            "url": "",
            "snippet": (
                "The web search returned no results. Do not name or rank specific grants "
                "unless supported by supplied evidence. Tell the user to verify opportunities "
                "directly with official funders."
            ),
        })
    logger.info("Grant search completed with %d result records.", len(found))
    return json.dumps(found[:12], ensure_ascii=False, indent=2)


def generate_grant_report(org_type: str, mission: str) -> str:
    """Search, validate, and draft a Markdown grant strategy report."""
    today = date.today().isoformat()
    logger.info("Grant workflow stage=search started.")
    sources = _search_grants(org_type, mission, today)

    logger.info("Grant workflow stage=groq_research started.")
    research = _groq_chat(
        "You are a careful grant research analyst. Use only the supplied search results. "
        "Never invent funders, amounts, deadlines, eligibility rules, or URLs. "
        "Distinguish verified facts from items requiring confirmation.",
        f"""Date today: {today}
Organization type: {org_type}
Mission: {mission}

Search results (unverified; check each official source):
{sources}

Identify up to 3 relevant grant opportunities. For each provide funder/program, official URL,
award amount only if stated in the supplied results, deadline only if stated, likely fit,
and what still needs verification. If no credible opportunity is evident, say so.""",
    )

    logger.info("Grant workflow stage=gemini_validation started.")
    try:
        validation = _gemini_generate(
            f"""You are a strict grant eligibility and fact-checking reviewer.
Today's date: {today}
Applicant organization type: {org_type}
Mission: {mission}

Research notes:
{research}

Review each candidate. Do not claim you independently verified a website unless the supplied
evidence proves it. Mark unknown details as "Needs official verification". Flag deadlines
that are missing, past, or ambiguous. Check entity type, geography, stage, matching funds,
and financial constraints where information is available. Rank opportunities Highest Match,
Medium Match, or Rejected, and explain risks. Never invent facts."""
        )
    except Exception as exc:
        # Gemini is an optional second-pass reviewer. A timeout must not discard
        # the research already produced by Groq or prevent the final report.
        logger.warning(
            "Gemini validation unavailable (%s); continuing with explicit verification caveat.",
            type(exc).__name__,
        )
        validation = (
            "SECOND-PASS VALIDATION UNAVAILABLE. Gemini validation failed or timed out. "
            "Do not treat any candidate as confirmed open or eligible. Mark deadlines, "
            "eligibility, award amounts, and application links as needing verification "
            "directly on the funder's official website."
        )

    logger.info("Grant workflow stage=groq_report started.")
    report = _groq_chat(
        "You are a grant proposal strategist. Write concise, credible, reviewer-friendly Markdown. "
        "Do not invent organizational facts, grant terms, budgets, metrics, or deadlines. "
        "Label assumptions and verification gaps clearly.",
        f"""Create a Grant Strategy Report for:
Organization type: {org_type}
Mission: {mission}
Date: {today}

Research notes:
{research}

Eligibility review:
{validation}

Use exactly these sections:
## 1. Executive Summary
## 2. Organizational Overview
## 3. Problem Statement
## 4. Proposed Solution & Innovation
## 5. Funder Value Proposition
## 6. 1-Page Proposal Skeleton (Headings + Bullet Points)
## 7. Budget Logic Overview (Structure only, no numbers)
## 8. Impact Metrics & KPIs
## 9. Risk & Mitigation
## 10. 5-Step Submission Roadmap

Do not fabricate applicant-specific facts. Use placeholders where details are missing. In the grant
strategy and roadmap, clearly distinguish potential leads from grants confirmed open and eligible.
Include source URLs from the research notes where relevant. If evidence is weak, say so explicitly.""",
    )
    logger.info("Grant workflow completed successfully.")
    return report
