# Evaluation Metrics & Methodology

## 1. Repro Completeness Score (RCS)
$$\text{RCS} = \frac{\text{Verified Sandbox Steps}}{\text{Total Steps}} \times 100\%$$
- **Goal**: $\ge 85\%$
- **Measurement**: Tracked automatically by checking Docker execution exit codes in `repro_steps`.

## 2. Clarification Efficiency (CE)
$$\text{CE} = \text{Average number of follow-up questions asked per issue}$$
- **Goal**: $\le 1.5$ questions
- **Measurement**: Computed from `clarifications` table entries per `run_id`.

## 3. Developer Acceptance Rate (DAR)
$$\text{DAR} = \frac{\text{Runs rated } \ge 4 \text{ stars}}{\text{Total Rated Runs}} \times 100\%$$
- **Goal**: $\ge 80\%$
- **Measurement**: Collected via developer feedback submissions (`/feedback/{run_id}`).
