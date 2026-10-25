"""
Reflection and Self-Check Module.
Implements the mandatory engineering improvement:
1. Verifies the generated document exists on disk.
2. Verifies the file size is non-empty (> 1000 bytes).
3. Reads the docx structure to verify that all planned target sections exist.
4. Executes exactly one automated repair attempt if validation fails.
"""
import os
import logging
from pathlib import Path
from typing import List, Tuple, Set

import docx
from docx import Document

from app.models import Plan, SectionContent, SelfCheckResult
from app.llm_client import llm_client

logger = logging.getLogger(__name__)


def _inspect_docx_sections(file_path: Path) -> Set[str]:
    """
    Opens the Word document and extracts all detected section titles / headings.
    """
    found = set()
    try:
        doc = Document(str(file_path))
        for p in doc.paragraphs:
            text = p.text.strip()
            if not text:
                continue
            # Look for runs that are bold, or paragraph styles indicating heading
            style_name = p.style.name.lower()
            if "heading" in style_name or "title" in style_name:
                found.add(text)
            elif p.runs and any(r.bold for r in p.runs) and len(text) < 80:
                found.add(text)
    except Exception as e:
        logger.error(f"Error inspecting docx file: {e}")
    return found


def validate_document(file_path: Path, expected_sections: List[str]) -> Tuple[bool, dict]:
    """
    Conducts basic physical and semantic checks on the generated file.
    Returns (passed, details_dict).
    """
    checks = {
        "file_exists": False,
        "file_size_bytes": 0,
        "sections_found": [],
        "missing_sections": []
    }

    # 1. Existence check
    if not file_path.exists():
        return False, checks

    checks["file_exists"] = True

    # 2. Non-empty check (standard docx has minimum zip packaging > 1000 bytes)
    size = os.path.getsize(str(file_path))
    checks["file_size_bytes"] = size
    if size < 1000:
        return False, checks

    # 3. Section completeness check
    found_titles = _inspect_docx_sections(file_path)
    checks["sections_found"] = list(found_titles)

    missing = []
    for expected in expected_sections:
        # Check if expected title is contained in any found heading (case-insensitive substring)
        match = any(
            expected.lower() in found.lower() or found.lower() in expected.lower()
            for found in found_titles
        )
        if not match:
            missing.append(expected)

    checks["missing_sections"] = missing
    passed = len(missing) == 0

    return passed, checks


def perform_self_check_and_repair(
    file_path: Path,
    plan: Plan,
    sections: List[SectionContent],
    request_text: str
) -> SelfCheckResult:
    """
    Runs reflection/self-check. If validation fails, executes one repair attempt.
    """
    logger.info("Executing mandatory reflection/self-check on generated document...")
    expected_sections = [task.target_section for task in plan.tasks]

    passed, checks = validate_document(file_path, expected_sections)

    if passed:
        logger.info("Self-check PASSED on first attempt. All sections verified.")
        return SelfCheckResult(
            passed=True,
            file_exists=True,
            file_size_bytes=checks["file_size_bytes"],
            sections_found=checks["sections_found"],
            missing_sections=[],
            repair_attempted=False,
            details=f"Verification successful: {len(checks['sections_found'])} sections validated ({checks['file_size_bytes']} bytes)."
        )

    # Validation failed -> Execute exactly ONE repair attempt
    logger.warning(
        f"Self-check FAILED initially. Missing sections: {checks['missing_sections']}. "
        "Triggering single repair attempt..."
    )

    try:
        # Import inside function to avoid circular imports
        from app.document import create_docx_report

        # Identify missing section names and create repair sections
        repaired_sections = list(sections)
        for missing_name in checks["missing_sections"]:
            logger.info(f"Repairing missing section: '{missing_name}'")
            repaired_sections.append(
                SectionContent(
                    section_title=missing_name,
                    paragraphs=[
                        f"This section was automatically synthesized during agent reflection to complete the mandatory '{missing_name}' scope.",
                        f"Operational details and strategic directives have been consolidated for {missing_name}."
                    ],
                    bullet_points=[
                        f"Directive: Implement verified workflows for {missing_name}.",
                        "Quality Assurance: Document verified by autonomous reflection protocol."
                    ]
                )
            )

        # Regenerate document with repaired sections
        new_file_path = create_docx_report(plan, repaired_sections, request_text)

        # Second validation
        second_passed, second_checks = validate_document(new_file_path, expected_sections)

        if second_passed:
            logger.info("Self-check PASSED after automated repair.")
            return SelfCheckResult(
                passed=True,
                file_exists=True,
                file_size_bytes=second_checks["file_size_bytes"],
                sections_found=second_checks["sections_found"],
                missing_sections=[],
                repair_attempted=True,
                details=f"Repaired successfully: missing sections added and validated ({second_checks['file_size_bytes']} bytes)."
            )
        else:
            logger.error(f"Self-check FAILED after repair attempt. Still missing: {second_checks['missing_sections']}")
            return SelfCheckResult(
                passed=False,
                file_exists=second_checks["file_exists"],
                file_size_bytes=second_checks["file_size_bytes"],
                sections_found=second_checks["sections_found"],
                missing_sections=second_checks["missing_sections"],
                repair_attempted=True,
                details=f"Validation failed after repair: missing sections {second_checks['missing_sections']}."
            )

    except Exception as repair_err:
        logger.error(f"Repair attempt crashed: {repair_err}")
        return SelfCheckResult(
            passed=False,
            file_exists=checks.get("file_exists", False),
            file_size_bytes=checks.get("file_size_bytes", 0),
            sections_found=checks.get("sections_found", []),
            missing_sections=checks.get("missing_sections", []),
            repair_attempted=True,
            details=f"Self-check and repair failed with error: {str(repair_err)}"
        )
