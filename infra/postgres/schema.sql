-- Initial PostgreSQL DDL Schema for Bug Reproducer Assistant

CREATE TYPE issue_source_enum AS ENUM ('github', 'jira', 'manual');
CREATE TYPE analysis_status_enum AS ENUM ('queued', 'running', 'needs_input', 'completed', 'failed');

CREATE TABLE IF NOT EXISTS issues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source issue_source_enum NOT NULL,
    source_id VARCHAR(255),
    repository_url VARCHAR(512),
    title VARCHAR(512) NOT NULL,
    body TEXT NOT NULL,
    raw_logs TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS analysis_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    issue_id UUID NOT NULL REFERENCES issues(id) ON DELETE CASCADE,
    status analysis_status_enum NOT NULL DEFAULT 'queued',
    overall_confidence NUMERIC(3,2) CHECK (overall_confidence BETWEEN 0.00 AND 1.00),
    groq_primary_model VARCHAR(128) NOT NULL,
    groq_fast_model VARCHAR(128) NOT NULL,
    groq_code_model VARCHAR(128) NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS extracted_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
    facts JSONB NOT NULL DEFAULT '{}'::jsonb,
    inferred_assumptions JSONB NOT NULL DEFAULT '[]'::jsonb,
    unknowns JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS repro_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
    step_order INT NOT NULL,
    action TEXT NOT NULL,
    expected_outcome TEXT,
    confidence NUMERIC(3,2),
    sandbox_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS clarifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
    question_id VARCHAR(64) NOT NULL,
    question TEXT NOT NULL,
    options JSONB DEFAULT '[]'::jsonb,
    answer TEXT,
    answered_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS test_artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
    test_type VARCHAR(64) NOT NULL,
    framework VARCHAR(64) NOT NULL,
    file_path VARCHAR(512) NOT NULL,
    code_content TEXT NOT NULL,
    execution_passed BOOLEAN,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
    markdown_content TEXT NOT NULL,
    json_content JSONB NOT NULL,
    qa_checklist JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS feedback_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
    developer_rating INT CHECK (developer_rating BETWEEN 1 AND 5),
    repro_successful BOOLEAN NOT NULL,
    comments TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_issues_source ON issues(source, source_id);
CREATE INDEX IF NOT EXISTS idx_analysis_runs_issue ON analysis_runs(issue_id);
CREATE INDEX IF NOT EXISTS idx_analysis_runs_status ON analysis_runs(status);
