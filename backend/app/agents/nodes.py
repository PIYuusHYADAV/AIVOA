"""
Each function is one node in the LangGraph StateGraph (see graph.py).
Every node reads from `state` and returns a partial dict that LangGraph merges
back into state -- this is the standard LangGraph node contract.
"""
from typing import Dict, Any
from app.llm.groq_client import call_json, call_text

FORM_FIELDS = [
    "complaint_source", "customer_name", "product_name", "product_strength",
    "batch_lot_number", "manufacturing_date", "expiry_date", "quantity_affected",
    "complaint_type", "complaint_date", "description",
]

MANDATORY_FIELDS = [
    "customer_name", "product_name", "batch_lot_number",
    "complaint_type", "description",
]


# ---------------------------------------------------------------------------
# 1. EXTRACTION
# ---------------------------------------------------------------------------
EXTRACTION_SYSTEM_PROMPT = """You are an AI Complaint Intake Assistant for a pharmaceutical
manufacturer's Quality Management System (QMS). Customers describe product complaints in
casual, vague, or incomplete language (emails, phone transcripts, portal messages). Your job
is to extract structured fields for the official Customer Complaint Log.

Extract these fields where you can infer them from the text. If a field is not mentioned or
cannot be reasonably inferred, use null -- never invent data.

Fields:
- complaint_source: how the complaint arrived. One of: "Email", "Phone Call", "Customer Portal", "Field Representative", "Distributor". Infer from tone/context if not explicit.
- customer_name: person or organization name.
- product_name: the drug/product name mentioned.
- product_strength: dosage strength or grade, e.g. "500mg", "10mg/ml", "USP Grade".
- batch_lot_number: batch or lot number, often alphanumeric like "B-2024-118" or "LOT7734".
- manufacturing_date: manufacturing date if mentioned (any format, keep as written).
- expiry_date: expiry date if mentioned.
- quantity_affected: amount affected, include unit, e.g. "12 tablets", "3 boxes", "5 kg".
- complaint_type: category of the issue. Choose the best-fitting category, e.g. "Discoloration",
  "Broken Seal / Tamper Evidence", "Foreign Particle", "Physical Damage", "Missing Label",
  "Adverse Event / Reaction", "Short Fill", "Odor / Smell Issue", "Packaging Defect", "Efficacy Concern", "Other".
- complaint_date: the date the issue was noticed/reported, if mentioned.
- description: a clear, professional 1-3 sentence restatement of the complaint in formal QMS
  language, based only on what the customer actually said.

Also return:
- confidence: an object mapping each field name above to a 0.0-1.0 confidence score for the value you extracted (0 if null).

Return this exact JSON shape:
{
  "fields": { <the 11 fields above> },
  "confidence": { <field_name>: <0-1 float>, ... }
}
"""


def extract_fields_node(state: Dict[str, Any]) -> Dict[str, Any]:
    raw_text = state.get("raw_text", "") or state.get("user_message", "")
    current_fields = state.get("current_fields") or {}

    user_prompt = f"""Existing form values already captured (may be partially filled -- only
override a field if the new text gives clearer/more specific information for it):
{current_fields}

Customer's complaint text to analyze:
\"\"\"{raw_text}\"\"\"
"""
    result = call_json(EXTRACTION_SYSTEM_PROMPT, user_prompt)
    fields = result.get("fields", {})
    confidence = result.get("confidence", {})

    # Merge: keep any existing value the model didn't override with something non-null
    merged = dict(current_fields)
    for f in FORM_FIELDS:
        val = fields.get(f)
        if val not in (None, "", "null"):
            merged[f] = val

    return {"fields": merged, "confidence": confidence}


# ---------------------------------------------------------------------------
# 2. COMPLETENESS CHECK
# ---------------------------------------------------------------------------
def completeness_check_node(state: Dict[str, Any]) -> Dict[str, Any]:
    fields = state.get("fields", {})
    missing = [f for f in MANDATORY_FIELDS if not fields.get(f)]
    return {"missing_fields": missing}


# ---------------------------------------------------------------------------
# 3. SEVERITY & PRIORITY CLASSIFICATION
# ---------------------------------------------------------------------------
SEVERITY_SYSTEM_PROMPT = """You are a pharmaceutical QMS risk classification assistant.
Classify the SEVERITY and PRIORITY of a customer complaint based on GxP / ICH Q10 style
risk thinking (patient safety impact, GMP impact, regulatory reportability).

severity: one of "Critical", "Major", "Minor"
  - Critical: potential patient harm, adverse event, sterility/contamination risk, wrong product/label (mix-up).
  - Major: quality defect that could affect efficacy or is a significant GMP deviation, but no immediate safety signal (e.g. broken seal, significant short-fill).
  - Minor: cosmetic or packaging issue unlikely to affect safety or efficacy (e.g. minor discoloration, label smudge).

priority: one of "High", "Medium", "Low" -- how urgently this needs QA/QC review and response.

Return ONLY JSON:
{ "severity": "...", "priority": "...", "reasoning": "1-2 sentence justification in QMS language" }
"""


def severity_priority_node(state: Dict[str, Any]) -> Dict[str, Any]:
    fields = state.get("fields", {})
    result = call_json(SEVERITY_SYSTEM_PROMPT, f"Complaint details:\n{fields}")
    fields = dict(fields)
    fields["severity"] = result.get("severity", "Minor")
    fields["priority"] = result.get("priority", "Low")
    return {"fields": fields, "severity_reasoning": result.get("reasoning", "")}


