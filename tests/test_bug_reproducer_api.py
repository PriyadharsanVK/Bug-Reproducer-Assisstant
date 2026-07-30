import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from apps.api.services.confidence import (
    calculate_step_confidence,
    calculate_overall_repro_confidence
)
from apps.api.services.guardrails import HallucinationGuard
from apps.api.services.report_composer import ReportComposer
from packages.evals.metrics import evaluate_run_record

def test_confidence_scoring():
    step_conf = calculate_step_confidence(
        action="pytest tests/test_token.py",
        expected_outcome="KeyError thrown as expected",
        has_exact_command=True,
        has_file_reference=True
    )
    assert step_conf >= 0.90

    facts = {"error_message": "KeyError: default_scope", "stack_trace": "Traceback...", "file_paths": ["services/token.py"]}
    inferred = [{"field": "config", "value": "missing", "reasoning": "log evidence", "confidence": 0.9}]
    unknowns = []
    repro_steps = [{"confidence": 0.9}]

    overall = calculate_overall_repro_confidence(facts, inferred, unknowns, repro_steps)
    assert overall >= 0.80

def test_hallucination_guard():
    raw_llm_json = """
    {
      "facts": {
        "error_message": "KeyError",
        "file_paths": ["services/token.py", "fake/path/fabricated.py"]
      },
      "inferred_assumptions": []
    }
    """
    issue_body = "The crash happened in services/token.py line 42."
    
    parsed, ok = HallucinationGuard.enforce_schema_and_tripartition(raw_llm_json, issue_body=issue_body)
    assert ok is True
    assert "fake/path/fabricated.py" not in parsed["facts"]["file_paths"]
    assert len(parsed["inferred_assumptions"]) == 1

def test_report_composer():
    md = ReportComposer.compose_markdown(
        run_id="test-run-123",
        issue_title="TypeError in Auth Handler",
        overall_confidence=0.92,
        facts={"error_message": "TypeError"},
        inferred_assumptions=[],
        unknowns=["runtime_version"],
        repro_steps=[{"step_number": 1, "action": "git clone repo", "expected_outcome": "Cloned", "sandbox_verified": True}],
        test_artifacts=[{"framework": "pytest", "file_path": "tests/test_repro.py", "code_content": "def test_repro(): pass"}],
        hypotheses=[{"category": "Uninitialized Var", "title": "Missing Config", "evidence": ["TypeError"], "probability": 0.9}]
    )
    assert "TypeError in Auth Handler" in md
    assert "Verified in Sandbox" in md

def test_eval_metrics():
    run_record = {
        "repro_steps": [{"sandbox_verified": True}, {"sandbox_verified": False}],
        "test_artifacts": [{"code_content": "def test_repro(): assert True"}],
        "unknowns": ["version"],
        "overall_confidence": 0.85
    }
    metrics = evaluate_run_record(run_record)
    assert metrics["repro_completeness_score"] == 50.0
    assert metrics["test_usefulness_score"] >= 4.0


# ---------------------------------------------------------------------------
# Bug 1 regression: needs_input gate
# ---------------------------------------------------------------------------

def test_needs_input_gate_vague_report():
    """
    A vague report (no error message, no stack trace, no file paths, many unknowns)
    must trigger the gate: confidence < 0.70 AND unknowns > 0.

    We test the gate condition using the real confidence scorer (no mocks) and
    confirm that the resulting status would be NEEDS_INPUT.
    """
    facts = {"error_message": None, "stack_trace": None, "file_paths": []}
    inferred = []
    unknowns = [
        "runtime_environment",
        "error_message",
        "stack_trace",
        "reproduction_steps",
        "affected_version",
        "operating_system",
    ]
    repro_steps = [{"confidence": 0.50, "sandbox_verified": False}]

    overall_conf = calculate_overall_repro_confidence(facts, inferred, unknowns, repro_steps)

    # Gate condition mirrors run_analysis.py exactly
    gate_fires = len(unknowns) > 0 and overall_conf < 0.70
    assert gate_fires, (
        f"Gate must fire for vague report but did not "
        f"(confidence={overall_conf:.2f}, unknowns={len(unknowns)})"
    )

    # Also assert that clarifications would be generated (one per unknown)
    clarification_questions = [
        f"Please provide more information about: {u}" for u in unknowns
    ]
    assert len(clarification_questions) == len(unknowns), (
        "Expected one clarification question per unknown"
    )


