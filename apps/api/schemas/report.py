from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

class FactItem(BaseModel):
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    file_paths: List[str] = Field(default_factory=list)
    explicit_versions: Dict[str, str] = Field(default_factory=dict)

class InferredAssumption(BaseModel):
    field: str
    value: str
    reasoning: str
    confidence: float

class ReproStepItem(BaseModel):
    step_number: int
    action: str
    expected_outcome: Optional[str] = None
    confidence: float
    sandbox_verified: bool = False

class EnvMatrixItem(BaseModel):
    os: str
    runtime_version: str
    dependency_versions: Dict[str, str]
    risk_rank: int
    reason: str

class HypothesisItem(BaseModel):
    category: str
    title: str
    evidence: List[str]
    probability: float

class TestArtifactItem(BaseModel):
    framework: str
    file_path: str
    code_content: str

class StructuredReport(BaseModel):
    run_id: str
    issue_id: str
    overall_confidence: float
    facts: FactItem
    inferred_assumptions: List[InferredAssumption]
    unknowns: List[str]
    repro_steps: List[ReproStepItem]
    env_matrix: List[EnvMatrixItem]
    hypotheses: List[HypothesisItem]
    test_artifacts: List[TestArtifactItem]
    qa_checklist: List[str]
