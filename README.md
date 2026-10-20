# AI Grant Writer Assistant 🤖📄

An AI-powered Flask web application that researches potential grant opportunities and generates a structured grant proposal draft for an organization based on its type and mission.

**🌐 Live Demo:** [grant-writer-assistant.vercel.app](https://grant-writer-assistant.vercel.app/)

**Repository:** [antalaraj/AI-Grant-Writer-Assistant](https://github.com/antalaraj/AI-Grant-Writer-Assistant)

---

## ✨ Features

- **Grant research:** Searches the web for potential funding opportunities using DuckDuckGo Search (`ddgs`).
- **Structured proposal generation:** Uses Groq to draft a report tailored to the organization type and mission.
- **Optional second-provider validation:** Gemini is configured as an optional model integration; the core draft generation requires Groq.
- **Evidence-first reporting:** Includes source links and labels search results as unverified leads unless independently verified.
- **Deterministic report structure:** Ensures the report contains the required proposal sections and builds the opportunity evidence table from collected search records.
- **Verification checklist:** Lists key items to confirm before applying, including call status, eligibility, deadlines, funding limits, and required documents.
- **Automated quality audit:** Attempts an internal checklist review and may make one revision pass when the audit succeeds. The audit is optional; rate limits or provider errors can leave the report without a score.
- **Browser-based PDF export:** The result page provides **Download / Save as PDF**, implemented through the browser print dialog. It is not a server-side PDF-generation service.

> **Important:** A search result or official portal is not proof that a grant call is currently open or that an applicant is eligible. Verify the official call documents and applicant details before submitting a proposal. The automated quality score, when available, is an internal checklist estimate—not a prediction of funding success.

---

## 🧰 Tech Stack

- **Language:** Python
- **Web framework:** Flask
- **Draft generation:** Groq API — `openai/gpt-oss-120b`
- **Optional model integration:** Google Gemini API — `gemini-3.8-flash`
- **Grant search:** DuckDuckGo Search via `ddgs`
- **Frontend:** HTML, CSS, JavaScript
- **Markdown rendering:** Marked.js and DOMPurify
- **Deployment:** Vercel

The current implementation calls the provider APIs directly from `grant_workflow.py`; the dependencies do not include CrewAI or LangChain.

---

## 🔄 How It Works

1. Enter the **organization type** and **project mission** in the web form.
2. The backend searches for potential grant sources and funding leads.
3. Groq generates the structured grant strategy/proposal draft.
4. The application normalizes the required sections and builds the source evidence table and verification checklist.
5. An optional quality-audit pass reviews the report. If the audit succeeds and the score is below the configured threshold, one revision attempt may be made.
6. The report is rendered in the browser, where you can print or save it as a PDF.

### Report sections

The workflow aims to provide these 12 core sections:

1. Executive Summary
2. Organizational Overview
3. Problem Statement
4. Proposed Solution & Innovation
5. Funder Value Proposition
6. 1-Page Proposal Skeleton
7. Budget Logic Overview
8. Impact Metrics & KPIs
9. Risk & Mitigation
10. 5-Step Submission Roadmap
11. Grant Opportunity Evidence Table
12. Sources and Verification Checklist

A 13th section, **Automated Quality Audit**, is appended to explain the internal checklist result or state that the audit could not be completed.

---

## 🖥️ Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/antalaraj/AI-Grant-Writer-Assistant.git
cd AI-Grant-Writer-Assistant
```

### 2. Create and activate a virtual environment (recommended)

**Windows PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS/Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure environment variables

Set `GROQ_API_KEY` for report drafting. `GEMINI_API_KEY` enables the optional Gemini integration.

**Windows PowerShell:**

```powershell
$env:GROQ_API_KEY = "your_groq_api_key"
$env:GEMINI_API_KEY = "your_gemini_api_key"
```

**macOS/Linux:**

```bash
export GROQ_API_KEY="your_groq_api_key"
export GEMINI_API_KEY="your_gemini_api_key"
```

Optionally set `FLASK_SECRET_KEY` to a long random secret. Never commit API keys to the repository or expose them in frontend JavaScript.

### 5. Start the app

```bash
python web.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000).

---

## ☁️ Vercel Deployment

The repository includes `app.py` as the Vercel entry point and `vercel.json` to configure a maximum function duration of 300 seconds.

1. Import [the GitHub repository](https://github.com/antalaraj/AI-Grant-Writer-Assistant) into Vercel.
2. Set the project root to the repository root.
3. Configure `GROQ_API_KEY` in the Vercel project's environment variables. Add `GEMINI_API_KEY` if you want the optional Gemini integration.
4. Deploy the project.

**Live application:** [https://grant-writer-assistant.vercel.app/](https://grant-writer-assistant.vercel.app/)

The maximum duration configured in `vercel.json` is subject to the limits of the Vercel plan and runtime. Provider availability, search-service behavior, and API rate limits can affect report generation. Check the Vercel function logs if a request fails.

---

## 🧪 Tests

The repository includes regression tests for report structure and evidence-table behavior, plus CI checks for Python compilation, required deployment files, and Flask routes.

Run the report-structure tests locally:

```bash
python -m unittest discover -s tests -v
```

---

## 📁 Project Structure

```text
AI-Grant-Writer-Assistant/
├── app.py                       # Vercel Flask entry point
├── web.py                       # Flask routes and local server
├── grant_workflow.py             # Search, drafting, report normalization, audit
├── requirements.txt              # Flask and ddgs dependencies
├── vercel.json                   # Vercel function configuration
├── .python-version
├── public/
│   ├── style.css                 # Frontend styling and print styles
│   └── main.js                   # Form submission and report rendering
├── templates/
│   ├── index.html                # Input form
│   ├── loading.html              # Loading state
│   └── result.html               # Report result and print/PDF action
├── tests/
│   └── test_report_structure.py  # Report normalization regression tests
└── .github/
    └── workflows/
        └── ci.yml                # Python CI and Flask smoke tests
```

---

## 👨‍💻 Author

**Raj Antala**  
PGDM Student in AI and Data Science  
Adani Institute of Digital Technology Management (AIDTM)  
Gandhinagar, India  
Email: antalaraj214@gmail.com  
LinkedIn: [linkedin.com/in/antalaraj](https://www.linkedin.com/in/antalaraj)

---

## 📌 Disclaimer

This project is intended for educational and demonstration purposes. It generates proposal drafts and research leads, not guaranteed funding outcomes. Users are responsible for checking official grant documents, confirming eligibility and deadlines, validating all applicant information and budget figures, and reviewing the final proposal before submission.
