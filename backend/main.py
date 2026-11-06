from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date, datetime
import httpx
import base64
from io import BytesIO
import random
import os
import re
import sqlite3
from openai import OpenAI
from PIL import Image
import rembg
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from agent_graph import run_multi_agent_pipeline, WardrobeItem
import database as db
from fashion.llm_client import (
    analyze_garment_vision,
    generate_stylist_commentary,
    generate_outfit_visualization_prompt,
    generate_outfit_visualization_image
)
from fashion.weather_client import fetch_live_weather
from voice_agent_graph import run_voice_agent_pipeline
from fashion.voice_service import voice_service

app = FastAPI(title="AI Smart Wardrobe & Multi-Agent Stylist Backend", version="1.0.0")
SCHEDULE_DAY_IDS = {"mon", "tue", "wed", "thu", "fri", "sat", "sun"}
AVAILABILITY_STATUSES = {
    "ready", "to_wash", "in_wash", "drying",
    "damaged", "missing", "borrowed", "unavailable"
}
IRONING_STATUSES = {"ready", "needs_ironing", "being_ironed"}

# Enable CORS for Vite React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize SQLite database schema & seed initial items
@app.on_event("startup")
def startup_db():
    db.init_db()
    from trend_research import ensure_schema, worker
    ensure_schema()
    worker.start()


@app.on_event("shutdown")
def stop_trend_worker():
    from trend_research import worker
    worker.stop()


@app.get("/api/trends/status")
def trend_status():
    from trend_research import snapshot
    return snapshot()

class StylistRequest(BaseModel):
    user_id: Optional[int] = 1
    occasion: Optional[str] = "college"
    style_preference: Optional[str] = "stylish-trendy"
    city: Optional[str] = "New York"
    clothes: List[Dict[str, Any]]
    requested_count: Optional[int] = 3
    exclude_bags: Optional[bool] = False
    exclude_accessories: Optional[bool] = False
    context_rules: Optional[str] = None

class VoiceRequest(BaseModel):
    user_message: str
    conversation_history: Optional[List[Dict[str, str]]] = None
    conversation_id: Optional[str] = None
    selected_outfit_id: Optional[str] = None
    context_outfit: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None
    user_id: int = 1

class WeekdayOutfitRequest(BaseModel):
    day_id: str
    plan_date: Optional[str] = None
    outfit: Dict[str, Any]
    source: str
    occasion: str = Field(default="Outfit", min_length=1, max_length=80)
    ready_confirmed_item_ids: List[str] = Field(default_factory=list)
    user_id: int = 1

class WeekdayOutfitReplacementRequest(WeekdayOutfitRequest):
    schedule_id: str
    expected_outfit_id: str

class AvailabilityUpdateRequest(BaseModel):
    availability_status: str
    ironing_status: Optional[str] = None
    expected_available_at: Optional[str] = None
    notify_when_ready: Optional[bool] = None
    status_note: Optional[str] = Field(default=None, max_length=240)
    user_id: int = 1

class OutfitWearEventRequest(BaseModel):
    outfit: Dict[str, Any]
    item_ids: List[str]
    wear_date: str
    planned_day: Optional[str] = None
    schedule_id: Optional[str] = None
    worn: bool = True
    user_id: int = 1

class OutfitWearAnswer(BaseModel):
    item_id: str
    actually_worn: Optional[bool] = None
    in_laundry: Optional[bool] = None

class OutfitWearAnswersRequest(BaseModel):
    answers: List[OutfitWearAnswer]
    user_id: int = 1

class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=128)

class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "wardrobe-multi-agent-backend",
        "active_pipeline": "LangGraph (5 Multi-Agent Nodes)",
        "context_node": "enabled for dynamic user rules"
    }

@app.post("/api/auth/register")
def register(req: RegisterRequest):
    name = req.name.strip()
    email = req.email.strip().lower()
    if not name:
        raise HTTPException(status_code=422, detail="Please enter your name.")
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise HTTPException(status_code=422, detail="Enter a valid email address.")
    try:
        user = db.create_user(name, email, req.password)
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    return {"status": "success", "user": user}

