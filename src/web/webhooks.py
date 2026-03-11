from fastapi import APIRouter, Request, Header, HTTPException
from typing import Optional
import hmac
import hashlib
import os

router = APIRouter()

# Verify token for Meta Webhook setup
VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN", "cero_secret_token")

@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = "",
    hub_verify_token: str = "",
    hub_challenge: str = ""
):
    """
    Handles the verification challenge from Meta when setting up the webhook.
    """
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Verification failed")

@router.post("/webhook")
async def handle_webhook(request: Request, x_hub_signature_256: Optional[str] = Header(None)):
    """
    Handles incoming messages (WhatsApp, IG, FB) from Meta.
    """
    body = await request.body()
    
    # TODO: Implement signature verification for security
    
    data = await request.json()
    print(f"Received webhook data: {data}")
    
    # Logic to identify client and trigger Brain Switch
    # 1. Extract Meta ID / Phone Number
    # 2. Match with storage/clients database
    # 3. Load Context
    # 4. Generate Response with AI
    
    return {"status": "received"}
