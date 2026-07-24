
import io
import email
from email import policy
from pypdf import PdfReader
from docx import Document


def extract_text_from_upload(filename: str, content: bytes) -> str:
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""

    if ext == "pdf":
        return _extract_pdf(content)
    if ext == "docx":
        return _extract_docx(content)
    if ext == "eml":
        return _extract_eml(content)
    if ext == "txt":
        return content.decode("utf-8", errors="ignore")

    # Best-effort fallback for unknown extensions
    try:
        return content.decode("utf-8", errors="ignore")
    except Exception:
        raise ValueError(f"Unsupported file type: .{ext}")


def _extract_pdf(content: bytes) -> str:
    reader = PdfReader(io.BytesIO(content))
    return "\n".join(page.extract_text() or "" for page in reader.pages).strip()


def _extract_docx(content: bytes) -> str:
    doc = Document(io.BytesIO(content))
    return "\n".join(p.text for p in doc.paragraphs).strip()


def _extract_eml(content: bytes) -> str:
    msg = email.message_from_bytes(content, policy=policy.default)
    parts = [f"From: {msg.get('from', '')}", f"Subject: {msg.get('subject', '')}"]
    body = msg.get_body(preferencelist=("plain", "html"))
    if body:
        parts.append(body.get_content())
    return "\n".join(parts).strip()
