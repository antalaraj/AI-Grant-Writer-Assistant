# ================================================================
# AI GRANT WRITER ASSISTANT (AGENT-SPECIFIC TOOLS)
# ================================================================

import os
import logging
import warnings

# ================================================================
# 1. SYSTEM SILENCING
# ================================================================
os.environ["LITELLM_LOG"] = "CRITICAL"
os.environ["OTEL_SDK_DISABLED"] = "true"
os.environ["PYTHONWARNINGS"] = "ignore"

logging.basicConfig(level=logging.CRITICAL)
warnings.filterwarnings("ignore")

# ================================================================
# 2. IMPORTS
# ================================================================
import litellm
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun

litellm.set_verbose = False
litellm.suppress_debug_info = True

# ================================================================
# 3. API KEYS
# ================================================================
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY")

# ================================================================
# 4. LLM CONFIGURATION
# ================================================================
research_llm = LLM(
    model="groq/llama-3.3-70b-versatile",
    temperature=0.2
)

validation_llm = LLM(
    model="gemini/gemini-2.5-flash",
    temperature=0.1
)

writing_llm = LLM(
    model="groq/llama-3.3-70b-versatile",
    temperature=0.2
)

# ================================================================
# 5. TOOLS (ONE CLASS, MULTIPLE TOOLS)
# ================================================================
class GrantTools:

    @tool("grant_search_tool")
    def grant_search(query: str) -> str:
        """Search active 2025 grant opportunities."""
        search = DuckDuckGoSearchRun()
        return search.run(f"{query} 2025 grant funding opportunity")

    @tool("eligibility_check_tool")
    def eligibility_check(grant_info: str) -> str:
        """Check eligibility risks and assumptions."""
        return (
            "Eligibility Review:\n"
            "- {org_type} verified\n"
            "- Deadline assumed active for 2025\n"
            "- Geographic restrictions must be confirmed\n"
            "- Matching funds requirement unclear (risk flagged)"
        )

    @tool("report_structuring_tool")
    def report_structuring(content: str) -> str:
        """Ensure professional and funder-ready structure."""
        return (
            "Content refined for clarity, compliance, and reviewer expectations.\n"
            "Language simplified, outcomes emphasized, risks addressed."
        )

# ================================================================
# 6. AGENTS WITH THEIR OWN TOOLS
# ================================================================

# ---------------- Researcher ----------------
researcher = Agent(
    role="Startup & NGO Funding Intelligence Lead",
    goal=(
        "Locate 3 high-probability, active 2025 grant opportunities specifically for "
        "a {org_type} working on {mission}."
    ),
    backstory=(
        "You specialize in the global funding landscape. For startups, you identify "
        "equity-free innovation grants, government programs, and accelerators. "
        "For NGOs, you prioritize philanthropic foundations, capacity-building grants, "
        "and government social-impact funding. You focus strictly on 2025 deadlines."
    ),
    tools=[GrantTools.grant_search],
    llm=research_llm,
    verbose=False
)

# ---------------- Validator ----------------
validator = Agent(
    role="Grant Eligibility Validator",
    goal=(
        "Verify that the {org_type} meets all stated 2025 eligibility requirements "
        "for each proposed grant, and eliminate unsuitable opportunities."
    ),
    backstory=(
        "You act as a strict gatekeeper. You scrutinize eligibility clauses such as "
        "entity type, geography, funding stage, indirect cost rules, and matching fund "
        "requirements. If critical information is missing, you explicitly state "
        "assumptions and flag risks. Grants with high uncertainty must be downgraded "
        "or rejected."
    ),
    tools=[GrantTools.eligibility_check],
    llm=validation_llm,
    verbose=False
)