# ---------------------------------------------------------------------------
# 4. DUPLICATE DETECTION (lightweight, no vector DB required for the demo)
# ---------------------------------------------------------------------------
def duplicate_check_node(state: Dict[str, Any]) -> Dict[str, Any]:
    fields = state.get("fields", {})
    existing = state.get("existing_complaints", [])
    if not existing:
        return {"duplicate_of": None, "duplicate_score": None}

    def score(a: Dict[str, Any], b: Dict[str, Any]) -> float:
        keys = ["product_name", "batch_lot_number", "complaint_type"]
        matches = sum(1 for k in keys if a.get(k) and b.get(k) and str(a.get(k)).strip().lower() == str(b.get(k)).strip().lower())
        return matches / len(keys)

    best_id, best_score = None, 0.0
    for c in existing:
        s = score(fields, c)
        if s > best_score:
            best_id, best_score = c.get("id"), s

    if best_score >= 0.66:
        return {"duplicate_of": best_id, "duplicate_score": round(best_score, 2)}
    return {"duplicate_of": None, "duplicate_score": round(best_score, 2) if existing else None}


# ---------------------------------------------------------------------------
# 5. ROOT CAUSE RECOMMENDATION
# ---------------------------------------------------------------------------
ROOT_CAUSE_SYSTEM_PROMPT = """You are a QMS quality engineer. Given a complaint about an
API/FDF pharmaceutical product, suggest the most likely root cause category using standard
QMS root-cause buckets (Man / Machine / Material / Method / Environment / Measurement --
the 5M+E framework), plus a one-line hypothesis. This is a preliminary AI suggestion for the
investigating QA officer, not a final determination -- phrase it that way.
Return ONLY JSON: { "category": "...", "hypothesis": "1-2 sentences" }
"""


def root_cause_node(state: Dict[str, Any]) -> Dict[str, Any]:
    fields = state.get("fields", {})
    result = call_json(ROOT_CAUSE_SYSTEM_PROMPT, f"Complaint details:\n{fields}", use_fallback_model=True)
    text = f"Likely category: {result.get('category', 'Unknown')}. {result.get('hypothesis', '')}"
    return {"root_cause_suggestion": text}


# ---------------------------------------------------------------------------
# 6. CAPA RECOMMENDATION
# ---------------------------------------------------------------------------
CAPA_SYSTEM_PROMPT = """You are a QMS quality engineer drafting a preliminary CAPA
(Corrective and Preventive Action) suggestion for a customer complaint on an API/FDF
pharmaceutical product. Suggest one concrete corrective action and one preventive action.
This is a draft suggestion for the QA officer to review, not a final CAPA.
Return ONLY JSON: { "corrective": "...", "preventive": "..." }
"""


def capa_node(state: Dict[str, Any]) -> Dict[str, Any]:
    fields = state.get("fields", {})
    result = call_json(CAPA_SYSTEM_PROMPT, f"Complaint details:\n{fields}", use_fallback_model=True)
    text = f"Corrective: {result.get('corrective', '')} | Preventive: {result.get('preventive', '')}"
    return {"capa_suggestion": text}


# ---------------------------------------------------------------------------
# 7. SUMMARY + NEXT STEPS + PRECAUTIONS + CONVERSATIONAL MESSAGE
# ---------------------------------------------------------------------------
ASSISTANT_SYSTEM_PROMPT = """You are the "AI Complaint Intake Assistant" chat panel next to a
QMS complaint form. Speak directly to the QA staff member logging the complaint: warm,
concise, professional. You have just analyzed a complaint. Produce:
1. summary: a 1-2 sentence plain-language summary of the complaint.
2. next_steps: 2-4 short imperative next steps for the QA officer right now (e.g. "Quarantine remaining stock from batch X", "Contact customer to confirm exact reaction symptoms").
3. precautions: 1-3 short immediate precautions to reduce risk while the investigation is pending.
4. assistant_message: a short (2-4 sentence) friendly chat message to show the user, mentioning
   the detected severity/priority, whether any mandatory fields are still missing (ask for them
   conversationally if so), and one encouraging/helpful closing line. If duplicate_of is set,
   mention it may be a duplicate of an existing logged complaint.

Return ONLY JSON:
{ "summary": "...", "next_steps": ["..."], "precautions": ["..."], "assistant_message": "..." }
"""


def summary_node(state: Dict[str, Any]) -> Dict[str, Any]:
    fields = state.get("fields", {})
    context = {
        "fields": fields,
        "missing_fields": state.get("missing_fields", []),
        "severity_reasoning": state.get("severity_reasoning", ""),
        "root_cause_suggestion": state.get("root_cause_suggestion", ""),
        "capa_suggestion": state.get("capa_suggestion", ""),
        "duplicate_of": state.get("duplicate_of"),
        "duplicate_score": state.get("duplicate_score"),
    }
    result = call_json(ASSISTANT_SYSTEM_PROMPT, f"Analysis context:\n{context}", use_fallback_model=True)
    return {
        "summary": result.get("summary", ""),
        "next_steps": result.get("next_steps", []),
        "precautions": result.get("precautions", []),
        "assistant_message": result.get("assistant_message", "I've analyzed the complaint."),
    }
