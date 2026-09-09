# Import standard packages
from typing import TYPE_CHECKING
from pydantic import BaseModel
from io import BytesIO

# Import third-party packages
from fastapi import HTTPException
from pypdf import PdfReader

# Import LangChain packages
from langchain_google_genai import ChatGoogleGenerativeAI

# Import custom modules
from src.raphael.agentry.config import config
from src.raphael.agentry.screenplay_breakdown.models import CharacterProfile

# CastingCandidate is only used for a type hint below (candidate_risk_query) -- a real
# top-level import here creates a circular import (casting_director.agent imports
# structuring_model from this module), which only "worked" before by accident of whichever
# module happened to import casting_director first. TYPE_CHECKING keeps the annotation
# without the runtime import.
if TYPE_CHECKING:
    from src.raphael.agentry.casting_director.models import CastingCandidate

def structuring_model(schema: type[BaseModel], model_id: str = config.MODEL_ID):
    """
    Builds a plain LLM call constrained to a given structured-output schema.

    temperature=0 -- this is an extraction task (turn already-fetched search
    findings into a fixed schema), not a creative one, so the same findings
    should structure the same way every time. Without this, the default
    sampling temperature made casting/risk/enrichment results vary between
    identical runs even when the underlying search findings didn't change.
    """
    return ChatGoogleGenerativeAI(
        model=model_id,
        vertexai=True,
        project=config.GOOGLE_CLOUD_PROJECT,
        location=config.GOOGLE_CLOUD_LOCATION,
        temperature=0,
        timeout=config.LLM_TIMEOUT_SECONDS,
        max_retries=config.LLM_MAX_RETRIES,
    ).with_structured_output(schema)

def character_query(character: CharacterProfile) -> str:
    """
    Builds a casting search query from a single character's breakdown.
    """
    return (
        f"Character: {character.name}\n"
        f"Role size: {character.role_presence.value}\n"
        f"Gender: {character.gender.value}\n"
        f"Age range: {character.age_range or 'unspecified'}\n"
        f"Description: {character.description or 'unspecified'}\n"
        f"Traits: {', '.join(character.traits) if character.traits else 'unspecified'}"
    )

def candidate_risk_query(candidate: "CastingCandidate") -> str:
    """
    Builds a risk-research search query for a single casting candidate.
    """
    return (
        f"Actor: {candidate.name}\n"
        f"Casting context: {candidate.fit_rationale or 'unspecified'}\n"
        f"Known bio: {candidate.dossier.bio_summary if candidate.dossier else 'unspecified'}"
    )

def extract_text(filename: str, content: bytes) -> str:
    """
    Extracts plain text from an uploaded screenplay document. Supports
    .txt (decoded as-is) and .pdf (text pulled page-by-page via pypdf, no
    OCR -- scanned/image-only PDFs will yield empty/partial text).
    """
    if filename.lower().endswith(".pdf"):
        reader = PdfReader(BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    if filename.lower().endswith(".txt"):
        return content.decode("utf-8")

    raise HTTPException(
        status_code=400,
        detail=f"Unsupported file type for '{filename}' -- expected one of {config.SUPPORTED_EXTENSIONS}.",
    )
