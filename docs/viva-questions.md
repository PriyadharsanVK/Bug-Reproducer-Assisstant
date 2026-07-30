# University Evaluation & Defense (Viva) Questions

### Q1: How does your system prevent LLM hallucinations when generating reproduction steps?
**Answer**: We implement a strict **HallucinationGuard** middleware that validates LLM JSON outputs against original text. If a file path or log trace claimed as a "Fact" is missing from raw input data, it is automatically demoted to an "Inferred Assumption" with a reduced confidence score.

### Q2: Why did you choose Groq API exclusively over other providers?
**Answer**: Groq provides deterministic high-throughput inference for open-weights models (`llama-3.3-70b`, `llama-3.1-8b`, `deepseek-r1-distill`). This allows multi-stage pipeline execution (extraction, clarification, code generation) to complete in under 5 seconds.

### Q3: How do you handle security when running untrusted reproduction code?
**Answer**: Reproduction scripts are executed inside SWE-agent's containerized sandbox (`sweagent/environment`) with non-root privileges, isolated network bridges, and memory/CPU limits.
