
import json
import logging
from typing import Optional
from langchain_groq import ChatGroq
from app.config import get_settings

logger = logging.getLogger("aivoa.llm")

settings = get_settings()

_primary_llm: Optional[ChatGroq] = None
_fallback_llm: Optional[ChatGroq] = None


def _primary() -> ChatGroq:
    global _primary_llm
    if _primary_llm is None:
        _primary_llm = ChatGroq(
            model=settings.groq_model,
            api_key=settings.groq_api_key,
            temperature=0.1,
        )
    return _primary_llm


def _fallback() -> ChatGroq:
    global _fallback_llm
    if _fallback_llm is None:
        _fallback_llm = ChatGroq(
            model=settings.groq_fallback_model,
            api_key=settings.groq_api_key,
            temperature=0.2,
        )
    return _fallback_llm


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        text = text.replace("json\n", "", 1) if text.startswith("json\n") else text
    return text.strip()


def call_json(system_prompt: str, user_prompt: str, use_fallback_model: bool = False) -> dict:
    
    llm = _fallback() if use_fallback_model else _primary()
    messages = [
        ("system", system_prompt + "\n\nRespond with ONLY valid JSON. No markdown fences, no commentary."),
        ("human", user_prompt),
    ]
    try:
        raw = llm.invoke(messages).content
        return json.loads(_strip_code_fence(raw))
    except Exception as e:
        logger.warning(f"Primary model JSON parse failed ({e}); retrying with fallback model")
        if use_fallback_model:
            raise
        try:
            raw = _fallback().invoke(messages).content
            return json.loads(_strip_code_fence(raw))
        except Exception as e2:
            logger.error(f"Fallback model also failed: {e2}")
            raise


def call_text(system_prompt: str, user_prompt: str, use_fallback_model: bool = True) -> str:
   
    llm = _fallback() if use_fallback_model else _primary()
    messages = [("system", system_prompt), ("human", user_prompt)]
    return llm.invoke(messages).content.strip()
