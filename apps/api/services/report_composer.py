import os
import json
from typing import Dict, Any, List

class ReportComposer:
    @staticmethod
    def compose_markdown(
        run_id: str,
        issue_title: str,
        overall_confidence: float,
        facts: Dict[str, Any],
        inferred_assumptions: List[Dict[str, Any]],
        unknowns: List[Any],
        repro_steps: List[Dict[str, Any]],
        test_artifacts: List[Dict[str, Any]],
        hypotheses: List[Dict[str, Any]]
    ) -> str:
        md = []
        md.append(f"# Bug Reproduction & Handoff Report")
        md.append(f"**Run ID**: `{run_id}` | **Overall Confidence**: `{overall_confidence * 100:.1f}%`\n")
        md.append(f"## Issue Summary\n**{issue_title}**\n")
        
        md.append("## 1. Facts vs. Assumptions vs. Unknowns")
        md.append(f"- **Facts Extracted**: {json.dumps(facts)}")
        md.append("- **Inferred Assumptions**:")
        for asm in inferred_assumptions:
            md.append(f"  - `{asm.get('field')}` = `{asm.get('value')}` ({asm.get('reasoning')}) [Conf: {asm.get('confidence')}]")
        
        unknowns_str = ", ".join(str(u) for u in unknowns) if unknowns else "None"
        md.append(f"- **Unknowns**: {unknowns_str}")
        md.append("")

        md.append("## 2. Reproduction Steps")
        for step in repro_steps:
            verified_str = "Verified in Sandbox" if step.get("sandbox_verified") else "Unverified"
            md.append(f"{step.get('step_number', 1)}. **{step.get('action')}** (Expected: {step.get('expected_outcome')}) - [{verified_str}]")
        md.append("")

        md.append("## 3. Auto-Generated Test Skeleton")
        for artifact in test_artifacts:
            md.append(f"### File: `{artifact.get('file_path')}` ({artifact.get('framework')})")
            md.append(f"```python\n{artifact.get('code_content')}\n```\n")

        md.append("## 4. Root Cause Candidates")
        for hyp in hypotheses:
            prob = hyp.get('probability', 0.5)
            prob_val = float(prob) if isinstance(prob, (int, float, str)) else 0.5
            md.append(f"- **[{hyp.get('category')}] {hyp.get('title')}** (Prob: {prob_val * 100:.0f}%)")
            for ev in hyp.get("evidence", []):
                md.append(f"  - Evidence: `{ev}`")
        md.append("")

        md.append("## 5. Ready for QA Checklist")
        md.append("- [ ] Environment dependencies verified")
        md.append("- [ ] Reproduction step 1 executed clean")
        md.append("- [ ] Test skeleton integrated into test suite")
        md.append("- [ ] Root cause hypothesis validated")

        return "\n".join(md)
