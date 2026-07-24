from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
import json

from app.db import get_db
from app.models import Complaint
from app.schemas import ExtractResponse, ComplaintFields
from app.llm.ingest import extract_text_from_upload
from app.agents.graph import complaint_graph

router = APIRouter(prefix="/api", tags=["extract"])


def _recent_complaints_for_dupe_check(db: Session, limit: int = 25):
    rows = db.query(Complaint).order_by(desc(Complaint.created_at)).limit(limit).all()
    return [
        {"id": c.id, "product_name": c.product_name, "batch_lot_number": c.batch_lot_number, "complaint_type": c.complaint_type}
        for c in rows
    ]


def _run_pipeline(db: Session, raw_text: str, current_fields: Optional[dict]) -> ExtractResponse:
    if not raw_text or not raw_text.strip():
        raise HTTPException(status_code=400, detail="No complaint text found to analyze.")

    result = complaint_graph.invoke({
        "raw_text": raw_text,
        "current_fields": current_fields or {},
        "existing_complaints": _recent_complaints_for_dupe_check(db),
    })

    return ExtractResponse(
        fields=ComplaintFields(**result.get("fields", {})),
        confidence=result.get("confidence", {}),
        missing_fields=result.get("missing_fields", []),
        severity_reasoning=result.get("severity_reasoning"),
        root_cause_suggestion=result.get("root_cause_suggestion"),
        capa_suggestion=result.get("capa_suggestion"),
        summary=result.get("summary"),
        duplicate_of=result.get("duplicate_of"),
        duplicate_score=result.get("duplicate_score"),
        assistant_message=result.get("assistant_message", ""),
        next_steps=result.get("next_steps", []),
        precautions=result.get("precautions", []),
    )


@router.post("/extract/text", response_model=ExtractResponse)
def extract_from_text(payload: dict, db: Session = Depends(get_db)):
    """Body: { "text": "...", "current_fields": {...} }"""
    text = payload.get("text", "")
    current_fields = payload.get("current_fields")
    return _run_pipeline(db, text, current_fields)


@router.post("/extract/file", response_model=ExtractResponse)
async def extract_from_file(
    file: UploadFile = File(...),
    current_fields: Optional[str] = Form(default=None),
    db: Session = Depends(get_db),
):
    """Multipart upload: file + optional JSON-encoded current_fields string."""
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File exceeds 10MB limit.")

    try:
        raw_text = extract_text_from_upload(file.filename, content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    parsed_fields = json.loads(current_fields) if current_fields else None
    return _run_pipeline(db, raw_text, parsed_fields)
