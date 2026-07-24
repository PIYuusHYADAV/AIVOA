from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db import get_db
from app.models import Complaint
from app.schemas import ChatRequest, ChatResponse, ComplaintFields
from app.agents.graph import complaint_graph
from app.llm.groq_client import call_text

router = APIRouter(prefix="/api", tags=["chat"])

GENERAL_QA_SYSTEM_PROMPT = """You are the "AI Complaint Intake Assistant" chat panel next to a
pharmaceutical QMS Customer Complaint form. The user may: (a) give you more details about the
complaint to fill in the form, (b) ask you a general question (e.g. "why is this marked
Critical?", "what should I do next?"), or (c) ask about QMS/complaint-handling concepts. Answer
directly, concisely (2-4 sentences), and in a professional-but-friendly tone. If relevant, refer
to the current form data given to you.
"""


def _looks_like_new_complaint_info(message: str) -> bool:
    """Heuristic: short questions ("why?", "what next?") get a conversational
    answer only; anything else is treated as potential new complaint detail and
    re-run through the extraction pipeline so the form can update live."""
    q_markers = ["why", "what should", "how do i", "what does", "explain", "what next", "?"]
    msg = message.strip().lower()
    if len(msg.split()) <= 6 and any(msg.startswith(m) or msg.endswith("?") for m in q_markers):
        return False
    return True


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    current_fields = payload.current_fields.model_dump()

    if _looks_like_new_complaint_info(payload.message):
        existing = db.query(Complaint).order_by(desc(Complaint.created_at)).limit(25).all()
        existing_dicts = [
            {"id": c.id, "product_name": c.product_name, "batch_lot_number": c.batch_lot_number, "complaint_type": c.complaint_type}
            for c in existing
        ]
        result = complaint_graph.invoke({
            "raw_text": payload.message,
            "current_fields": current_fields,
            "existing_complaints": existing_dicts,
        })
        return ChatResponse(
            assistant_message=result.get("assistant_message", ""),
            updated_fields=ComplaintFields(**result.get("fields", {})),
            next_steps=result.get("next_steps", []),
            precautions=result.get("precautions", []),
        )

    # General Q&A -- no field extraction, just a grounded conversational reply
    history_text = "\n".join(f"{m.role}: {m.content}" for m in payload.history[-6:])
    user_prompt = f"""Current form data:\n{current_fields}\n\nRecent conversation:\n{history_text}\n\nUser's new message: {payload.message}"""
    reply = call_text(GENERAL_QA_SYSTEM_PROMPT, user_prompt)
    return ChatResponse(assistant_message=reply, updated_fields=None, next_steps=[], precautions=[])
