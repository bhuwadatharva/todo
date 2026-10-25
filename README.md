# Python AI Engineer – Autonomous Agents (60-Minute Challenge)

> A production-grade, minimalist Autonomous Strategy Agent built with **FastAPI**, **Groq LLM (Llama 3.3 70B)**, **python-docx**, and a deterministic **Reflection & Self-Check** loop.

---

## 🎯 Challenge Objectives & Philosophy
- **Keep it simple, reliable, and interview-ready**: Zero frontend, zero database, zero heavy multi-agent frameworks (no LangGraph/CrewAI/AutoGen).
- **Decoupled 7-Stage Pipeline**:
  `Request` ➔ `Validation` ➔ `LLM Planning` ➔ `Plan Validation` ➔ `Sequential Execution` ➔ `DOCX Generation` ➔ `Self-Check / Reflection` ➔ `JSON Response`.
- **Mandatory Engineering Improvement**: Deterministic Reflection/Self-Check that verifies physical file existence, minimum byte size (> 1,000 bytes), and section completeness against the planned TODO list, executing **exactly one automated repair pass** if validation fails.
- **Handling Ambiguity & Competing Priorities**: Explicit extraction of assumptions rather than hallucinating ungrounded facts.

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    User([User / Client]) -->|POST /agent| API[FastAPI: app/main.py]
    API -->|1. Validate Request| Pydantic[Pydantic Models: app/models.py]
    Pydantic -->|2. Generate Plan| Planner[LLM Planner: app/planner.py]
    Planner -->|Groq JSON Mode| LLM[Groq: llama-3.3-70b-versatile]
    Planner -->|3. Validate Plan Structure| PlanValidator[Plan Validator]
    PlanValidator -->|4. Execute Sequential Tasks| Executor[Executor: app/executor.py]
    Executor -->|Rich Drafts & Tables| DocxGen[DOCX Builder: app/document.py]
    DocxGen -->|Write .docx to disk| OutputDir[(output/ directory)]
    DocxGen -->|5. Reflection & Self-Check| Reflection[Reflection Engine: app/reflection.py]
    Reflection -->|Passes Checks?| ResultCheck{Valid & Complete?}
    ResultCheck -->|No| Repair[Automated Repair Pass (1 Attempt)]
    Repair -->|Re-verify| OutputDir
    ResultCheck -->|Yes| Response[AgentResponse JSON + Download URL]
    Response -->|GET /download/filename| Download[Safe Download Endpoint]
```

### Architecture Highlights
1. **Decoupled Modularity**:
   - `app/main.py`: REST API routing, CORS, exception handling, and safe path traversal prevention.
   - `app/config.py`: Environment configuration via `.env`, directories, and provider status.
   - `app/models.py`: Strongly typed Pydantic schemas for requests, tasks, plans, sections, and self-checks.
   - `app/llm_client.py`: Groq API wrapper with 30s timeout, JSON mode parsing, and graceful offline fallback.
   - `app/planner.py`: Dynamic task decomposition and explicit assumption extraction.
   - `app/executor.py`: Sequential execution generating paragraphs, bullets, and tables.
   - `app/document.py`: Executive Word (`.docx`) formatting using `python-docx` (Navy & Slate theme, metadata table, assumption callouts, styled tables, header/footer).
   - `app/reflection.py`: Self-check inspector and 1-repair recovery mechanism.
   - `app/agent.py`: High-level orchestrator.

---

## 📂 Project Directory Tree

```
d:\Website\todo\
├── app/
│   ├── __init__.py
│   ├── config.py              # Environment variables, output paths, timeouts
│   ├── models.py              # Pydantic schemas (AgentRequest, Plan, TaskItem, SelfCheck)
│   ├── llm_client.py          # Groq API client with JSON mode, timeouts & fallback
│   ├── planner.py             # LLM task decomposition & plan validation
│   ├── executor.py            # Sequential task execution & content drafting
│   ├── document.py            # Word document builder (Navy/Slate design palette)
│   ├── reflection.py          # Mandatory self-check validator & single repair attempt
│   ├── agent.py               # Master agent workflow orchestrator
│   └── main.py                # FastAPI application (POST /agent, GET /download)
├── tests/
│   ├── __init__.py
│   └── test_agent.py          # Comprehensive test suite (Test Cases 1 & 2, Security, Reflection)
├── output/                    # Generated .docx documents directory
├── scripts/
│   └── generate_interview_script.py  # Script generating INTERVIEW_VIDEO_SCRIPT.docx
├── .env.example               # Environment variables template
├── .env                       # Local environment file (with GROQ_API_KEY)
├── requirements.txt           # Dependencies
├── run_tests.py               # One-click test runner with colored output
├── INTERVIEW_VIDEO_SCRIPT.docx # Formatted 8–10 minute interview video script
└── README.md                  # This documentation
```

---

## ⚙️ Quick Start (Windows PowerShell)

### 1. Prerequisites & Virtual Environment
Ensure Python 3.10+ is installed.

```powershell
# Navigate to project directory
cd d:\Website\todo

