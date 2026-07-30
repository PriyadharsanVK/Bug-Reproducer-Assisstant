# Academic & Technical Novelty Statement

## 1. Tripartition of Truth (Zero-Hallucination Safeguard)
Unlike existing LLM triage tools that risk inventing non-existent file paths or stack traces when issue reports are incomplete, **Bug Reproducer Assistant** enforces a strict mathematical tripartition into **Facts** (verifiable data in original text), **Inferred Assumptions** (explicitly scored probabilities), and **Unknowns**.

## 2. Multi-Tier Model Routing over Groq Ultra-Low Latency Infrastructure
By routing rapid clarification loops to `llama-3.1-8b-instant` and complex test generation to `deepseek-r1-distill-llama-70b`, the system achieves sub-second HITL query generation and sub-minute end-to-end bug reproduction verification.

## 3. Containerized Verification via Adapted SWE-Agent Engine
Instead of producing static text recommendations, the platform adapts SWE-agent to run reproduction shell scripts inside isolated Docker containers, guaranteeing machine-verified reproduction outcomes.
