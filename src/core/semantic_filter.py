"""
Semantic Filter (Fase 2 - Premium)
B2B Lead Qualifier Agent using Gemini Structured Outputs.
Analyzes bio and recent posts to determine if a lead fits the target niches.
"""

from __future__ import annotations

import os
import json
from enum import Enum
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

def get_client() -> genai.Client | None:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    return genai.Client(api_key=api_key)

class MatchType(str, Enum):
    EXPLICIT = "explicit"
    INFERRED = "inferred"
    OUT_OF_NICHE = "out_of_niche"

class LeadQualification(BaseModel):
    is_target_niche: bool = Field(
        description="True si es un prospecto viable enfocado en academias, gimnasios, deportes o restaurantes."
    )
    inferred_niche: str = Field(
        description="El nicho detectado (ej. 'danza', 'fitness', 'restaurante', 'spam')."
    )
    match_type: MatchType = Field(
        description="'explicit' (en la bio), 'inferred' (por los posts), o 'out_of_niche'."
    )
    confidence_score: int = Field(
        description="Nivel de confianza de la clasificación, 1 a 10."
    )
    reasoning: str = Field(
        description="Breve justificación de la decisión (máximo 15 palabras)."
    )

SYSTEM_PROMPT = """
Eres un calificador implacable de leads B2B buscando academias de baile, gimnasios, pilates, deportes y restaurantes.

REGLA CRÍTICA:
Nunca asumas un nicho si no hay evidencia. Si la biografía está vacía o es ambigua ("Atrévete a más"), debes analizar obligatoriamente los textos de los últimos posts para inferir si venden clases, servicios, comida, etc. Si no hay suficiente información, recházalo (is_target_niche=False).
"""

def qualify_lead(bio_text: str, recent_posts_texts: list[str]) -> LeadQualification | None:
    """
    Evaluates lead viability using LLM structured output.
    """
    client = get_client()
    if not client:
        return None

    model_id = "gemini-2.5-flash"
    
    # Payload for the LLM
    data = {
        "bio_text": bio_text or "Vacío",
        "recent_posts_texts": recent_posts_texts or []
    }

    prompt = f"Analiza la siguiente información de perfil y posts:\n{json.dumps(data, ensure_ascii=False, indent=2)}"

    try:
        response = client.models.generate_content(
            model=model_id,
            contents=[prompt],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=LeadQualification,
                temperature=0.1
            )
        )
        
        result_text = response.text
        if result_text:
            parsed_json = json.loads(result_text)
            return LeadQualification(**parsed_json)
        return None
    except Exception as e:
        print(f"Error Semantic Filter: {e}")
        return None