# Create virtual environment (optional but recommended)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure `.env`
Copy `.env.example` to `.env` and set your Groq API key:

```powershell
# In PowerShell:
Copy-Item .env.example .env
```

Open `.env` in your editor and set:
```ini
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
LLM_TIMEOUT_SECONDS=30
OUTPUT_DIR=output
```
*(Note: If you run tests without a Groq key, the built-in intelligent offline engine ensures 100% of the workflow executes and validates smoothly).*

### 3. Run the Automated Test Suite
```powershell
python run_tests.py
```
Or directly with pytest:
```powershell
pytest tests/test_agent.py -v
```

---

## 🚀 Running the Server & API Commands

### Start the FastAPI Dev Server
```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
Server is live at: `http://127.0.0.1:8000`
Swagger UI docs: `http://127.0.0.1:8000/docs`

---

## 🧪 Test Cases (Windows PowerShell Commands)

### Test Case 1: Standard Business Request
*Scenario: AI SaaS startup marketing plan with clear parameters.*

```powershell
$body = @{
    request = "Create a Q3 Marketing Strategy Plan for an AI SaaS startup launching an automated code review tool with a $20,000 budget and a 3-month timeline."
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8000/agent" -Method Post -ContentType "application/json" -Body $body | ConvertTo-Json -Depth 6
```

### Test Case 2: Complex Request with Missing Info & Competing Priorities
*Scenario: Impossible timeline, zero downtime, cost cuts, HIPAA & GDPR compliance without budget or compliance personnel.*

```powershell
$body = @{
    request = "Launch our enterprise AI product next week with zero downtime, cut infrastructure costs by 50% immediately, and build a complete compliance framework for HIPAA and GDPR, but we don't have a compliance officer or budget specified."
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8000/agent" -Method Post -ContentType "application/json" -Body $body | ConvertTo-Json -Depth 6
```

### Safe File Download Command
Download the generated document using the `download_url` returned in the response:

```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/download/q3_marketing_go-to-market_strategy_20261022_191504.docx" -OutFile "downloaded_plan.docx"
```

---

## 📊 Sample API Response Structure

```json
{
  "status": "success",
  "request": "Create a Q3 Marketing Strategy Plan for an AI SaaS startup launching an automated code review tool with a $20,000 budget and a 3-month timeline.",
  "document_title": "Q3 Marketing & Go-To-Market Strategy",
  "assumptions": [
    "Assumed target market focuses on developer-first software companies.",
    "Assumed $20,000 budget is strictly allocated across content, devrel, and paid search channels.",
    "Assumed core metrics for success are Qualified Signups and Customer Acquisition Cost (CAC)."
  ],
  "tasks": [
    {
      "id": 1,
      "title": "Establish Executive Scope & Core Objectives",
      "description": "Synthesize the primary objectives, constraints, and success criteria based on the request.",
      "target_section": "Executive Summary",
      "status": "completed",
      "output_summary": "Generated 2 paragraphs, 3 key points and 3 table rows."
    },
    {
      "id": 2,
      "title": "Analyze Operating Constraints & Prioritization Matrix",
      "description": "Evaluate technical feasibility, resource bottlenecks, and tradeoff resolutions.",
      "target_section": "Context & Constraints Analysis",
      "status": "completed",
      "output_summary": "Generated 2 paragraphs, 3 key points and 3 table rows."
    },
    {
      "id": 3,
      "title": "Architect Phased Execution Roadmap",
      "description": "Draft sequential milestones, deliverables, and operational ownership for each phase.",
      "target_section": "Strategic Roadmap & Execution Plan",
      "status": "completed",
      "output_summary": "Generated 2 paragraphs, 3 key points and 3 table rows."
    },
    {
      "id": 4,
      "title": "Formulate Risk Assessment & Contingency Protocols",
      "description": "Identify primary failure modes, regulatory/financial pitfalls, and mitigations.",
      "target_section": "Risk Management & Mitigations",
      "status": "completed",
      "output_summary": "Generated 2 paragraphs, 3 key points and 3 table rows."
    },
    {
      "id": 5,
      "title": "Synthesize Immediate Next Steps & Governance",
      "description": "Define key deliverables for the next 7-14 days and assign accountability.",
      "target_section": "Immediate Action Items & Governance",
      "status": "completed",
      "output_summary": "Generated 2 paragraphs, 3 key points and 3 table rows."
    }
  ],
  "document_path": "output/q3_marketing_go-to-market_strategy_20261022_191504.docx",
  "download_url": "/download/q3_marketing_go-to-market_strategy_20261022_191504.docx",
  "self_check": {
    "passed": true,
    "file_exists": true,
    "file_size_bytes": 38487,
    "sections_found": [
      "Immediate Action Items & Governance",
      "Risk Management & Mitigations",
      "Context & Constraints Analysis",
      "Executive Summary",
      "Strategic Roadmap & Execution Plan"
    ],
    "missing_sections": [],
    "repair_attempted": false,
    "details": "Verification successful: 5 sections validated (38487 bytes)."
  },
  "execution_time_seconds": 3.42,
  "llm_provider": "groq:llama-3.3-70b-versatile",
  "error": null
}
```

