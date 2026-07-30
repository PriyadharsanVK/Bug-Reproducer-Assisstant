# Architecture & System Design Document

## System Components
1. **API Gateway & Ingestion Layer**: Built with FastAPI for async JSON ingestion and webhook processing.
2. **Groq Model Router**: Dynamic LLM routing engine directing sub-tasks to `llama-3.3-70b-versatile`, `llama-3.1-8b-instant`, and `deepseek-r1-distill-llama-70b`.
3. **SWE-agent Sandbox Integration**: Utilizes containerized environment isolation (`sweagent/environment`) to run reproduction steps inside Docker containers safely.
4. **Persistence Layer**: Async PostgreSQL storage for complete run lineage, facts, prompt logs, and developer feedback metrics.
