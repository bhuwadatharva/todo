"""
Test suite covering:
1. Health endpoint
2. Test Case 1: Standard business request
3. Test Case 2: Complex request with missing information & competing priorities
4. Request validation (too short / empty)
5. Security: Safe download path traversal prevention
6. Reflection: Self-check validation and repair capability
"""
import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.config import OUTPUT_DIR
from app.models import Plan, TaskItem, SectionContent
from app.reflection import perform_self_check_and_repair, validate_document

client = TestClient(app)


def test_health_endpoint():
    """Verify health and provider status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "llm_provider" in data


def test_standard_business_request():
    """
    Test Case 1: Standard business request.
    AI SaaS code review marketing plan with $20,000 budget and 3-month timeline.
    """
    payload = {
        "request": "Create a Q3 Marketing Strategy Plan for an AI SaaS startup launching an automated code review tool with a $20,000 budget and a 3-month timeline."
    }
    response = client.post("/agent", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "success"
    assert len(data["tasks"]) >= 2
    assert all(task["status"] == "completed" for task in data["tasks"])
    assert data["document_title"] != ""
    assert data["document_path"] != ""
    assert data["download_url"].startswith("/download/")
    assert data["self_check"]["passed"] is True
    assert data["self_check"]["file_exists"] is True
    assert data["self_check"]["file_size_bytes"] > 1000

    # Verify physical file existence on disk
    file_path = OUTPUT_DIR / os.path.basename(data["document_path"])
    assert file_path.exists()
    assert os.path.getsize(str(file_path)) > 1000

    # Verify download endpoint
    dl_response = client.get(data["download_url"])
    assert dl_response.status_code == 200
    assert len(dl_response.content) == data["self_check"]["file_size_bytes"]


def test_complex_request_with_missing_info_and_competing_priorities():
    """
    Test Case 2: Complex request with missing information & competing priorities.
    Zero downtime vs 1-week launch; 50% cost cut; HIPAA & GDPR without compliance officer or budget.
    """
    payload = {
        "request": "Launch our enterprise AI product next week with zero downtime, cut infrastructure costs by 50% immediately, and build a complete compliance framework for HIPAA and GDPR, but we don't have a compliance officer or budget specified."
    }
    response = client.post("/agent", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "success"
    assert len(data["tasks"]) >= 2

    # Verify that assumptions were extracted to handle ambiguities
    assert len(data["assumptions"]) > 0
    # Must explicitly state assumptions regarding missing compliance officer or budget or timeline
    assumptions_text = " ".join(data["assumptions"]).lower()
    assert any(k in assumptions_text for k in ["compliance", "budget", "cost", "phase", "rollout", "downtime", "interim"])

    # Verify generated document
    assert data["self_check"]["passed"] is True
    file_path = OUTPUT_DIR / os.path.basename(data["document_path"])
    assert file_path.exists()
    assert os.path.getsize(str(file_path)) > 1000


def test_request_validation_too_short():
    """Verify that requests shorter than 5 characters are rejected."""
    payload = {"request": "Hi"}
    response = client.post("/agent", json=payload)
    assert response.status_code == 422  # Unprocessable Entity from Pydantic


def test_safe_download_path_traversal():
    """Verify security prevention against path traversal attacks."""
    response = client.get("/download/../../etc/passwd")
    assert response.status_code in (400, 404)

    response2 = client.get("/download/..\\..\\windows\\system32")
    assert response2.status_code in (400, 404)


def test_reflection_repair_mechanism():
    """
    Directly tests the self-check reflection and automated single repair attempt.
    Simulates a situation where an expected section was missing from the initial file.
    """
    from app.document import create_docx_report

    plan = Plan(
        title="Repair Mechanism Test",
        subtitle="Verifying 1-repair attempt capability",
        assumptions=["Testing assumption"],
        tasks=[
            TaskItem(id=1, title="Draft Section One", description="desc", target_section="Section One"),
            TaskItem(id=2, title="Draft Section Two", description="desc", target_section="Section Two"),
            TaskItem(id=3, title="Draft Missing Section Three", description="desc", target_section="Section Three")
        ]
    )

    # Intentionally only provide content for Section One and Two (Section Three missing!)
    incomplete_sections = [
        SectionContent(section_title="Section One", paragraphs=["Content 1"]),
        SectionContent(section_title="Section Two", paragraphs=["Content 2"])
    ]

    # Generate initial incomplete file
    initial_file = create_docx_report(plan, incomplete_sections, "Test repair request")
    
    # Run self check and repair
    result = perform_self_check_and_repair(
        file_path=initial_file,
        plan=plan,
        sections=incomplete_sections,
        request_text="Test repair request"
    )

    # The reflection engine should have flagged Section Three missing, triggered repair, and succeeded!
    assert result.repair_attempted is True
    assert result.passed is True
    assert "Section Three" in [s for s in result.sections_found if "Three" in s or "Section Three" in s]
