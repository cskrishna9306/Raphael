# Import standard packages
from pydantic import BaseModel

# Import LangChain packages
from langchain_google_genai import ChatGoogleGenerativeAI

# Import custom modules
from src.raphael.agentry.config import config
from src.raphael.agentry.screenplay_breakdown.models import CharacterProfile
from src.raphael.agentry.casting_director.models import CastingCandidate

def structuring_model(schema: type[BaseModel], model_id: str = config.MODEL_ID):
    """
    Builds a plain LLM call constrained to a given structured-output schema.
    """
    return ChatGoogleGenerativeAI(
        model=model_id,
        vertexai=True,
        project=config.GOOGLE_CLOUD_PROJECT,
        location=config.GOOGLE_CLOUD_LOCATION,
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

def candidate_risk_query(candidate: CastingCandidate) -> str:
    """
    Builds a risk-research search query for a single casting candidate.
    """
    return (
        f"Actor: {candidate.name}\n"
        f"Casting context: {candidate.fit_rationale or 'unspecified'}\n"
        f"Known bio: {candidate.dossier.bio_summary if candidate.dossier else 'unspecified'}"
    )
