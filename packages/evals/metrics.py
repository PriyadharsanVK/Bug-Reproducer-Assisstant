from typing import Dict, Any, List

def compute_repro_completeness_score(repro_steps: List[Dict[str, Any]]) -> float:
    """RCS = (Verified Steps / Total Steps) * 100%"""
    if not repro_steps:
        return 0.0
    verified = sum(1 for step in repro_steps if step.get("sandbox_verified", False))
    return round((verified / len(repro_steps)) * 100.0, 2)

def compute_clarification_efficiency(questions_asked: int) -> float:
    """Target: <= 1.5 questions per run"""
    return float(questions_asked)

def compute_test_usefulness_rating(test_artifacts: List[Dict[str, Any]]) -> float:
    """Proxy score based on syntax validity, assertion presence, and framework matching."""
    if not test_artifacts:
        return 0.0
    score = 3.0
    for art in test_artifacts:
        code = art.get("code_content", "")
        if "def test_" in code or "describe(" in code or "it(" in code:
            score += 1.0
        if "assert" in code or "expect(" in code:
            score += 1.0
    return min(5.0, score)

def evaluate_run_record(run_data: Dict[str, Any]) -> Dict[str, float]:
    steps = run_data.get("repro_steps", [])
    artifacts = run_data.get("test_artifacts", [])
    unknowns = run_data.get("unknowns", [])

    return {
        "repro_completeness_score": compute_repro_completeness_score(steps),
        "clarification_count": compute_clarification_efficiency(len(unknowns)),
        "test_usefulness_score": compute_test_usefulness_rating(artifacts),
        "overall_confidence": run_data.get("overall_confidence", 0.0)
    }
