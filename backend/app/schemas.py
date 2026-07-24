from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class ComplaintFields(BaseModel):
    """The exact set of fields shown on the left-hand form."""
    complaint_source: Optional[str] = None
    customer_name: Optional[str] = None
    product_name: Optional[str] = None
    product_strength: Optional[str] = None
    batch_lot_number: Optional[str] = None
    manufacturing_date: Optional[str] = None
    expiry_date: Optional[str] = None
    quantity_affected: Optional[str] = None
    complaint_type: Optional[str] = None
    complaint_date: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None
    priority: Optional[str] = None


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ExtractRequest(BaseModel):
    text: Optional[str] = None  # pasted complaint text / email body
    current_fields: Optional[ComplaintFields] = None  # fields already on the form, for incremental refinement


class ExtractResponse(BaseModel):
    fields: ComplaintFields
    confidence: Dict[str, float]
    missing_fields: List[str]
    severity_reasoning: Optional[str] = None
    root_cause_suggestion: Optional[str] = None
    capa_suggestion: Optional[str] = None
    summary: Optional[str] = None
    duplicate_of: Optional[str] = None
    duplicate_score: Optional[float] = None
    assistant_message: str
    next_steps: List[str] = []
    precautions: List[str] = []


class ChatRequest(BaseModel):
    message: str
    current_fields: ComplaintFields
    history: List[ChatMessage] = []


class ChatResponse(BaseModel):
    assistant_message: str
    updated_fields: Optional[ComplaintFields] = None
    next_steps: List[str] = []
    precautions: List[str] = []


class ComplaintCreate(ComplaintFields):
    raw_source_text: Optional[str] = None
    ai_root_cause: Optional[str] = None
    ai_capa: Optional[str] = None
    ai_summary: Optional[str] = None
    ai_missing_fields: Optional[List[str]] = None
    ai_confidence: Optional[Dict[str, float]] = None
    ai_duplicate_of: Optional[str] = None
    ai_duplicate_score: Optional[float] = None


class ComplaintOut(ComplaintCreate):
    id: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