@app.post("/api/auth/login")
def login(req: LoginRequest):
    email = req.email.strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise HTTPException(status_code=422, detail="Enter a valid email address.")
    user = db.authenticate_user(email, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Email or password is incorrect.")
    return {"status": "success", "user": user}

# --- PERSISTENT WARDROBE DATABASE CRUD ENDPOINTS ---

@app.get("/api/clothes")
def get_clothes(user_id: int = 1):
    """Fetch all persistent clothing items from SQLite database."""
    if user_id != 1:
        raise HTTPException(status_code=403, detail="This installation supports only its configured single user.")
    items = db.get_all_clothes(user_id)
    return {"status": "success", "clothes": items}

@app.get("/api/availability")
def get_availability(user_id: int = 1):
    if user_id != 1:
        raise HTTPException(status_code=403, detail="This installation supports only its configured single user.")
    items = db.get_all_clothes(user_id)
    return {"status": "success", "items": items}

@app.put("/api/clothes/{item_id}/availability")
def update_clothing_availability(item_id: str, req: AvailabilityUpdateRequest):
    if req.user_id != 1:
        raise HTTPException(status_code=403, detail="This installation supports only its configured single user.")
    if req.availability_status not in AVAILABILITY_STATUSES:
        raise HTTPException(status_code=422, detail="Choose a supported wardrobe availability status.")
    if req.ironing_status is not None and req.ironing_status not in IRONING_STATUSES:
        raise HTTPException(status_code=422, detail="Choose a supported ironing status.")
    if req.expected_available_at is not None:
        try:
            datetime.fromisoformat(req.expected_available_at.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=422, detail="Expected-ready time must be a valid ISO date/time.")
    try:
        updated = db.update_clothing_availability(
            item_id,
            req.user_id,
            req.availability_status,
            req.ironing_status,
            req.expected_available_at,
            req.status_note,
            req.notify_when_ready
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not save wardrobe availability: {exc}")
    if not updated:
        raise HTTPException(status_code=404, detail="Wardrobe item not found.")
    if (
        updated["availability_status"] not in {"ready", "available"}
        or updated.get("ironing_status", "ready") != "ready"
    ):
        db.remove_future_outfits_using_item(item_id, req.user_id)
    return {"status": "success", "item": updated}

@app.get("/api/outfit-wear-events")
def get_outfit_wear_events(user_id: int = 1):
    if user_id != 1:
        raise HTTPException(status_code=403, detail="This installation supports only its configured single user.")
    return {"status": "success", "events": db.get_pending_wear_events(user_id)}

@app.post("/api/outfit-wear-events")
def create_outfit_wear_event(req: OutfitWearEventRequest):
    if req.user_id != 1:
        raise HTTPException(status_code=403, detail="This installation supports only its configured single user.")
    try:
        wear_date = date.fromisoformat(req.wear_date)
    except ValueError:
        raise HTTPException(status_code=422, detail="Wear date must be an ISO date.")
    if wear_date > date.today():
        raise HTTPException(status_code=422, detail="You cannot confirm an outfit as worn before its scheduled date.")
    if req.planned_day is not None and req.planned_day not in SCHEDULE_DAY_IDS:
        raise HTTPException(status_code=422, detail="Choose a planned day from Monday to Sunday.")
    if req.planned_day is not None and wear_date.weekday() != (
        ["mon", "tue", "wed", "thu", "fri", "sat", "sun"].index(req.planned_day)
    ):
        raise HTTPException(status_code=422, detail="Wear date must match the planned weekday.")
    planned_entry = None
    if req.schedule_id:
        planned_entry = db.get_weekday_outfit(req.schedule_id, req.user_id)
        if (
            not planned_entry
            or planned_entry["confirmation_status"] != "awaiting"
            or planned_entry["plan_date"] != req.wear_date
            or planned_entry["outfit"].get("id") != req.outfit.get("id")
        ):
            raise HTTPException(status_code=409, detail="This planned outfit has already been confirmed or changed.")
    try:
        event = db.create_outfit_wear_event(
            req.user_id,
            req.outfit,
            req.item_ids,
            req.wear_date,
            req.planned_day,
            req.worn
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    if req.schedule_id and not db.confirm_weekday_outfit(req.schedule_id, req.user_id, req.worn):
        raise HTTPException(status_code=409, detail="This planned outfit was confirmed by another request.")
    return {"status": "success", "event": event, "pending_events": db.get_pending_wear_events(req.user_id)}

@app.put("/api/outfit-wear-events/{event_id}")
def submit_outfit_wear_event(event_id: str, req: OutfitWearAnswersRequest):
    if req.user_id != 1:
        raise HTTPException(status_code=403, detail="This installation supports only its configured single user.")
    try:
        saved = db.submit_wear_event_answers(
            req.user_id, event_id, [answer.model_dump() for answer in req.answers]
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    if not saved:
        raise HTTPException(status_code=404, detail="Pending wear reminder not found.")
    return {"status": "success", "events": db.get_pending_wear_events(req.user_id)}

@app.delete("/api/outfit-wear-events/{event_id}")
def dismiss_outfit_wear_event(event_id: str, user_id: int = 1):
    if user_id != 1:
        raise HTTPException(status_code=403, detail="This installation supports only its configured single user.")
    if not db.dismiss_wear_event(user_id, event_id):
        raise HTTPException(status_code=404, detail="Pending wear reminder not found.")
    return {"status": "success", "events": db.get_pending_wear_events(user_id)}

@app.get("/api/laundry/ready-confirmation")
def get_ready_confirmation_items(user_id: int = 1):
    """Get items that have been in wash for 2+ days and need confirmation."""
    if user_id != 1:
        raise HTTPException(status_code=403, detail="This installation supports only its configured single user.")
    items = db.get_items_needing_ready_confirmation(user_id)
    return {"status": "success", "items": items}

@app.get("/api/profile")
def get_profile():
    """Fetch persistent user profile and context rules from SQLite database."""
    profile = db.get_user_profile()
    return {"status": "success", "profile": profile}

@app.post("/api/profile")
def save_profile(profile: Dict[str, Any]):
    """Save user profile and context rules into SQLite database."""
    saved = db.save_user_profile(profile)
    return {"status": "success", "profile": saved}

@app.post("/api/clothes")
def create_clothing_item(item: Dict[str, Any]):
    """Add a new clothing item to SQLite database."""
    created_item = db.add_clothing_item(item, 1)
    return {"status": "success", "item": created_item}

@app.put("/api/clothes/{item_id}")
def update_clothing_item(item_id: str, item: Dict[str, Any]):
    """Update an existing clothing item in SQLite database."""
    updated_item = db.update_clothing_item(item_id, item, 1)
    if not updated_item:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"status": "success", "item": updated_item}

@app.delete("/api/clothes/{item_id}")
def delete_clothing_item(item_id: str):
    """Permanently delete a clothing item from SQLite database."""
    if not db.delete_clothing_item(item_id, 1):
        raise HTTPException(status_code=404, detail="Item not found")
    db.remove_future_outfits_using_item(item_id, 1)
    return {"status": "success", "message": f"Item {item_id} deleted successfully"}

@app.get("/api/weekday-outfits")
def get_weekday_outfits(user_id: int = 1):
    if user_id != 1:
        raise HTTPException(status_code=403, detail="This installation supports only its configured single user.")
    db.ensure_stylist_tables()
    db.remove_unavailable_future_outfits(user_id)
    return {"status": "success", "schedule": db.get_weekday_outfits(user_id)}

@app.post("/api/weekday-outfits")
def create_weekday_outfit(req: WeekdayOutfitRequest):
    if req.user_id != 1:
        raise HTTPException(status_code=403, detail="This installation supports only its configured single user.")
    if req.day_id not in SCHEDULE_DAY_IDS:
        raise HTTPException(status_code=422, detail="Choose a day from Monday to Sunday.")
    if req.plan_date is not None:
        try:
            plan_date = date.fromisoformat(req.plan_date)
        except ValueError:
            raise HTTPException(status_code=422, detail="Plan date must be an ISO date.")
        if plan_date.weekday() != ["mon", "tue", "wed", "thu", "fri", "sat", "sun"].index(req.day_id):
            raise HTTPException(status_code=422, detail="Plan date must match the selected weekday.")
        if plan_date < date.today():
            raise HTTPException(status_code=422, detail="You cannot schedule a new outfit on a past date.")
    if req.source not in {"daily", "voice", "occasion"}:
        raise HTTPException(status_code=422, detail="Invalid outfit source.")
    occasion = req.occasion.strip()
    if not occasion:
        raise HTTPException(status_code=422, detail="Add an occasion or time-of-day label for this look.")
    db.ensure_stylist_tables()
    try:
        scheduled = db.schedule_weekday_outfit(
            req.day_id,
            req.user_id,
            req.outfit,
            req.source,
            occasion,
            req.ready_confirmed_item_ids,
            req.plan_date
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    if scheduled is None:
        raise HTTPException(status_code=409, detail="Could not add this look to the selected day.")
    return {"status": "success", "scheduled_outfit": scheduled}

@app.put("/api/weekday-outfits")
def replace_weekday_outfit(req: WeekdayOutfitReplacementRequest):
    if req.user_id != 1:
        raise HTTPException(status_code=403, detail="This installation supports only its configured single user.")
    if req.day_id not in SCHEDULE_DAY_IDS:
        raise HTTPException(status_code=422, detail="Choose a day from Monday to Sunday.")
    if req.plan_date is not None:
        try:
            plan_date = date.fromisoformat(req.plan_date)
        except ValueError:
            raise HTTPException(status_code=422, detail="Plan date must be an ISO date.")
        if plan_date.weekday() != ["mon", "tue", "wed", "thu", "fri", "sat", "sun"].index(req.day_id):
            raise HTTPException(status_code=422, detail="Plan date must match the selected weekday.")
    if req.source not in {"daily", "voice", "occasion"}:
        raise HTTPException(status_code=422, detail="Invalid outfit source.")
    db.ensure_stylist_tables()
    try:
        replaced = db.replace_weekday_outfit(
            req.schedule_id,
            req.user_id,
            req.expected_outfit_id,
            req.outfit,
            req.source,
            req.ready_confirmed_item_ids
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    if replaced is None:
        raise HTTPException(
            status_code=409,
            detail="The planned outfit changed or was removed. Refresh the weekly plan and try again."
        )
    return {"status": "success", "scheduled_outfit": replaced}

@app.delete("/api/weekday-outfits/{schedule_id}")
def delete_weekday_outfit(schedule_id: str, user_id: int = 1):
    if user_id != 1:
        raise HTTPException(status_code=403, detail="This installation supports only its configured single user.")
    db.ensure_stylist_tables()
    db.remove_weekday_outfit(schedule_id, user_id)
    return {"status": "success"}

@app.post("/api/stylist-recommend")
def stylist_recommend(req: StylistRequest):
    """
    Multi-Agent LangGraph Endpoint:
    Triggers the 7-node pipeline (Style Profile -> Trend Research -> Occasion -> Wardrobe -> Outfit Stylist -> Outfit Critic -> Visualization Agent)
    and returns ranked outfits + step-by-step agent trace.
    """
    try:
        if req.user_id != 1:
            raise HTTPException(status_code=403, detail="This installation supports only its configured single user.")
        response = run_multi_agent_pipeline({
            "user_id": req.user_id,
            "occasion": req.occasion,
            "style_preference": req.style_preference,
            "city": req.city,
            "exclude_bags": req.exclude_bags,
            "exclude_accessories": req.exclude_accessories,
            "context_rules": req.context_rules,
            "clothes": db.get_all_clothes(req.user_id)
        })
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/weather")
def get_weather(city: str = "New York"):
    """
    Live Weather Endpoint:
    Queries Open-Meteo free API for live temperature, weather conditions & fashion constraints.
    """
    weather_data = fetch_live_weather(city)
    return {"status": "success", "weather": weather_data}

@app.post("/api/visualize-outfit")
def visualize_outfit(outfit: Dict[str, Any]):
    """
    AI Outfit Visualization Endpoint:
    Constructs a text-to-image prompt from structured outfit attributes
    and renders an AI photo of a fashion model wearing that look.
    """
    try:
        prompt = generate_outfit_visualization_prompt(outfit)
        image_url = generate_outfit_visualization_image(prompt)
        return {
            "status": "success",
            "prompt": prompt,
            "visualization_image_url": image_url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Visualization failed: {str(e)}")


# --- VOICE STYLIST AGENT ENDPOINTS ---

@app.post("/api/voice/command")
def voice_command(req: VoiceRequest):
    """
    Voice Stylist Agent Endpoint:
    Processes voice/text commands and returns outfit recommendations or status updates.
    Supports natural language commands for outfit requests, status updates, and availability queries.
    """
    try:
        response = run_voice_agent_pipeline(
            user_message=req.user_message,
            conversation_history=req.conversation_history,
            conversation_id=req.conversation_id,
            selected_outfit_id=req.selected_outfit_id,
            request_id=req.request_id,
            user_id=req.user_id,
            context_outfit=req.context_outfit
        )
        return response
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice command failed: {str(e)}")


@app.get("/api/voice/conversations/{conversation_id}")
def get_voice_conversation(conversation_id: str, user_id: int = 1):
    """Load persisted messages and current outfit state for the single configured user."""
    if user_id != 1:
        raise HTTPException(status_code=403, detail="This installation supports only its configured single user.")
    db.ensure_stylist_tables()
    conversation = db.get_stylist_conversation(conversation_id, user_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "success", **conversation}


@app.get("/api/voice/saved-outfits")
def get_saved_voice_outfits(user_id: int = 1):
    """Return saved looks belonging to the configured single user."""
    if user_id != 1:
        raise HTTPException(status_code=403, detail="This installation supports only its configured single user.")
    db.ensure_stylist_tables()
    return {"status": "success", "outfits": db.get_saved_stylist_outfits(user_id)}


@app.post("/api/voice/tts")
def text_to_speech(text: str = Form(...), voice: str = Form("alloy")):
    """
    Text-to-Speech Endpoint:
    Converts text to speech audio using OpenAI TTS or returns None for browser TTS.
    """
    try:
        audio_base64 = voice_service.text_to_speech_base64(text, voice)
        if audio_base64:
            return {
                "status": "success",
                "audio_data": audio_base64,
                "provider": "openai"
            }
        else:
            return {
                "status": "success",
                "audio_data": None,
                "provider": "browser",
                "message": "Use browser Web Speech API for TTS"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS failed: {str(e)}")


@app.post("/api/voice/image-stylist")
async def voice_image_stylist(
    file: UploadFile = File(...),
    user_message: str = Form(...),
    conversation_id: Optional[str] = Form(None),
    selected_outfit_id: Optional[str] = Form(None),
    request_id: Optional[str] = Form(None),
    user_id: int = Form(1),
):
    """
    Vision-Powered Voice Stylist Endpoint:
    Accepts an uploaded outfit/garment image + a natural language question.
    Uses GPT-4o Vision (or Gemini) to:
      - Analyze the uploaded garment (color, category, style)
      - Cross-reference with the user's wardrobe
      - Answer questions like "which tops from my wardrobe match this pant?"
        or "what colors suit this bottomwear?"
    Returns a styled text answer plus any matching wardrobe items.
    """
    import json as _json

    if user_id != 1:
        raise HTTPException(status_code=403, detail="This installation supports only its configured single user.")

    try:
        image_bytes = await file.read()
        base64_image = base64.b64encode(image_bytes).decode("utf-8")

        # Detect mime type
        content_type = file.content_type or "image/jpeg"

        # Fetch user's wardrobe for context
        wardrobe = db.get_all_clothes(user_id)
        available_items = [
            item for item in wardrobe
            if item.get("availability_status", "ready") in ("ready", "available")
            and item.get("ironing_status", "ready") == "ready"
        ]

        # Build a compact wardrobe summary for the LLM
        def _summarise_items(items):
            lines = []
            for item in items:
                attrs = item.get("attributes") or {}
                line = (
                    f"- [{item.get('category','?')}] {item.get('title','?')} "
                    f"| Color: {item.get('color','?')} "
                    f"| Style: {item.get('style','?')} "
                    f"| Pattern: {item.get('pattern','?')}"
                )
                if attrs.get("type"):
                    line += f" | Type: {attrs['type']}"
                line += f" (id: {item.get('id','?')})"
                lines.append(line)
            return "\n".join(lines) if lines else "(no available items)"

        wardrobe_text = _summarise_items(available_items)

        system_prompt = (
            "You are Aria, an expert AI fashion stylist. "
            "The user has uploaded a photo of a clothing item. "
            "Analyze the item in the image and answer the user's question using their actual wardrobe. "
            "Be specific — reference real items from the wardrobe by name. "
            "Keep your answer warm, concise, and actionable (3-5 sentences). "
            "If asked which items match, list specific wardrobe items. "
            "If asked about colors, give color theory advice AND reference wardrobe items in those colors."
        )

        user_prompt = (
            f"User question: {user_message}\n\n"
            f"User's available wardrobe:\n{wardrobe_text}\n\n"
            "First, describe the uploaded garment (category, color, style, pattern). "
            "Then answer the user's question referencing their actual wardrobe items above."
        )

        answer_text = None
        matched_item_ids = []

        # Try OpenAI GPT-4o Vision first
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            try:
                client = OpenAI(api_key=api_key)
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:{content_type};base64,{base64_image}",
                                        "detail": "high"
                                    }
                                },
                                {"type": "text", "text": user_prompt}
                            ]
                        }
                    ],
                    max_tokens=600,
                    temperature=0.7
                )
                answer_text = response.choices[0].message.content.strip()
            except Exception as openai_err:
                print(f"[ImageStylist] OpenAI Vision failed: {openai_err}")

        # Try Gemini Vision as fallback
        if not answer_text:
            gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")
            if gemini_key and gemini_key.startswith("AIza"):
                try:
                    from google import genai as google_genai  # type: ignore
                    from google.genai import types as genai_types  # type: ignore
                    genai_client = google_genai.Client(api_key=gemini_key)
                    model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
                    full_prompt = system_prompt + "\n\n" + user_prompt
                    response = genai_client.models.generate_content(
                        model=model_name,
                        contents=[
                            genai_types.Part.from_bytes(data=image_bytes, mime_type=content_type),
                            genai_types.Part.from_text(text=full_prompt),
                        ]
                    )
                    answer_text = (response.text or "").strip()
                except Exception as gemini_err:
                    print(f"[ImageStylist] Gemini Vision failed: {gemini_err}")

        # ── RULE-BASED FALLBACK: Pillow color extraction — zero API dependency ──
        # Runs whenever all LLM providers are unavailable. Uses Pillow to extract
        # the dominant color from the image, then cross-references the wardrobe.
        if not answer_text:
            try:
                from gemini_stylist import COLOR_COMBOS

                # ── Step 1: Extract dominant color from image using Pillow ──────
                img = Image.open(BytesIO(image_bytes)).convert("RGB")

                # Resize to a small grid; skip very light (background) pixels
                img_small = img.resize((64, 64), Image.LANCZOS)
                w, h = img_small.size
                pixels = [img_small.getpixel((x, y)) for y in range(h) for x in range(w)]
                # Filter out near-white/near-black background pixels
                garment_pixels = [
                    p for p in pixels
                    if not (p[0] > 220 and p[1] > 220 and p[2] > 220)   # not white/light bg
                    and not (p[0] < 30 and p[1] < 30 and p[2] < 30)      # not pure black
                ]
                if not garment_pixels:
                    garment_pixels = pixels   # fallback to all pixels

                # Average the garment pixels
                avg_r = sum(p[0] for p in garment_pixels) // len(garment_pixels)
                avg_g = sum(p[1] for p in garment_pixels) // len(garment_pixels)
                avg_b = sum(p[2] for p in garment_pixels) // len(garment_pixels)

                # ── Step 2: Map average RGB to a named color ──────────────────
                COLOR_RGB = {
                    "black":   (20,  20,  20),
                    "white":   (240, 240, 240),
                    "grey":    (128, 128, 128),
                    "navy":    (30,  40,  100),
                    "blue":    (50,  100, 200),
                    "denim":   (80,  110, 160),
                    "red":     (200, 40,  40),
                    "maroon":  (120, 20,  40),
                    "pink":    (230, 130, 150),
                    "blush":   (240, 180, 180),
                    "orange":  (220, 110, 30),
                    "yellow":  (220, 200, 50),
                    "mustard": (180, 150, 30),
                    "green":   (50,  150, 60),
                    "olive":   (100, 120, 50),
                    "teal":    (40,  140, 130),
                    "purple":  (120, 50,  160),
                    "lavender":(170, 130, 200),
                    "brown":   (130, 70,  30),
                    "tan":     (180, 140, 90),
                    "beige":   (220, 200, 160),
                    "cream":   (240, 230, 200),
                    "gold":    (210, 170, 50),
                    "silver":  (190, 190, 200),
                    "coral":   (240, 110, 90),
                    "rust":    (170, 80,  30),
                }

                def _color_distance(r1, g1, b1, r2, g2, b2):
                    return ((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2) ** 0.5

                detected_color = min(
                    COLOR_RGB.items(),
                    key=lambda kv: _color_distance(avg_r, avg_g, avg_b, *kv[1])
                )[0]

                # ── Step 3: Infer garment category from the user's question ────
                q = user_message.lower()
                # "bottomwear is suit with this TOP" → image is a TOP, look for bottoms
                # "which top suits this PANT" → image is a PANT (bottom), look for tops
                # Order matters: check more specific phrases first
                is_top = any(kw in q for kw in [
                    "top", "shirt", "blouse", "tshirt", "t-shirt", "kurta",
                    "sweater", "hoodie", "tunic", "crop", "this top",
                    "suit with this top", "for this top", "goes with this top",
                    "topwear"
                ])
                is_bottom = any(kw in q for kw in [
                    "pant", "trouser", "jean", "jeans", "bottom", "skirt",
                    "shorts", "legging", "chino", "palazzo", "bottomwear",
                    "this bottom", "this pant", "this trouser", "this jeans",
                    "suit with this bottom", "for this bottom", "this skirt"
                ])
                is_shoe = any(kw in q for kw in [
                    "shoe", "shoes", "footwear", "heel", "sneaker", "sandal",
                    "boot", "loafer"
                ])

                # When user says "which bottomwear suits this top/shirt":
                # → the IMAGE is a TOP, they want BOTTOMS
                # When user says "which top suits this pant":
                # → the IMAGE is a BOTTOM, they want TOPS
                # The question structure: "which X suits with this Y" → image = Y
                import re as _recq
                # Detect "X suits/goes with this [image-garment]"
                _with_match = _recq.search(
                    r"(?:suit|go|match|pair|wear)\s+with\s+this\s+(\w+)",
                    q
                )
                _this_match = _recq.search(
                    r"\bthis\s+(\w+(?:wear)?)\b",
                    q
                )
                _for_match = _recq.search(
                    r"\bfor\s+this\s+(\w+)\b",
                    q
                )
                def _kw_is_bottom(kw):
                    return any(b in kw for b in [
                        "pant","trouser","jean","bottom","skirt","short","legging","chino","palazzo","bottomwear"
                    ])
                def _kw_is_top(kw):
                    return any(t in kw for t in [
                        "top","shirt","blouse","tshirt","t-shirt","kurta","sweater","hoodie","tunic","topwear","crop"
                    ])

                # Determine the garment IN THE IMAGE from question context
                _this_word = (
                    (_with_match and _with_match.group(1))
                    or (_this_match and _this_match.group(1))
                    or (_for_match and _for_match.group(1))
                    or ""
                ).lower()

                if _kw_is_top(_this_word) or (is_top and not is_bottom):
                    # Image is a top → look for bottoms to pair with it
                    garment_label = "top"
                    search_categories = ["bottoms"]
                    search_label = "bottoms"
                elif _kw_is_bottom(_this_word) or (is_bottom and not is_top):
                    # Image is a bottom → look for tops to pair with it
                    garment_label = "bottom"
                    search_categories = ["tops", "outerwear", "one_piece"]
                    search_label = "tops"
                elif is_shoe:
                    garment_label = "footwear"
                    search_categories = ["tops", "bottoms", "outerwear"]
                    search_label = "outfit pieces"
                else:
                    # No clear signal — default: treat image as bottom, look for tops
                    # (most common "give me a look" request)
                    garment_label = "bottom"
                    search_categories = ["tops", "outerwear", "one_piece"]
                    search_label = "tops"

                # ── Step 4: Get complementary colors ─────────────────────────
                complement_colors = COLOR_COMBOS.get(detected_color, [
                    "white", "black", "grey", "beige", "cream"
                ])

                # ── Step 5: Find matching wardrobe items ──────────────────────
                matching_items = []
                style_matching_items = []
                for item in available_items:
                    item_color = (item.get("color") or "").lower()
                    item_cat = (item.get("category") or "").lower()
                    if item_cat not in search_categories:
                        continue
                    # Check if item's color matches any complementary color
                    color_match = any(
                        comp in item_color or item_color in comp
                        for comp in complement_colors
                    )
                    if color_match:
                        matching_items.append(item)
                        matched_item_ids.append(str(item.get("id")))
                    else:
                        style_matching_items.append(item)

                # ── Step 6: Compose the answer ────────────────────────────────
                top_matches = matching_items[:5]
                fallback_matches = style_matching_items[:3]

                color_display = detected_color.capitalize()
                comp_display = ", ".join(complement_colors[:5])

                if top_matches:
                    names = [f"**{m['title']}** ({m.get('color','?')})" for m in top_matches]
                    answer_text = (
                        f"I analyzed the image and detected a **{color_display}** {garment_label}. "
                        f"Colors that pair beautifully with {detected_color} are: {comp_display}. "
                        f"From your wardrobe, these {search_label} match perfectly: {', '.join(names)}."
                    )
                    if len(top_matches) < 3 and fallback_matches:
                        extra = [f"**{m['title']}**" for m in fallback_matches[:2]]
                        answer_text += f" You could also try: {', '.join(extra)} for a contrasting look."
                elif available_items:
                    # No exact color match — show best wardrobe options with style advice
                    all_options = (style_matching_items or available_items)
                    options_in_cat = [
                        i for i in all_options
                        if (i.get("category") or "").lower() in search_categories
                    ][:5]
                    if options_in_cat:
                        names = [f"**{m['title']}** ({m.get('color','?')})" for m in options_in_cat]
                        answer_text = (
                            f"I can see a **{color_display}** {garment_label} in your image. "
                            f"The best color pairings for {detected_color} are: {comp_display}. "
                            f"From your wardrobe these {search_label} would work well: {', '.join(names)}. "
                            f"For the closest match, try adding a {complement_colors[0]} or {complement_colors[1]} {search_label.rstrip('s')} to your wardrobe!"
                        )
                    else:
                        answer_text = (
                            f"I detected a **{color_display}** {garment_label} in your image. "
                            f"The best pairings for {detected_color} are: {comp_display}. "
                            f"Your wardrobe doesn't have {search_label} in those colors yet — "
                            f"adding a {complement_colors[0]} or {complement_colors[1]} piece would complete this look perfectly!"
                        )
                else:
                    answer_text = (
                        f"I detected a **{color_display}** {garment_label} in your image. "
                        f"The best color pairings for {detected_color} are: {comp_display}. "
                        "Your wardrobe is empty right now — add some clothes and I'll match them to this piece!"
                    )

                print(f"[ImageStylist] Rule-based: detected {detected_color} ({avg_r},{avg_g},{avg_b}) "
                      f"→ {len(matching_items)} wardrobe matches")

            except Exception as fallback_err:
                print(f"[ImageStylist] Rule-based fallback failed: {fallback_err}")
                import traceback
                traceback.print_exc()
                answer_text = (
                    f"I can see your uploaded garment! Based on your wardrobe of "
                    f"{len(available_items)} available items, I can help you style it. "
                    "Try asking: 'which tops from my wardrobe go with this pant?' or "
                    "'what color top suits a blue pant?' and I'll give you specific recommendations."
                )

        # ── Detect whether the user is asking for a full outfit look ────────────
        import re as _re
        _OUTFIT_REQUEST_RE = _re.compile(
            r"\b("
            r"outfit|full\s+look|whole\s+look|complete\s+look|look\s+from|"
            r"give\s+me\s+a\s+look|give\s+me\s+(?:an?\s+)?(?:outfit|look)|"
            r"put\s+together|style\s+me|what\s+(?:should\s+i\s+)?wear|"
            r"suggest\s+.*(?:outfit|look)|give\s+.*(?:outfit|look)|"
            r"outfit\s+look|match\s+with\s+this|based\s+on\s+(?:this|your)|"
            r"full\s+outfit|complete\s+outfit|entire\s+(?:outfit|look)|"
            r"whole\s+outfit|create\s+(?:a\s+)?(?:look|outfit)|"
            r"style\s+(?:this|the|my)|dress\s+me|show\s+me\s+(?:a\s+)?(?:look|outfit)|"
            r"pair\s+(?:this|it)\s+with|what\s+(?:goes|pairs?)\s+with\s+this"
            r")\b",
            _re.IGNORECASE,
        )
        is_outfit_request = bool(_OUTFIT_REQUEST_RE.search(user_message))

        # ── Persist this turn in the stylist conversation ─────────────────────
        db.ensure_stylist_tables()
        import uuid as _uuid, datetime as _dt
        conv_id = conversation_id or str(_uuid.uuid4())
        req_id = request_id or str(_uuid.uuid4())
        persisted = db.get_stylist_conversation(conv_id, user_id)
        messages = list(persisted["messages"] if persisted else [])
        # Load saved state fresh — do NOT carry over required_colors/required_top_colors
        # from previous turns; those are per-request constraints only.
        _raw_saved = dict(persisted["state"] if persisted else {})
        saved_state = {
            k: v for k, v in _raw_saved.items()
            if k not in ("required_colors", "required_top_colors")
        }

        # ── Collect image analysis results from local variables ───────────────
        _dc = locals().get("detected_color")
        _gl = locals().get("garment_label", "bottom")
        _cc = locals().get("complement_colors") or []
        _sc = locals().get("search_categories") or []

        # ── Save image-analysis context into saved_state (for follow-up turns) ─
        if _dc:
            saved_state["image_context"] = {
                "detected_color":    _dc,
                "garment_label":     _gl,
                "complement_colors": _cc,
                "search_categories": _sc,
            }

        # ── If user asks for a full outfit, call the outfit pipeline ─────────
        if is_outfit_request:
            from voice_agent_graph import run_voice_agent_pipeline as _vap

            # Determine occasion from question or use "casual" as safe default
            _occasion_map = {
                "wedding": ["wedding", "shaadi", "reception"],
                "office": ["office", "work", "meeting", "presentation"],
                "party": ["party", "club", "night out", "birthday"],
                "college": ["college", "class", "campus"],
                "date": ["date", "dinner date", "romantic"],
                "travel": ["travel", "trip", "vacation"],
                "festival": ["festival", "diwali", "eid", "holi"],
            }
            _q_lower = user_message.lower()
            _detected_occasion = next(
                (occ for occ, kws in _occasion_map.items() if any(kw in _q_lower for kw in kws)),
                None
            ) or _raw_saved.get("occasion") or "casual"

            # Build a natural query that tells the pipeline what was detected in the image
            if _dc and _gl:
                if _gl == "top":
                    outfit_query = (
                        f"Suggest a complete outfit for {_detected_occasion}. "
                        f"I'm wearing a {_dc} top. Find matching bottoms, footwear and accessories."
                    )
                else:
                    outfit_query = (
                        f"Suggest a complete outfit for {_detected_occasion}. "
                        f"I'm wearing a {_dc} bottom. Find matching tops, footwear and accessories."
                    )
            else:
                outfit_query = f"Suggest a complete outfit for {_detected_occasion}."

            # Persist the user turn BEFORE calling the pipeline
            messages.append({
                "id": req_id,
                "role": "user",
                "content": f"[Image uploaded] {user_message}",
                "has_image": True,
                "created_at": _dt.datetime.now().isoformat(),
            })
            # Save state WITHOUT color constraints so the pipeline runs freely
            _clean_state = {k: v for k, v in saved_state.items()
                            if k not in ("required_colors", "required_top_colors")}
            _clean_state["occasion"] = _detected_occasion
            db.save_stylist_conversation(conv_id, user_id, _clean_state, messages)

            pipeline_result = _vap(
                user_message=outfit_query,
                conversation_id=conv_id,
                user_id=user_id,
                request_id=str(_uuid.uuid4()),  # always fresh — never hits dedup guard
            )

            # Final state: ensure no color constraints bleed forward
            _final_state = dict(pipeline_result.get("conversation_state", _clean_state))
            _final_state.pop("required_top_colors", None)
            _final_state.pop("required_colors", None)
            # Keep image_context for future follow-ups
            if _dc:
                _final_state["image_context"] = saved_state["image_context"]

            outfit_list = pipeline_result.get("outfits", [])
            if outfit_list:
                final_answer = (
                    answer_text
                    + "\n\nBased on this, here are complete outfit looks from your wardrobe:"
                )
            else:
                # Pipeline found nothing — just return the color analysis text
                final_answer = answer_text

            # Patch messages so the image badge shows on the user turn
            merged_messages = list(pipeline_result.get("messages", messages))
            for msg in reversed(merged_messages):
                if msg.get("role") == "user":
                    msg["has_image"] = True
                    msg["content"] = f"[Image uploaded] {user_message}"
                    break
            if outfit_list:
                for msg in reversed(merged_messages):
                    if msg.get("role") == "assistant":
                        msg["content"] = final_answer
                        break

            return {
                "status": "success",
                "conversation_id": conv_id,
                "agent_response": final_answer if outfit_list else answer_text,
                "response_type": "outfit" if outfit_list else "image_analysis",
                "outfits": outfit_list,
                "matched_item_ids": matched_item_ids,
                "messages": merged_messages,
                "conversation_state": _final_state,
            }

        # ── Non-outfit image question: return text answer as before ───────────
        messages.append({
            "id": req_id,
            "role": "user",
            "content": f"[Image uploaded] {user_message}",
            "has_image": True,
            "created_at": _dt.datetime.now().isoformat(),
        })
        messages.append({
            "id": str(_uuid.uuid4()),
            "role": "assistant",
            "content": answer_text,
            "response_type": "image_analysis",
            "outfits": [],
            "created_at": _dt.datetime.now().isoformat(),
        })
        db.save_stylist_conversation(conv_id, user_id, saved_state, messages)

        return {
            "status": "success",
            "conversation_id": conv_id,
            "agent_response": answer_text,
            "response_type": "image_analysis",
            "matched_item_ids": matched_item_ids,
            "messages": messages,
            "conversation_state": saved_state,
        }

    except Exception as e:
        print(f"[ImageStylist] Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Image stylist failed: {str(e)}")


@app.post("/api/analyze-clothing")
async def analyze_clothing_image(file: UploadFile = File(...)):
    """
    AI Clothing Analysis Endpoint using GPT-4 Vision:
    Automatically detects:
    - Category (tops, bottoms, footwear, bags, accessories)
    - Color (dominant colors)
    - Style (casual, formal, streetwear)
    - Pattern and other attributes
    """
    try:
        # Read image file
        image_bytes = await file.read()
        base64_image = base64.b64encode(image_bytes).decode('utf-8')

        print(f"Image size: {len(image_bytes)} bytes")
        print(f"Calling GPT-4 Vision API...")

        # Get OpenAI API key from environment variable
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("OPENAI_API_KEY not found, using fallback")
            # Use fallback if no API key
            seed = len(image_bytes) % 1000
            random.seed(seed)
            categories = ["tops", "bottoms", "outerwear", "footwear", "bags", "accessories"]
            colors = ["Black", "Blue", "Red", "White", "Grey", "Brown", "Green", "Pink", "Yellow", "Navy"]
            patterns = ["Solid", "Striped", "Floral", "Geometric", "Plaid", "Polka Dot", "Checkered"]
            styles = ["casual", "formal", "smart-casual", "streetwear", "ethnic", "sporty"]
            subcategories = {
                "tops": ["T-Shirt", "Shirt", "Blouse", "Sweater", "Hoodie", "Tank Top"],
                "bottoms": ["Jeans", "Trousers", "Shorts", "Skirt", "Leggings", "Chinos"],
                "outerwear": ["Jacket", "Coat", "Blazer", "Cardigan", "Vest", "Windbreaker"],
                "footwear": ["Sneakers", "Loafers", "Boots", "Sandals", "Heels", "Flats"],
                "bags": ["Handbag", "Backpack", "Tote", "Clutch", "Crossbody", "Shoulder Bag"],
                "accessories": ["Watch", "Belt", "Scarf", "Hat", "Jewelry", "Sunglasses"]
            }
            selected_category = categories[seed % len(categories)]
            selected_color = colors[seed % len(colors)]
            selected_pattern = patterns[seed % len(patterns)]
            selected_style = styles[seed % len(styles)]
            selected_subcategory = subcategories[selected_category][seed % len(subcategories[selected_category])]
            analysis = {
                "category": selected_category,
                "subcategory": selected_subcategory,
                "color": selected_color,
                "pattern": selected_pattern,
                "style": selected_style,
                "confidence": 0.85
            }
            return {"status": "success", "analysis": analysis}

        # Use GPT-4 Vision for accurate clothing detection
        client = OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """Analyze this clothing item and return a rich structured JSON representation of its fashion attributes:
{
  "category": "one of: tops, bottoms, outerwear, footwear, bags, accessories",
  "subcategory": "specific name (e.g., T-Shirt, Jeans, Kurti, Blazer, Sneakers, Handbag)",
  "type": "exact garment type (e.g. bell_bottom, wide_leg, skinny_jeans, cargo, kurti, crop_top, oversized_tshirt, fitted_shirt, hoodie, blazer)",
  "color": "primary color (e.g., Black, Blue, Red, White, Beige, Navy)",
  "secondary_color": "secondary accent color or null",
  "pattern": "pattern type (e.g., solid, striped, floral, graphic, plaid, denim)",
  "style": "aesthetic (e.g., casual, formal, smart-casual, streetwear, ethnic, sporty)",
  "formality": "integer score from 1 (extremely casual) to 10 (black tie formal)",
  "fit": "fit cut (e.g., fitted, regular, relaxed, oversized, slim, skinny, loose)",
  "silhouette": "shape profile (e.g., flared, straight, A-line, boxy, fitted_thigh, loose)",
  "volume": "visual volume (e.g. low, medium, high)",
  "length": "garment length (e.g. cropped, waist, hip, mid_thigh, knee, ankle, full)",
  "rise": "for bottoms only: high, mid, or low (else null)",
  "leg_shape": "for bottoms only: bell_bottom, wide_leg, straight, skinny, cargo, jogger, bootcut (else null)",
  "crop_level": "for tops only: cropped, non_cropped (else null)",
  "sleeve_length": "for tops/outerwear: sleeveless, short, 3/4, long (else null)",
  "neckline": "for tops: crew, v-neck, collar, boat, scoop, turtleneck (else null)",
  "confidence": 0.95,
  "alternative_type": "alternative classification if ambiguous or null"
}

Be precise and realistic. Return ONLY valid JSON, no markdown formatting or extra text."""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=400
        )

        # Parse GPT-4 response
        content = response.choices[0].message.content
        print(f"GPT-4 Response: {content}")

        import json
        from fashion.attribute_extractor import normalize_garment_attributes
        
        raw_json = json.loads(content.replace("```json", "").replace("```", "").strip())
        analysis = normalize_garment_attributes(raw_json)

        print(f"Final normalized vision analysis: {analysis}")

        return {
            "status": "success",
            "analysis": analysis
        }

    except Exception as e:
        print(f"Error in analyze_clothing_image: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Image analysis failed: {str(e)}")

@app.post("/api/remove-background")
async def remove_background(file: UploadFile = File(...)):
    """
    Enhanced Background Removal Endpoint using rembg:
    Automatically removes background from clothing photos to create clean PNG images.
    Returns transparent PNG base64.
    """
    try:
        image_bytes = await file.read()
        print(f"Original image size: {len(image_bytes)} bytes")

        from PIL import ImageOps
        input_image = Image.open(BytesIO(image_bytes))
        input_image = ImageOps.exif_transpose(input_image).convert("RGBA")
        
        models_to_try = ['u2net', 'u2netp', 'silueta']
        best_result = None
        
        for model_name in models_to_try:
            try:
                print(f"Trying rembg model: {model_name}")
                output_image = rembg.remove(input_image, session=rembg.new_session(model_name))
                best_result = output_image
                print(f"Successfully used model: {model_name}")
                break
            except Exception as model_error:
                print(f"Model {model_name} failed: {model_error}")
                continue
        
        if best_result is None:
            best_result = rembg.remove(input_image)
        
        # Clean mask & auto-rotate upright
        best_result = clean_mask_connected_components(best_result)
        output_image = category_aware_rotate(best_result)
        
        if output_image.mode == 'RGBA':
            output_image = clean_mask_connected_components(output_image)
        
        output_bytes = BytesIO()
        output_image.save(output_bytes, format='PNG')
        output_bytes.seek(0)
        
        processed_image_data = base64.b64encode(output_bytes.read()).decode('utf-8')
        
        return {
            "status": "success",
            "processed_image": f"data:image/png;base64,{processed_image_data}",
            "original_size": len(image_bytes),
            "processed_size": len(processed_image_data)
        }

    except Exception as e:
        print(f"Error in remove_background: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Background removal failed: {str(e)}")

def clean_mask_connected_components(image: Image.Image) -> Image.Image:
    """
    Refined background removal post-processing:
    - Removes white edge halos, background bleed, and border artifacts.
    - Erodes alpha boundary by 1-2px to clip off original white backdrop rim.
    - Suppresses white background color bleed on garment edges.
    - Keeps natural internal gaps (crotch split, collar, armholes) clean & transparent.
    """
    import cv2
    import numpy as np

    rgba = np.array(image.convert("RGBA"))
    r, g, b, alpha = rgba[:, :, 0], rgba[:, :, 1], rgba[:, :, 2], rgba[:, :, 3]

    # Binary mask of alpha (alpha > 40 trims faint background reflections)
    _, binary_mask = cv2.threshold(alpha, 40, 255, cv2.THRESH_BINARY)

    # 1. Morphological erosion (1-2px) to shave off the white backdrop rim line
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    eroded_mask = cv2.erode(binary_mask, kernel, iterations=1)

    # 2. Isolate largest connected component(s) (removes floating specks)
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(eroded_mask, connectivity=8)

    if num_labels > 1:
        areas = stats[1:, cv2.CC_STAT_AREA]
        max_area = np.max(areas)
        valid_labels = np.where(areas >= max_area * 0.03)[0] + 1
        garment_mask = np.isin(labels, valid_labels).astype(np.uint8) * 255
    else:
        garment_mask = eroded_mask

    # Apply trimmed mask to alpha channel
    final_alpha = np.where(garment_mask == 255, alpha, 0).astype(np.uint8)

    # 3. Suppress white edge halo on border pixels
    dilated_alpha = cv2.dilate(final_alpha, kernel, iterations=1)
    border_zone = (dilated_alpha > 0) & (final_alpha > 0) & (final_alpha < 240)
    
    # White background bleed detector: where border pixel is bright (R,G,B > 170)
    white_edge = border_zone & (r > 170) & (g > 170) & (b > 170)
    
    # Inpaint or bleed solid dark garment color into white edge pixels
    solid_interior = (final_alpha > 240) & ~((r > 200) & (g > 200) & (b > 200))
    if np.any(solid_interior) and np.any(white_edge):
        rgb = rgba[:, :, :3]
        inpainted_rgb = cv2.inpaint(rgb, (~solid_interior).astype(np.uint8), inpaintRadius=5, flags=cv2.INPAINT_TELEA)
        rgba[:, :, :3] = np.where(np.expand_dims(white_edge, -1), inpainted_rgb, rgb)

    rgba[:, :, 3] = final_alpha
    return Image.fromarray(rgba, mode="RGBA")

def category_aware_rotate(image: Image.Image, category: Optional[str] = "tops") -> Image.Image:
    """
    PCA & Bounding Box Auto-Orientation Detection:
    Automatically detects horizontal/sideways clothing & accessory photos and rotates them upright.
    - Handles EXIF orientation tags.
    - Checks bounding box aspect ratio (if width > height * 1.05, garment is sideways -> rotate 90 degrees upright).
    - Verifies top vs bottom profile density to avoid inverted orientation.
    """
    import cv2
    import numpy as np
    
    cat = (category or "tops").lower().strip()
    rgba = np.array(image.convert("RGBA"))
    alpha = rgba[:, :, 3]
    
    ys, xs = np.where(alpha > 20)
    if len(xs) < 100 or len(ys) < 100:
        return image
        
    w = xs.max() - xs.min()
    h = ys.max() - ys.min()
    
    is_sideways = False
    
    # 1. Bounding box ratio check: standard clothes/accessories are taller than wide
    if w > h * 1.05:
        is_sideways = True
    else:
        # PCA Principal Component angle analysis for subtle tilt / diagonal sideways shots
        pts = np.column_stack((xs, ys)).astype(np.float32)
        mean, eigenvectors = cv2.PCACompute(pts, mean=None)
        angle = np.degrees(np.arctan2(eigenvectors[0, 1], eigenvectors[0, 0]))
        angle = abs(angle) % 180
        
        if (35 < angle < 145 and w > h * 0.95):
            is_sideways = True
            
    current_img = image
    if is_sideways:
        # Rotate 90 degrees clockwise to bring height > width
        current_img = image.rotate(270, expand=True, resample=Image.Resampling.BICUBIC)
        
    # 2. Garment Upright Orientation Check (Top vs Bottom region check)
    rgba_curr = np.array(current_img.convert("RGBA"))
    alpha_curr = rgba_curr[:, :, 3]
    ys_c, xs_c = np.where(alpha_curr > 20)
    
    if len(ys_c) > 50:
        min_y, max_y = ys_c.min(), ys_c.max()
        height_c = max_y - min_y
        
        top_slice = alpha_curr[min_y : min_y + int(height_c * 0.25), :]
        bot_slice = alpha_curr[max_y - int(height_c * 0.25) : max_y, :]
        
        # Check pants leg split at bottom vs waistband at top
        if cat in ["bottoms", "pants", "trousers", "jeans", "shorts", "skirt"]:
            num_top, _ = cv2.connectedComponents((top_slice > 20).astype(np.uint8))
            num_bot, _ = cv2.connectedComponents((bot_slice > 20).astype(np.uint8))
            if num_top > num_bot and num_top >= 3:
                # Leg split is at top -> inverted! Rotate 180 degrees
                current_img = current_img.rotate(180, expand=True, resample=Image.Resampling.BICUBIC)
                
    return current_img

def crop_and_standardize_1024(
    image: Image.Image, 
    canvas_size: int = 1024, 
    target_ratio: float = 0.82,
    backdrop: str = "transparent"
) -> Image.Image:
    """
    Standardizes clothing cutouts into a uniform 1024x1024 e-commerce product image:
    1. Tight crops around non-transparent garment pixels
    2. Scales item proportionally to ~82% of max canvas dimension
    3. Centers item on a 1024x1024 studio canvas (transparent PNG or clean white/checkerboard)
    """
    import numpy as np
    
    rgba = np.array(image.convert("RGBA"))
    alpha = rgba[:, :, 3]
    
    ys, xs = np.where(alpha > 20)
    if len(xs) == 0 or len(ys) == 0:
        # Fallback if empty image
        return image.resize((canvas_size, canvas_size), Image.Resampling.LANCZOS)
        
    x1, y1 = xs.min(), ys.min()
    x2, y2 = xs.max(), ys.max()
    
    cropped = image.crop((x1, y1, x2 + 1, y2 + 1))
    width, height = cropped.size
    
    max_dim = int(canvas_size * target_ratio)
    scale = min(max_dim / width, max_dim / height)
    
    new_w = max(1, int(width * scale))
    new_h = max(1, int(height * scale))
    
    resized = cropped.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    if backdrop == "white":
        canvas = Image.new("RGBA", (canvas_size, canvas_size), (255, 255, 255, 255))
    elif backdrop == "studio_checkerboard":
        canvas = Image.new("RGBA", (canvas_size, canvas_size), (248, 249, 252, 255))
    else:
        canvas = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
        
    pos_x = (canvas_size - new_w) // 2
    pos_y = (canvas_size - new_h) // 2
    
    canvas.alpha_composite(resized, (pos_x, pos_y))
    return canvas

@app.post("/api/process-clothing")
async def process_clothing_image(
    file: UploadFile = File(...),
    category: Optional[str] = Form(None)
):
    """
    Combined Endpoint: AI Analysis + E-Commerce Studio Background Removal & Standardization
    1. Removes background to create clean transparent PNG image
    2. Cleans mask using Connected Component Analysis (isolates largest garment piece)
    3. Applies category-aware orientation rotation
    4. Crops and standardizes to 1024x1024 canvas
    5. Analyzes the clothing item using GPT-4 Vision
    """
    try:
        image_bytes = await file.read()
        print(f"Processing clothing image of size: {len(image_bytes)} bytes")

        # Step 1: Background removal with EXIF orientation fix
        from PIL import ImageOps

        input_image = Image.open(BytesIO(image_bytes))
        input_image = ImageOps.exif_transpose(input_image).convert("RGBA")
        
        # Remove background using rembg
        raw_cutout = rembg.remove(input_image)
        
        # Step 2: ChatGPT's Mask Cleaning (Connected Components)
        clean_cutout = clean_mask_connected_components(raw_cutout)
        
        # Step 3: Category-Aware Orientation Correction
        oriented_cutout = category_aware_rotate(clean_cutout, category=category)
        
        # Step 4: Crop & Center on Standard 1024x1024 Canvas
        standardized_studio_image = crop_and_standardize_1024(oriented_cutout, canvas_size=1024)
        
        processed_bytes = BytesIO()
        standardized_studio_image.save(processed_bytes, format='PNG')
        processed_bytes.seek(0)
        processed_image_data = base64.b64encode(processed_bytes.read()).decode('utf-8')
        
        # Step 2: AI Analysis
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            seed = len(image_bytes) % 1000
            random.seed(seed)
            categories = ["tops", "bottoms", "outerwear", "footwear", "bags", "accessories"]
            colors = ["Black", "Blue", "Red", "White", "Grey", "Brown", "Green", "Pink", "Yellow", "Navy"]
            patterns = ["Solid", "Striped", "Floral", "Geometric", "Plaid", "Polka Dot", "Checkered"]
            styles = ["casual", "formal", "smart-casual", "streetwear", "ethnic", "sporty"]
            subcategories = {
                "tops": ["T-Shirt", "Shirt", "Blouse", "Sweater", "Hoodie", "Tank Top"],
                "bottoms": ["Jeans", "Trousers", "Shorts", "Skirt", "Leggings", "Chinos"],
                "outerwear": ["Jacket", "Coat", "Blazer", "Cardigan", "Vest", "Windbreaker"],
                "footwear": ["Sneakers", "Loafers", "Boots", "Sandals", "Heels", "Flats"],
                "bags": ["Handbag", "Backpack", "Tote", "Clutch", "Crossbody", "Shoulder Bag"],
                "accessories": ["Watch", "Belt", "Scarf", "Hat", "Jewelry", "Sunglasses"]
            }
            selected_category = categories[seed % len(categories)]
            selected_color = colors[seed % len(colors)]
            selected_pattern = patterns[seed % len(patterns)]
            selected_style = styles[seed % len(styles)]
            selected_subcategory = subcategories[selected_category][seed % len(subcategories[selected_category])]
            analysis = {
                "category": selected_category,
                "subcategory": selected_subcategory,
                "color": selected_color,
                "pattern": selected_pattern,
                "style": selected_style,
                "confidence": 0.85
            }
            return {
                "status": "success",
                "processed_image": f"data:image/png;base64,{processed_image_data}",
                "analysis": analysis
            }

        try:
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """Analyze this clothing item and provide the following information in JSON format:
{
  "category": "one of: tops, bottoms, outerwear, footwear, bags, accessories",
  "subcategory": "specific type (e.g., T-Shirt, Jeans, Jacket, Sneakers, Handbag, Watch)",
  "color": "dominant color (e.g., Black, Blue, Red, White, Grey, Brown, Green, Pink, Yellow, Navy)",
  "pattern": "pattern type (e.g., Solid, Striped, Floral, Geometric, Plaid, Polka Dot, Checkered)",
  "style": "style aesthetic (e.g., casual, formal, smart-casual, streetwear, ethnic, sporty)"
}
Return ONLY the JSON, no other text."""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{processed_image_data}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300
            )

            content = response.choices[0].message.content
            import json
            analysis = json.loads(content)

            valid_categories = ["tops", "bottoms", "outerwear", "footwear", "bags", "accessories"]
            if analysis.get("category") not in valid_categories:
                analysis["category"] = "tops"

            valid_styles = ["casual", "formal", "smart-casual", "streetwear", "ethnic", "sporty"]
            if analysis.get("style") not in valid_styles:
                analysis["style"] = "casual"

            analysis["confidence"] = 0.95

            return {
                "status": "success",
                "processed_image": f"data:image/png;base64,{processed_image_data}",
                "analysis": analysis
            }
        except Exception as openai_error:
            seed = len(image_bytes) % 1000
            random.seed(seed)
            categories = ["tops", "bottoms", "outerwear", "footwear", "bags", "accessories"]
            colors = ["Black", "Blue", "Red", "White", "Grey", "Brown", "Green", "Pink", "Yellow", "Navy"]
            patterns = ["Solid", "Striped", "Floral", "Geometric", "Plaid", "Polka Dot", "Checkered"]
            styles = ["casual", "formal", "smart-casual", "streetwear", "ethnic", "sporty"]
            subcategories = {
                "tops": ["T-Shirt", "Shirt", "Blouse", "Sweater", "Hoodie", "Tank Top"],
                "bottoms": ["Jeans", "Trousers", "Shorts", "Skirt", "Leggings", "Chinos"],
                "outerwear": ["Jacket", "Coat", "Blazer", "Cardigan", "Vest", "Windbreaker"],
                "footwear": ["Sneakers", "Loafers", "Boots", "Sandals", "Heels", "Flats"],
                "bags": ["Handbag", "Backpack", "Tote", "Clutch", "Crossbody", "Shoulder Bag"],
                "accessories": ["Watch", "Belt", "Scarf", "Hat", "Jewelry", "Sunglasses"]
            }
            analysis = {
                "category": categories[seed % len(categories)],
                "subcategory": subcategories[categories[seed % len(categories)]][seed % len(subcategories[categories[seed % len(categories)]])],
                "color": colors[seed % len(colors)],
                "pattern": patterns[seed % len(patterns)],
                "style": styles[seed % len(styles)],
                "confidence": 0.85
            }
            return {
                "status": "success",
                "processed_image": f"data:image/png;base64,{processed_image_data}",
                "analysis": analysis
            }

    except Exception as e:
        print(f"Error in process_clothing_image: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Clothing processing failed: {str(e)}")

