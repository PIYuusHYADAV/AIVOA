from typing import TypedDict, Optional, List, Dict, Any


class ComplaintState(TypedDict, total=False):
    # --- inputs ---
    raw_text: str                          # pasted text or text extracted from an uploaded doc
    current_fields: Dict[str, Any]         # whatever is already on the form (for incremental chat turns)
    existing_complaints: List[Dict[str, Any]]  # recent complaints from DB, for duplicate detection
    user_message: Optional[str]            # if this run was triggered by a chat message rather than a fresh doc

    # --- outputs, filled in by each node ---
    fields: Dict[str, Any]
    confidence: Dict[str, float]
    missing_fields: List[str]
    severity: str
    priority: str
    severity_reasoning: str
    duplicate_of: Optional[str]
    duplicate_score: Optional[float]
    root_cause_suggestion: str
    capa_suggestion: str
    summary: str
    next_steps: List[str]
    precautions: List[str]
    assistant_message: str