---

## 🔍 Key Functions Explanation

| File | Function / Class | Purpose & Engineering Decisions |
| :--- | :--- | :--- |
| `app/models.py` | `AgentRequest` | Validates prompt length (5-5000 chars) and strips whitespace using Pydantic field validators. |
| `app/llm_client.py` | `LLMClient.query_json()` | Enforces JSON output from Groq LLM with configurable timeout (30s) and fallback. |
| `app/planner.py` | `generate_plan()` | Prompts LLM to decompose goal into 4-6 sequential tasks and extract explicit assumptions. |
| `app/planner.py` | `validate_plan()` | Deterministically validates task IDs, non-empty titles, and mapped target sections. |
| `app/executor.py` | `execute_tasks()` | Iterates through planned tasks, drafting rich section content (paragraphs, bullets, tables). |
| `app/document.py` | `create_docx_report()` | Builds styled `.docx` with custom XML cell shading, metadata tables, callouts, and footers. |
| `app/reflection.py`| `perform_self_check_and_repair()` | Physical file check (> 1,000 bytes) + XML heading inspection; triggers single repair if incomplete. |
| `app/main.py` | `download_document()` | Safe file retrieval protecting against directory traversal using `os.path.basename` and path relativity. |

---

## 🛡️ Mandatory Engineering Improvement: Reflection & Self-Check Pattern

Naive LLM agents often suffer from "silent failure": the model reports success, but the resulting file is missing, empty, or truncated.

Our solution implements **deterministic physical and semantic verification**:
1. **Physical Existence**: Checks `file_path.exists()`.
2. **Non-Empty Byte Inspection**: Checks `file_size > 1000` bytes (valid `.docx` zip container).
3. **Semantic Section Completeness**: Opens the `.docx` using `python-docx`, scans all headings, and verifies every `target_section` from the planned TODO list is physically present.
4. **Single Repair Attempt**: If a section was skipped or omitted during drafting, the engine generates the missing section, recompiles the document, and runs a second verification pass. If still failing, it returns a descriptive error rather than serving broken data.

---

## ⚖️ Tradeoffs & Design Decisions (60-Minute Scope)

1. **Lightweight Python vs. Heavy Frameworks**:
   - *Decision*: Avoided LangGraph, CrewAI, and AutoGen.
   - *Rationale*: Heavy frameworks introduce hundreds of dependencies, hidden prompt engineering abstractions, and brittle debugging cycles. Pure Python + FastAPI gives 100% control, sub-second execution, and zero bloat.
2. **Synchronous Execution vs. Background Celery Queue**:
   - *Decision*: Synchronous execution with Fast Groq API.
   - *Rationale*: For a 60-minute build challenge, keeping it synchronous avoids configuring Redis, Celery, and WebSockets while still delivering responses in 3 to 5 seconds.
3. **Local Filesystem vs. Cloud Object Storage**:
   - *Decision*: Saved files to `./output` with sanitized endpoints.
   - *Rationale*: Zero cloud credentials required to run locally; easily swappable to AWS S3/GCS in production.

---

## 🎥 Interview Video Script

The root directory contains **`INTERVIEW_VIDEO_SCRIPT.docx`**, a complete 8–10 minute spoken script and live-demonstration guide designed specifically for fresher interviews:
- **Section 1**: Introduction & Personal Pitch `[0:00 - 1:15]`
- **Section 2**: Architecture & Pipeline Walkthrough `[1:15 - 3:00]`
- **Section 3**: Live Demo Walkthrough (Both Test Cases) `[3:00 - 5:30]`
- **Section 4**: Deep-Dive on Reflection & Self-Check Pattern `[5:30 - 7:00]`
- **Section 5**: Error Handling, Security & Traversal Prevention `[7:00 - 8:30]`
- **Section 6**: Engineering Tradeoffs in 60 Minutes `[8:30 - 9:30]`
- **Section 7**: Conclusion & Q&A Readiness `[9:30 - 10:00]`

All areas requiring candidate personalization are highlighted with `[PERSONALIZE: ...]`.