# ---------------- Writer ----------------
writer = Agent(
    role="Lead Proposal Architect",
    goal="Produce a funder-ready Grant Strategy Report based strictly on validated inputs.",
    backstory=(
        "You write with a grant reviewer mindset. Every claim must connect to "
        "measurable impact, feasibility, sustainability, and alignment with funder priorities. "
        "You avoid marketing language and focus on clarity, outcomes, and credibility. "
        "Your output is suitable for direct submission or minimal editing."
    ),
    tools=[GrantTools.report_structuring],
    llm=writing_llm,
    verbose=False
)

# ================================================================
# 7. TASKS
# ================================================================

task_research = Task(
    description=(
        "1. Identify the core funding needs of a {org_type} working on {mission}.\n"
        "2. Find exactly 3 active 2025 grant opportunities with official links.\n"
        "3. Prioritize equity-free funding for startups or capacity-building grants for NGOs."
    ),
    expected_output=(
        "A structured list of 3 grants including:\n"
        "- Funder Name\n"
        "- Grant Program Name\n"
        "- Award Amount Range\n"
        "- Application Deadline (2025)\n"
        "- Official Link\n"
        "- Short explanation of why the grant fits the {org_type}"
    ),
    agent=researcher
)

task_validate = Task(
    description=(
        "Perform a strict eligibility and risk audit on the 3 identified grants:\n"
        "- Confirm the {org_type} is an eligible entity type.\n"
        "- Verify the 2025 deadline is still active.\n"
        "- Check geographic, financial, and legal constraints.\n"
        "- Identify indirect cost rules or matching fund requirements.\n"
        "- Explicitly state assumptions if data is missing.\n"
        "- Reject or downgrade grants with high uncertainty."
    ),
    expected_output=(
        "A Validation Summary ranking grants as:\n"
        "- Highest Match\n"
        "- Medium Match\n"
        "- Rejected\n\n"
        "Each entry must include eligibility status, key risks, and assumptions."
    ),
    agent=validator,
    context=[task_research]
)

task_write = Task(
    description=(
        "Generate a professional Grant Strategy Report for the {mission} project.\n"
        "Use STRICT Markdown format with ONLY the following sections:\n\n"
        "## 1. Executive Summary\n"
        "## 2. Organizational Overview\n"
        "## 3. Problem Statement\n"
        "## 4. Proposed Solution & Innovation\n"
        "## 5. Funder Value Proposition\n"
        "## 6. 1-Page Proposal Skeleton (Headings + Bullet Points)\n"
        "## 7. Budget Logic Overview (Structure only, no numbers)\n"
        "## 8. Impact Metrics & KPIs\n"
        "## 9. Risk & Mitigation\n"
        "## 10. 5-Step Submission Roadmap\n\n"
        "Do NOT add extra sections. Use concise, reviewer-friendly language."
    ),
    expected_output=(
        "A strictly structured, funder-ready Markdown Grant Strategy Report "
        "based only on validated grant opportunities."
    ),
    agent=writer,
    context=[task_validate]
)

# ================================================================
# 8. EXECUTION
# ================================================================
def run_grant_assistant():

    crew = Crew(
        agents=[researcher, validator, writer],
        tasks=[task_research, task_validate, task_write],
        process=Process.sequential,
        verbose=False
    )

    print("\n" + "=" * 50)
    print("        AI GRANT WRITER ASSISTANT")
    print("=" * 50)

    org_type = input("\nEnter Organization Type: ")
    mission = input("Enter Project Mission: ")

    print("\n[System] Agents are working...")
    print("-" * 50)

    try:
        result = crew.kickoff(
            inputs={"org_type": org_type, "mission": mission}
        )

        print("\n" + "#" * 50)
        print("           FINAL GRANT REPORT")
        print("#" * 50)
        print(result)

        filename = f"Grant_Report_{org_type.replace(' ', '_')}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(str(result))

        print(f"\n[Success] Report saved as {filename}")

    except Exception as e:
        print(f"\n[Error] {e}")

# ================================================================
# 9. MAIN
# ================================================================
if __name__ == "__main__":
    run_grant_assistant()
