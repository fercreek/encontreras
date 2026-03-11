"""
AI Synthesis Engine to generate Context, Why They Matter, and Icebreakers.
Uses Google Gemini API via google-genai package.
"""

from __future__ import annotations

import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

from src.core.models import Business

# Load environment variables
load_dotenv()

def get_client() -> genai.Client | None:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    return genai.Client(api_key=api_key)

SYSTEM_PROMPT = """
Eres un estratega de ventas B2B experto en prospección.
Te proporcionaré datos extraídos (Scraping) de un negocio. Tu trabajo es analizar la información y devolver un objeto JSON con 3 campos:
1. "context": Un resumen breve (1-2 oraciones) de lo que hace el negocio, su ubicación y su enfoque (basado en nombre y categoría).
2. "why_they_matter": Un análisis corto de si es un buen prospecto. Mezcla su score, nivel de precio, ratings y especialmente problemas en su sitio web o seguidores en redes sociales. ¿Por qué deberíamos contactarlos?
3. "icebreaker": Un mensaje directo o correo MUY corto y casual (1-2 párrafos max) para iniciar conversación. Hazlo sonar humano y empático. Menciona algún problema de los que detectamos (ej. su web está caída, falta de H1, o no tienen muchos seguidores) y ofrece ayuda indirectamente sin sonar a vendedor desesperado.

El JSON DEBE DEVOLVER SOLAMENTE ESTAS 3 LLAVES.
"""

def synthesize_business(business: Business) -> dict | None:
    """Analyze a business using Gemini and return the synthesized context and icebreaker."""
    client = get_client()
    if not client:
        return None

    model_id = "gemini-2.5-flash"
    
    # Prepare the payload to send to the LLM
    business_data = {
        "name": business.name,
        "category": business.category,
        "location": business.address,
        "score": business.score,
        "quality_label": business.quality_label,
        "rating": business.rating,
        "reviews_count": business.reviews_count,
        "price_level": business.price_level,
        "website": business.website,
        "site_status": business.site_status,
        "site_issues": business.site_issues,
        "instagram": business.instagram,
        "ig_followers": business.ig_followers,
        "facebook": business.facebook,
        "tiktok": business.tiktok,
    }

    prompt = f"Analiza esta empresa:\n{json.dumps(business_data, ensure_ascii=False, indent=2)}"

    try:
        response = client.models.generate_content(
            model=model_id,
            contents=[prompt],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
            )
        )
        
        result_text = response.text
        if result_text:
            return json.loads(result_text)
        return None
    except Exception as e:
        print(f"Error LLM synthesis: {e}")
        return None
