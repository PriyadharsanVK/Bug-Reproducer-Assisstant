import re
from typing import Dict, Any, List

def calculate_step_confidence(
    action: str,
    expected_outcome: str,
    has_exact_command: bool,
    has_file_reference: bool
) -> float:
    """Calculate deterministic confidence score for an individual reproduction step."""
    base_score = 0.50
    if has_exact_command:
        base_score += 0.25
    if has_file_reference:
        base_score += 0.15
    if expected_outcome and len(expected_outcome.strip()) > 10:
        base_score += 0.10
    return min(1.00, round(base_score, 2))

def calculate_overall_repro_confidence(
    facts: Dict[str, Any],
    inferred_assumptions: List[Dict[str, Any]],
    unknowns: List[Any],
    repro_steps: List[Dict[str, Any]]
) -> float:
    """
    Deterministic Overall Confidence Formula:
    Overall Confidence = 0.35 * Fact_Completeness 
                       + 0.25 * Step_Quality 
                       + 0.20 * Log_Evidence_Presence 
                       - 0.15 * Unknown_Penalty 
                       + 0.05 * Consistency_Bonus
    """
    # 1. Fact Completeness (0 to 1)
    fact_score = 0.0
    if facts.get("error_message"):
        fact_score += 0.4
    if facts.get("stack_trace"):
        fact_score += 0.4
    if facts.get("file_paths"):
        fact_score += 0.2

    # 2. Step Quality
    if repro_steps:
        step_confidences = [step.get("confidence", 0.5) for step in repro_steps]
        step_quality = sum(step_confidences) / len(step_confidences)
    else:
        step_quality = 0.0

    # 3. Log Evidence Presence
    log_evidence = 1.0 if facts.get("stack_trace") else 0.2

    # 4. Unknown Penalty
    unknown_count = len(unknowns)
    unknown_penalty = min(0.40, unknown_count * 0.10)

    # 5. Consistency Bonus
    consistency_bonus = 0.05 if fact_score > 0.6 and step_quality > 0.6 else 0.0

    final_score = (
        0.35 * fact_score +
        0.25 * step_quality +
        0.20 * log_evidence -
        0.15 * unknown_penalty +
        consistency_bonus
    )
    return max(0.00, min(1.00, round(final_score, 2)))
