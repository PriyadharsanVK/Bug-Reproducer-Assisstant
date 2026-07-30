import json
import re
import logging
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)

class HallucinationGuard:
    @staticmethod
    def enforce_schema_and_tripartition(
        raw_llm_output: str,
        issue_body: str,
        raw_logs: str = ""
    ) -> Tuple[Dict[str, Any], bool]:
        """
        Validates LLM output against hallucination safeguards:
        1. Ensures raw stack traces or file paths mentioned in 'Facts' actually exist in original issue or logs.
        2. Automatically demotes non-existent file path claims from 'Facts' to 'Inferred Assumptions'.
        """
        try:
            # Extract JSON block if wrapped in markdown
            match = re.search(r"```json\s*(.*?)\s*```", raw_llm_output, re.DOTALL)
            json_str = match.group(1) if match else raw_llm_output
            data = json.loads(json_str)

            combined_source = (issue_body + "\n" + (raw_logs or "")).lower()
            facts = data.get("facts", {})
            file_paths = facts.get("file_paths", [])

            verified_files = []
            demoted_assumptions = []

            for fp in file_paths:
                # Basic string or filename check
                file_basename = fp.split("/")[-1].lower()
                if file_basename in combined_source or fp.lower() in combined_source:
                    verified_files.append(fp)
                else:
                    demoted_assumptions.append({
                        "field": "file_path",
                        "value": fp,
                        "reasoning": "File path claimed as fact was not present in raw issue text; demoted by HallucinationGuard.",
                        "confidence": 0.50
                    })

            facts["file_paths"] = verified_files
            data["facts"] = facts
            
            existing_assumptions = data.get("inferred_assumptions", [])
            existing_assumptions.extend(demoted_assumptions)
            data["inferred_assumptions"] = existing_assumptions

            return data, True
        except Exception as e:
            logger.error(f"HallucinationGuard failed parsing JSON: {e}")
            return {}, False

    @staticmethod
    def validate_hypotheses(
        hypotheses: List[Dict[str, Any]],
        facts: Dict[str, Any],
        issue_body: str,
        raw_logs: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Validates hypothesis evidence against raw source material.

        Mirrors the file-path hallucination check: any hypothesis whose evidence
        list is null/empty, or whose evidence strings cannot be found in the
        combined source text (issue body + raw logs + known facts), is demoted
        to probability <= 0.30 and flagged with demoted_by_guard=True.

        A hypothesis is considered grounded if at least one evidence string
        appears (case-insensitive substring) in the combined source.
        """
        # Build the searchable corpus from raw text + fact values
        fact_values = " ".join(str(v) for v in facts.values() if v)
        combined_source = (issue_body + "\n" + (raw_logs or "") + "\n" + fact_values).lower()

        validated: List[Dict[str, Any]] = []
        for hyp in hypotheses:
            evidence = hyp.get("evidence")
            probability = float(hyp.get("probability", 0.5))

            # Determine whether the hypothesis has verifiable evidence
            is_grounded = False
            if evidence:  # non-null and non-empty list
                for ev_item in evidence:
                    if ev_item and str(ev_item).strip().lower() in combined_source:
                        is_grounded = True
                        break

            if not is_grounded:
                logger.warning(
                    f"HallucinationGuard: hypothesis '{hyp.get('title')}' has "
                    f"null/empty/unverifiable evidence; demoting from {probability:.2f} to 0.30."
                )
                hyp = {**hyp, "probability": 0.30, "demoted_by_guard": True}
            else:
                hyp = {**hyp, "demoted_by_guard": False}

            validated.append(hyp)

        return validated
