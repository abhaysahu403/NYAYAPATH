"""Pydantic schemas: every LLM output is validated here before it is trusted."""
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

from judgments.models import LegalTopic

TOPIC_CODES = {c for c, _ in LegalTopic.choices}
ClaimKind = Literal["SOURCE_INFO", "INTERPRETATION", "POSSIBLE_OPTION", "UNKNOWN", "USER_PROVIDED"]


class IntakeResult(BaseModel):
    language: Literal["hi", "en", "hinglish"] = "en"
    legal_topic: str = "OTHER"
    problem_summary_en: Optional[str] = None
    problem_summary_hi: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    court: Optional[str] = None
    case_number: Optional[str] = None
    cnr: Optional[str] = None
    existing_case: Optional[bool] = None
    case_age_years: Optional[float] = Field(default=None, ge=0, le=80)
    documents: List[str] = Field(default_factory=list)
    property_type: Optional[str] = None
    property_size: Optional[str] = None
    key_issues: List[str] = Field(default_factory=list)
    issue_flags: List[str] = Field(default_factory=list)
    search_keywords: List[str] = Field(default_factory=list)
    urgency: Literal["LOW", "MEDIUM", "HIGH"] = "MEDIUM"

    @field_validator("legal_topic", mode="before")
    @classmethod
    def _topic(cls, v):
        v = str(v or "OTHER").strip().upper().replace(" ", "_")
        return v if v in TOPIC_CODES else "OTHER"

    @field_validator("key_issues", "search_keywords", "documents", mode="before")
    @classmethod
    def _list(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        return [str(i).strip() for i in v if str(i).strip()][:10]

    @field_validator("state", "district", "court", "case_number", "cnr", "property_type", "property_size", mode="before")
    @classmethod
    def _blank(cls, v):
        if v is None:
            return None
        v = str(v).strip()
        return None if v.lower() in {"", "null", "none", "unknown", "n/a"} else v[:200]

    @field_validator("case_age_years", mode="before")
    @classmethod
    def _age(cls, v):
        try:
            return float(v) if v not in (None, "", "null") else None
        except (TypeError, ValueError):
            return None


class QueryRewrite(BaseModel):
    queries: List[str] = Field(default_factory=list, max_length=5)
    keywords: List[str] = Field(default_factory=list, max_length=12)


class Claim(BaseModel):
    text: str
    kind: ClaimKind = "INTERPRETATION"
    source_ids: List[str] = Field(default_factory=list)


class NextStep(BaseModel):
    title: str
    detail: str = ""
    source_ids: List[str] = Field(default_factory=list)


class GroundedAnswer(BaseModel):
    answer: str
    claims: List[Claim] = Field(default_factory=list)
    next_steps: List[NextStep] = Field(default_factory=list, max_length=6)
    unknowns: List[str] = Field(default_factory=list, max_length=6)


class PlanStep(BaseModel):
    title: str
    description: str
    why_relevant: str = ""
    required_documents: List[str] = Field(default_factory=list)
    legal_basis: Optional[str] = None
    estimated_timeline: Optional[str] = None
    difficulty: Literal["EASY", "MEDIUM", "HARD"] = "MEDIUM"
    kind: Literal["POSSIBLE_OPTION", "INFORMATION_GATHERING"] = "POSSIBLE_OPTION"
    source_ids: List[str] = Field(default_factory=list)


class PlanResult(BaseModel):
    title: str
    situation_assessment: str
    delay_cause_analysis: Optional[str] = None
    immediate_priority: Optional[str] = None
    steps: List[PlanStep] = Field(min_length=1, max_length=8)
    warnings: List[str] = Field(default_factory=list, max_length=8)


class JudgmentExplanation(BaseModel):
    plain_summary: str
    key_facts: List[str] = Field(default_factory=list)
    legal_issue: Optional[str] = None
    court_reasoning: Optional[str] = None
    outcome: Optional[str] = None
    relevance_to_question: Optional[str] = None
    source_ids: List[str] = Field(default_factory=list)


class DocumentAnalysis(BaseModel):
    document_type: Optional[str] = None
    plain_summary: str
    key_facts: List[str] = Field(default_factory=list)
    important_dates: List[str] = Field(default_factory=list)
    parties: List[str] = Field(default_factory=list)
    suggested_questions: List[str] = Field(default_factory=list)
    source_ids: List[str] = Field(default_factory=list)