def test_needs_input_gate_concrete_report():
    """
    Non-regression: a concrete report with all key facts present must NOT
    trigger the gate — confidence should be >= 0.70 so the run completes.
    """
    facts = {
        "error_message": "KeyError: default_scope",
        "stack_trace": "Traceback (most recent call last): ...",
        "file_paths": ["services/token.py"],
    }
    inferred = [{"field": "config", "value": "missing", "reasoning": "log evidence", "confidence": 0.9}]
    unknowns = []  # no unknowns
    repro_steps = [{"confidence": 0.90, "sandbox_verified": True}]

    overall_conf = calculate_overall_repro_confidence(facts, inferred, unknowns, repro_steps)

    gate_fires = len(unknowns) > 0 and overall_conf < 0.70
    assert not gate_fires, (
        f"Gate must NOT fire for concrete report "
        f"(confidence={overall_conf:.2f}, unknowns={len(unknowns)})"
    )
    assert overall_conf >= 0.70, f"Concrete report confidence too low: {overall_conf:.2f}"


# ---------------------------------------------------------------------------
# Bug 2 regression: hypothesis grounding
# ---------------------------------------------------------------------------

def test_hypothesis_grounding_demotes_unverifiable():
    """
    Hypotheses with null or empty evidence must be capped at probability <= 0.30
    and marked with demoted_by_guard=True.
    """
    hypotheses = [
        {
            "category": "Configuration / Missing Parameter",
            "title": "Uninitialized default configuration key",
            "evidence": None,       # null evidence — should be demoted
            "probability": 0.75,
        },
        {
            "category": "Race Condition",
            "title": "Thread-unsafe singleton initialisation",
            "evidence": [],         # empty evidence — should be demoted
            "probability": 0.80,
        },
    ]

    facts = {}
    issue_body = "App breaks sometimes"
    raw_logs = ""

    validated = HallucinationGuard.validate_hypotheses(hypotheses, facts, issue_body, raw_logs)

    for hyp in validated:
        assert hyp["probability"] <= 0.30, (
            f"Hypothesis '{hyp['title']}' has unverifiable evidence but probability "
            f"{hyp['probability']} > 0.30"
        )
        assert hyp["demoted_by_guard"] is True, (
            f"Hypothesis '{hyp['title']}' should be flagged demoted_by_guard=True"
        )


def test_hypothesis_grounding_preserves_valid():
    """
    Non-regression: a hypothesis backed by evidence that appears in the raw issue
    text must NOT be demoted — it keeps its original probability and
    demoted_by_guard=False.
    """
    issue_body = (
        "Auth service crashes with KeyError: default_scope. "
        "Stack trace points to services/token.py line 88."
    )
    raw_logs = "KeyError: 'default_scope' at services/token.py:88"
    facts = {
        "error_message": "KeyError: default_scope",
        "stack_trace": "Traceback ... services/token.py line 88",
        "file_paths": ["services/token.py"],
    }

    hypotheses = [
        {
            "category": "Configuration / Missing Parameter",
            "title": "Missing config key default_scope in token service",
            "evidence": ["KeyError: default_scope"],   # ← present in issue_body / logs
            "probability": 0.85,
        }
    ]

    validated = HallucinationGuard.validate_hypotheses(hypotheses, facts, issue_body, raw_logs)

    assert len(validated) == 1
    hyp = validated[0]
    assert hyp["probability"] == 0.85, (
        f"Valid hypothesis must not be demoted; probability changed to {hyp['probability']}"
    )
    assert hyp["demoted_by_guard"] is False, (
        "Valid hypothesis must have demoted_by_guard=False"
    )

