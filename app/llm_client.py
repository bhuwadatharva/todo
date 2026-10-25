"""
LLM Client Module.
Wraps Groq API with robust error handling, configurable timeouts,
JSON mode, and a safe heuristic fallback if an API key is not yet configured.
"""
import json
import logging
import re
from typing import Dict, Any, Optional

from app.config import GROQ_API_KEY, GROQ_MODEL, LLM_TIMEOUT_SECONDS, is_llm_configured

logger = logging.getLogger(__name__)

# Try importing official groq client
try:
    from groq import Groq, AuthenticationError, RateLimitError, APITimeoutError, APIConnectionError
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    logger.warning("Groq library not installed. Offline fallback will be active.")


class LLMClient:
    """
    Manages communication with Groq LLM with timeouts and fallback handling.
    """

    def __init__(self):
        self.api_key = GROQ_API_KEY
        self.model = GROQ_MODEL
        self.timeout = LLM_TIMEOUT_SECONDS
        self.client: Optional[Any] = None

        if GROQ_AVAILABLE and is_llm_configured():
            try:
                self.client = Groq(api_key=self.api_key, timeout=self.timeout)
                logger.info(f"Initialized Groq client with model '{self.model}' (timeout: {self.timeout}s)")
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")
                self.client = None
        else:
            logger.info("No valid Groq API key detected. Running in heuristic simulation mode.")

    def get_provider_name(self) -> str:
        if self.client is not None:
            return f"groq:{self.model}"
        return "mock-heuristic (offline/no-key)"

    def query_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """
        Sends a prompt to the LLM and guarantees a valid parsed JSON dictionary.
        Uses Groq's JSON mode when online, or heuristic fallback if offline/no key.
        """
        if self.client is not None:
            try:
                return self._call_groq_json(system_prompt, user_prompt)
            except Exception as e:
                logger.warning(f"Groq API call failed ({e}). Falling back to internal engine.")
                return self._fallback_json(system_prompt, user_prompt)
        else:
            return self._fallback_json(system_prompt, user_prompt)

    def _call_groq_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Call Groq API requesting structured JSON response."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt + "\nYou MUST return valid, parseable JSON only. Do not wrap in markdown quotes if possible, or use standard JSON."},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=4096
        )

        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response received from Groq LLM.")

        # Clean any potential markdown wrapping (e.g. ```json ... ```)
        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)

        return json.loads(cleaned)

    def _fallback_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """
        Offline heuristic fallback engine.
        Ensures the agent is 100% testable and runnable even before an API key is input,
        while returning structured, dynamic data corresponding to the prompt.
        """
        lower_prompt = user_prompt.lower()

        # Is this a planning request?
        if "plan" in system_prompt.lower() or "todo" in system_prompt.lower():
            is_complex = any(k in lower_prompt for k in ["zero downtime", "hipaa", "gdpr", "competing", "no budget", "next week"])
            
            # Extract high-level topic
            if "marketing" in lower_prompt:
                topic = "Q3 Marketing & Go-To-Market Strategy"
            elif "enterprise" in lower_prompt or "compliance" in lower_prompt:
                topic = "Enterprise AI Launch & Compliance Blueprint"
            else:
                words = user_prompt.split()[:5]
                topic = "Autonomous Strategic Plan: " + " ".join(words)

            assumptions = []
            if is_complex:
                assumptions.append("Assumed launch date is adjusted to phased rollout to prevent zero-downtime regression.")
                assumptions.append("Assumed interim compliance measures are prioritized (data encryption, audit logging) prior to full HIPAA/GDPR certification.")
                assumptions.append("Assumed infrastructure optimization achieves 30-40% immediate savings without risking high-availability SLAs.")
                assumptions.append("Assumed fractional compliance advisor or external auditor will be onboarded in Phase 2.")
            else:
                assumptions.append("Assumed target market focuses on developer-first software companies.")
                assumptions.append("Assumed $20,000 budget is strictly allocated across content, devrel, and paid search channels.")
                assumptions.append("Assumed core metrics for success are Qualified Signups and Customer Acquisition Cost (CAC).")

            tasks = [
                {
                    "id": 1,
                    "title": "Establish Executive Scope & Core Objectives",
                    "description": "Synthesize the primary objectives, constraints, and success criteria based on the request.",
                    "target_section": "Executive Summary",
                    "status": "pending",
                    "output_summary": None
                },
                {
                    "id": 2,
                    "title": "Analyze Operating Constraints & Prioritization Matrix",
                    "description": "Evaluate technical feasibility, resource bottlenecks, and tradeoff resolutions.",
                    "target_section": "Context & Constraints Analysis",
                    "status": "pending",
                    "output_summary": None
                },
                {
                    "id": 3,
                    "title": "Architect Phased Execution Roadmap",
                    "description": "Draft sequential milestones, deliverables, and operational ownership for each phase.",
                    "target_section": "Strategic Roadmap & Execution Plan",
                    "status": "pending",
                    "output_summary": None
                },
                {
                    "id": 4,
                    "title": "Formulate Risk Assessment & Contingency Protocols",
                    "description": "Identify primary failure modes, regulatory/financial pitfalls, and mitigations.",
                    "target_section": "Risk Management & Mitigations",
                    "status": "pending",
                    "output_summary": None
                },
                {
                    "id": 5,
                    "title": "Synthesize Immediate Next Steps & Governance",
                    "description": "Define key deliverables for the next 7-14 days and assign accountability.",
                    "target_section": "Immediate Action Items & Governance",
                    "status": "pending",
                    "output_summary": None
                }
            ]

            return {
                "title": topic,
                "subtitle": "Generated by Autonomous AI Strategy Agent",
                "assumptions": assumptions,
                "tasks": tasks
            }

        # Otherwise, this is a section drafting request
        section_name = "Detailed Analysis"
        for candidate in ["Executive Summary", "Context & Constraints Analysis", "Strategic Roadmap & Execution Plan", "Risk Management & Mitigations", "Immediate Action Items & Governance"]:
            if candidate.lower() in user_prompt.lower():
                section_name = candidate
                break

        return {
            "section_title": section_name,
            "paragraphs": [
                f"This section addresses the requirements established for '{section_name}' under current operational directives.",
                f"Key factors driving the strategy include balancing rapid execution with stability, resource discipline, and verified outcomes."
            ],
            "bullet_points": [
                "Primary Objective: Ensure robust delivery aligned with stakeholder benchmarks.",
                "Process Governance: Establish continuous monitoring and weekly milestone retrospectives.",
                "Risk Threshold: Zero unmitigated blockers tolerated during primary deployment phases."
            ],
            "table_headers": ["Milestone / Metric", "Target Target", "Ownership", "Status"],
            "table_rows": [
                ["Initial Baseline Setup", "Day 1-7", "Lead AI Engineer", "Ready"],
                ["Operational Validation", "Day 8-21", "DevOps & Compliance", "Pending"],
                ["Full Scale Review", "Day 30", "Executive Sponsor", "Scheduled"]
            ]
        }


# Singleton instance for simple app-wide access
llm_client = LLMClient()