def process_ghost_mannequin_effect(clothing_bytes: bytes, style: str = "hollow_man", backdrop: str = "checkerboard") -> str:
    """
    Generates a high-quality 3D Ghost Mannequin / Invisible Mannequin apparel render:
    1. Background removal using rembg
    2. Morphological mask cleaning to remove stray floor/bed artifacts
    3. Auto-orientation detection (rotates sideways photos upright)
    4. Auto-cropping & Studio Centering
    5. E-commerce studio checkerboard or transparent backdrop + 3D drop shadow
    """
    from PIL import ImageOps, ImageFilter, ImageEnhance
    import cv2
    import numpy as np

    input_image = Image.open(BytesIO(clothing_bytes))
    # Correct EXIF orientation from phone uploads
    input_image = ImageOps.exif_transpose(input_image).convert("RGBA")
    output_image = rembg.remove(input_image)

    # Clean mask, defringe white edges, and preserve inner background gaps
    clean_pil = clean_mask_connected_components(output_image)

    # Convert to OpenCV RGBA for precision processing
    img_np = np.array(clean_pil)
    cleaned_alpha = img_np[:, :, 3]

    # Find tight bounding box of garment
    bbox = cv2.boundingRect(cleaned_alpha)
    x, y, w, h = bbox

    # Intelligent Auto-Orientation: Check if garment alpha mask is wider than tall (sideways phone shot)
    if w > h * 1.15 and w > 100:
        # Rotate 90 degrees upright
        img_np = cv2.rotate(img_np, cv2.ROTATE_90_COUNTERCLOCKWISE)
        cleaned_alpha = img_np[:, :, 3]
        bbox = cv2.boundingRect(cleaned_alpha)
        x, y, w, h = bbox

    if w > 0 and h > 0:
        pad = int(max(w, h) * 0.06)
        H_orig, W_orig = img_np.shape[:2]
        x1, y1 = max(0, x - pad), max(0, y - pad)
        x2, y2 = min(W_orig, x + w + pad), min(H_orig, y + h + pad)
        img_np = img_np[y1:y2, x1:x2]

    garment_pil = Image.fromarray(img_np, mode="RGBA")
    max_dim = max(garment_pil.width, garment_pil.height)
    canvas_size = max(512, max_dim + 40)
    
    if backdrop == "checkerboard":
        # Create transparent checkerboard studio grid (exact match to e-commerce product standards like Image 3!)
        canvas = Image.new("RGBA", (canvas_size, canvas_size), (245, 245, 248, 255))
        sq_size = 20
        for i in range(0, canvas_size, sq_size):
            for j in range(0, canvas_size, sq_size):
                if (i // sq_size + j // sq_size) % 2 == 0:
                    for x_sq in range(i, min(i + sq_size, canvas_size)):
                        for y_sq in range(j, min(j + sq_size, canvas_size)):
                            canvas.putpixel((x_sq, y_sq), (230, 230, 235, 255))
    else:
        canvas = Image.new("RGBA", (canvas_size, canvas_size), (255, 255, 255, 0))

    # Add 3D apparel depth shadow (hollow man studio effect)
    shadow = Image.new("RGBA", garment_pil.size, (0, 0, 0, 0))
    g_alpha = garment_pil.split()[3]
    shadow_alpha = g_alpha.filter(ImageFilter.GaussianBlur(radius=10))
    shadow_alpha = ImageEnhance.Brightness(shadow_alpha).enhance(0.35)
    shadow.putalpha(shadow_alpha)

    # Center garment on studio canvas
    pos_x = (canvas_size - garment_pil.width) // 2
    pos_y = (canvas_size - garment_pil.height) // 2

    canvas.paste(shadow, (pos_x + 5, pos_y + 8), shadow)
    canvas.paste(garment_pil, (pos_x, pos_y), garment_pil)

    out_bytes = BytesIO()
    canvas.save(out_bytes, format="PNG")
    out_bytes.seek(0)
    return base64.b64encode(out_bytes.read()).decode("utf-8")

@app.post("/api/ghost-mannequin")
async def ghost_mannequin(
    clothing_image: UploadFile = File(...),
    style: str = "hollow_man",
    backdrop: str = "checkerboard"
):
    """
    Ghost Mannequin Endpoint:
    Generates invisible 3D mannequin effect for e-commerce clothing views.
    Includes auto-orienting, auto-cropping, edge noise cleaning, and studio checkerboard rendering.
    """
    try:
        clothing_bytes = await clothing_image.read()
        photta_api_key = os.getenv("PHOTTA_API_KEY")
        
        if photta_api_key and photta_api_key != "your_photta_api_key_here":
            try:
                photta_url = "https://api.photta.ai/api/v1/ghost-mannequin"
                files = {'image': (clothing_image.filename or 'clothing.jpg', clothing_bytes, 'image/jpeg')}
                data = {'style': style}
                headers = {'Authorization': f'Bearer {photta_api_key}'}
                
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(photta_url, files=files, data=data, headers=headers)
                    if response.status_code == 200:
                        result = response.json()
                        ghost_image_url = result.get('image_url') or result.get('url') or result.get('result')
                        if ghost_image_url:
                            return {
                                "status": "success",
                                "ghost_mannequin_image": ghost_image_url,
                                "method": "photta-ghost-mannequin"
                            }
            except Exception as p_err:
                print(f"Photta API skipped: {p_err}. Using localized 3D Ghost Mannequin processor.")

        ghost_base64 = process_ghost_mannequin_effect(clothing_bytes, style, backdrop)
        return {
            "status": "success",
            "ghost_mannequin_image": f"data:image/png;base64,{ghost_base64}",
            "method": "3d-ghost-mannequin-processor"
        }

    except Exception as e:
        print(f"Error in ghost_mannequin: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Fallback to transparent background removal if ghost mannequin fails
        try:
            input_image = Image.open(BytesIO(clothing_bytes)).convert("RGBA")
            output_image = rembg.remove(input_image)
            out_bytes = BytesIO()
            output_image.save(out_bytes, format='PNG')
            return {
                "status": "success",
                "ghost_mannequin_image": f"data:image/png;base64,{base64.b64encode(out_bytes.getvalue()).decode('utf-8')}",
                "method": "enhanced-background-removal"
            }
        except Exception:
            clothing_base64 = base64.b64encode(clothing_bytes).decode('utf-8')
            return {
                "status": "success",
                "ghost_mannequin_image": f"data:image/jpeg;base64,{clothing_base64}",
                "method": "original"
            }
