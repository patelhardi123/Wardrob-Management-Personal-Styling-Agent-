"""
Voice Stylist Agent LangGraph Workflow
Integrates voice commands with the existing multi-agent outfit recommendation pipeline.
Handles intent understanding, status updates, availability checking, and conversation context.

Gemini-powered conversational intelligence (gemini_stylist.py) is the PRIMARY understanding
layer — it handles any styling question, complex context, and open-ended requests.
The legacy keyword/rule-based parser serves as fallback.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import json
import re
import sqlite3
import uuid
from datetime import datetime, timedelta
from pydantic import ValidationError

from agent_graph import WardrobeItem, run_multi_agent_pipeline
from fashion.llm_client import get_llm_client_and_model
import database as db

# Gemini conversational intelligence — primary understanding layer
try:
    from gemini_stylist import process_with_gemini, answer_general_style_question, classify_message_type
    _GEMINI_AVAILABLE = True
except ImportError:
    _GEMINI_AVAILABLE = False
    def process_with_gemini(*a, **kw): return None
    def answer_general_style_question(*a, **kw): return ""
    def classify_message_type(msg): return "unknown"


def _get_user_clothes(user_id: int):
    return db.get_all_clothes() if user_id == 1 else db.get_all_clothes(user_id)


def _planned_wearing_deadline(message: str) -> datetime:
    now = datetime.now().astimezone()
    text = message.lower()
    if "tomorrow" in text:
        return now + timedelta(days=1)
    for day_index, day_name in enumerate(
        ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
    ):
        if re.search(r"\b" + day_name + r"\b", text):
            days_ahead = (day_index - now.weekday()) % 7
            return now + timedelta(days=days_ahead)
    return now


class VoiceAgentState(BaseModel):
    # User and conversation context
    user_id: int = 1
    user_message: str = ""
    conversation_history: List[Dict[str, str]] = []

    # Intent classification
    intent: str = ""  # outfit_request, status_update, availability_query, modification, weather_request
    occasion: Optional[str] = None
    style_preference: Optional[str] = None
    constraints: List[str] = []
    exclude_items: List[str] = []
    target_garment: Optional[Dict[str, Any]] = None
    status_change: Optional[Dict[str, str]] = None
    planning_time: Optional[str] = None  # "today", "tomorrow", etc.
    conversation_id: Optional[str] = None
    required_colors: List[str] = []
    required_top_colors: List[str] = []
    preferred_colors: List[str] = []
    excluded_colors: List[str] = []
    excluded_items: List[str] = []
    ready_to_wear_only: bool = False
    required_garment_types: List[str] = []
    excluded_categories: List[str] = []
    excluded_item_ids: List[str] = []
    locked_item_ids: List[str] = []
    excluded_outfit_signatures: List[str] = []
    availability_constraints: List[str] = []
    current_outfits: List[Dict[str, Any]] = []
    current_outfit_id: Optional[str] = None
    pending_clarification: Optional[str] = None
    saved_outfit_ids: List[str] = []
    parse_warning: Optional[str] = None

    # Workflow state
    clothes: List[WardrobeItem] = []
    filtered_clothes: List[WardrobeItem] = []
    recommended_outfits: List[Dict[str, Any]] = []
    status_update_result: Optional[Dict[str, Any]] = None
    weather_data: Optional[Dict[str, Any]] = None

    # Final response
    agent_response: str = ""
    response_type: str = "text"  # text, outfit, no_match, status_update, error
    execution_trace: List[Dict[str, Any]] = []


def intent_understanding_node(state: VoiceAgentState) -> VoiceAgentState:
    """
    Node 1: Intent Understanding
    Uses LLM to classify user intent and extract structured parameters.
    """
    import random
    message = state.user_message.lower()

    # Check if this is a follow-up request (based on conversation history)
    is_follow_up = len(state.conversation_history) > 0
    previous_occasion = None
    previous_constraints = []

    if is_follow_up:
        # Extract context from previous conversation
        for turn in reversed(state.conversation_history):
            if turn["role"] == "assistant":
                prev_msg = turn["content"].lower()
                # Try to extract occasion from previous response
                for occ in ["interview", "wedding", "college", "party", "office", "date", "travel"]:
                    if occ in prev_msg:
                        previous_occasion = occ
                        break
            if turn["role"] == "user":
                prev_user_msg = turn["content"].lower()
                # Try to extract constraints from previous user message
                if "without" in prev_user_msg or "no " in prev_user_msg or "don't" in prev_user_msg:
                    previous_constraints.append(prev_user_msg)
                break

    # Rule-based intent classification (fallback)
    intent = "outfit_request"
    occasion = None
    constraints = []
    exclude_items = []
    target_garment = None
    status_change = None
    planning_time = "today"

    status_patterns = [
        (r"(?:my\s+)?(.+?)\s+(?:is\s+|are\s+)?(?:in the wash|in wash|in the washing machine|in washing machine)", "in_wash", None),
        (r"(?:i put\s+)?(?:my\s+)?(.+?)\s+(?:in the laundry|into the laundry|in laundry)", "to_wash", None),
        (r"(?:my\s+)?(.+?)\s+(?:is\s+|are\s+)?drying\b", "drying", None),
        (r"(?:my\s+)?(.+?)\s+(?:needs|need|requires)\s+washing", "to_wash", None),
        (r"(?:my\s+)?(.+?)\s+(?:is\s+|are\s+)?(?:missing|lost)\b", "missing", None),
        (r"(?:my\s+)?(.+?)\s+(?:is\s+|are\s+)?(?:damaged|broken|torn)\b", "damaged", None),
        (r"(?:my\s+)?(.+?)\s+(?:is\s+|are\s+)?(?:borrowed|lent out)\b", "borrowed", None),
        (r"(?:my\s+)?(.+?)\s+(?:needs|need|requires)\s+ironing", None, "needs_ironing"),
        (r"(?:my\s+)?(.+?)\s+(?:is\s+|are\s+)?being ironed\b", None, "being_ironed"),
        (r"(?:i have ironed|i ironed)\s+(?:my\s+)?(.+)", None, "ready"),
        (r"(?:my\s+)?(.+?)\s+(?:is\s+|are\s+)?(?:ready to wear|ready now|ready)\b", "ready", "ready"),
        (r"(?:my\s+)?(.+?)\s+(?:is\s+|are\s+)?clean\b", "ready", None),
    ]
    if re.search(r"\b(?:don't|dont|do not|avoid|exclude)\b", message):
        status_patterns = []
    if re.search(r"\b(?:only|suggest|recommend|outfit|clothes)\b", message) and "ready to wear" in message:
        status_patterns = [pattern for pattern in status_patterns if pattern[0] != r"(?:my\s+)?(.+?)\s+(?:is\s+|are\s+)?(?:ready to wear|ready now|ready)\b"]
    for pattern, availability_status, ironing_status in status_patterns:
        match = re.search(pattern, message)
        if not match:
            continue
        garment_desc = re.sub(r"\b(?:please|now|today|tomorrow)\b", "", match.group(1)).strip(" .,!?")
        if not garment_desc:
            continue
        intent = "status_update"
        status_change = {
            "garment_description": garment_desc,
            "availability_status": availability_status,
            "ironing_status": ironing_status,
        }
        target_garment = {"description": garment_desc}
        break

    expected_time_match = re.search(
        r"(?:my\s+)?(.+?)\s+(?:should be|will be|be|is expected to be)\s+ready\s+by\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b",
        message
    )
    if expected_time_match:
        garment_desc = expected_time_match.group(1).strip(" .,!?")
        hour = int(expected_time_match.group(2)) % 12
        minute = int(expected_time_match.group(3) or "0")
        if expected_time_match.group(4) == "pm":
            hour += 12
        expected_at = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
        if "tomorrow" in message:
            expected_at += timedelta(days=1)
        status_change = {
            "garment_description": garment_desc,
            "availability_status": None,
            "ironing_status": None,
            "expected_available_at": expected_at.isoformat()
        }
        target_garment = {"description": garment_desc}
        intent = "status_update"

    # Detect availability query
    if intent == "outfit_request" and any(kw in message for kw in ["what clothes", "which clothes", "available clothes", "unavailable", "in the wash"]):
        intent = "availability_query"

    # Detect modification requests
    if intent == "outfit_request" and any(kw in message for kw in ["replace", "don't use", "no", "without", "another option", "show me another"]):
        intent = "modification"

    # Detect weather-based requests
    if "weather" in message or "tomorrow" in message:
        planning_time = "tomorrow" if "tomorrow" in message else "today"

    # Extract occasion — check interview/wedding before generic office/casual words
    occasion_keywords = [
        ("job interview", ["job interview", "interview", "placement"]),
        ("wedding", ["wedding", "marriage", "reception", "sangeet", "mehndi", "shaadi"]),
        ("office", ["office", "work", "meeting", "presentation", "corporate"]),
        ("party", ["party", "club", "night out"]),
        ("date", ["date", "dinner", "romantic"]),
        ("college", ["college", "class", "lecture", "study"]),
        ("travel", ["travel", "trip", "vacation"]),
    ]

    for occ, keywords in occasion_keywords:
        if any(kw in message for kw in keywords):
            occasion = occ
            break

    # If no occasion mentioned and it's a follow-up, use previous occasion
    if not occasion and is_follow_up and previous_occasion:
        occasion = previous_occasion

    # Do NOT default to "college" — leave occasion as None if undetected
    # The calling code in run_voice_agent_pipeline will handle None gracefully

    # Extract exclusions
    if "without" in message:
        match = re.search(r"without (.+?)(?:\.|$|,| for)", message)
        if match:
            exclude_items.append(match.group(1).strip())
    if "don't" in message or "dont" in message:
        match = re.search(r"don't (?:suggest|use|wear) (.+?)(?:\s+(?:today|tomorrow)\b|\.|$|,)", message)
        if not match:
            match = re.search(r"dont (?:suggest|use|wear) (.+?)(?:\s+(?:today|tomorrow)\b|\.|$|,)", message)
        if match:
            exclude_items.append(match.group(1).strip())
    if "no " in message:
        match = re.search(r"no (.+?)(?:\.|$|,| for)", message)
        if match:
            exclude_items.append(match.group(1).strip())

    # Add previous constraints if this is a follow-up
    if is_follow_up and previous_constraints:
        for prev_constraint in previous_constraints:
            if "without" in prev_constraint:
                match = re.search(r"without (.+)", prev_constraint)
                if match and match.group(1).strip() not in exclude_items:
                    exclude_items.append(match.group(1).strip())

    # Extract style preference
    style_keywords = {
        "ethnic": ["ethnic", "traditional", "indian", "lehenga", "saree", "anarkali"],
        "western": ["western", "tuxedo"],
        "casual": ["casual", "relaxed", "comfortable"],
        "formal": ["formal", "professional", "elegant"],
        "streetwear": ["streetwear", "urban", "cool"],
        "smart-casual": ["smart-casual", "smart casual", "chic"]
    }

    for style, keywords in style_keywords.items():
        if any(kw in message for kw in keywords):
            state.style_preference = style
            break

    if not state.style_preference:
        occasion_style_defaults = {
            "wedding": "ethnic",
            "job interview": "formal",
            "office": "formal",
            "college": "casual",
            "party": "smart-casual",
            "date": "smart-casual",
            "travel": "casual",
        }
        state.style_preference = occasion_style_defaults.get(occasion or "college", "casual")

    # Extract "ready to wear" constraint
    if "ready to wear" in message or "only ready" in message:
        constraints.append("ready_to_wear_only")

    state.intent = intent
    state.occasion = occasion
    state.constraints = constraints
    state.exclude_items = exclude_items
    state.target_garment = target_garment
    state.status_change = status_change
    state.planning_time = planning_time

    state.execution_trace.append({
        "agent": "Intent Understanding",
        "status": "completed",
        "intent": intent,
        "occasion": occasion,
        "summary": f"Classified intent as '{intent}' for occasion '{occasion}'"
    })

    return state


def wardrobe_retrieval_node(state: VoiceAgentState) -> VoiceAgentState:
    """
    Node 2: Wardrobe Retrieval with Availability Filtering
    Fetches user's wardrobe and applies availability constraints.
    """
    clothes = _get_user_clothes(state.user_id)

    # Convert to WardrobeItem objects
    wardrobe_items = []
    for item in clothes:
        wardrobe_items.append(WardrobeItem(
            id=item["id"],
            title=item["title"],
            category=item["category"],
            color=item["color"],
            pattern=item["pattern"],
            style=item["style"],
            season=item["season"],
            usageCount=item["usageCount"],
            imageUrl=item["imageUrl"],
            attributes=item["attributes"],
            availability_status=item.get("availability_status", "available"),
            ironing_status=item.get("ironing_status", "ready"),
            expected_available_at=item.get("expected_available_at")
        ))

    state.clothes = wardrobe_items

    # Apply availability filtering if "ready to wear" constraint
    if "ready_to_wear_only" in state.constraints:
        filtered = []
        for item in clothes:
            avail = item.get("availability_status", "available")
            iron = item.get("ironing_status", "ready")
            if avail in ("ready", "available") and iron == "ready":
                filtered.append(item)
        state.filtered_clothes = [WardrobeItem(**item) for item in filtered]
    else:
        state.filtered_clothes = wardrobe_items

    state.execution_trace.append({
        "agent": "Wardrobe Retrieval",
        "status": "completed",
        "total_items": len(wardrobe_items),
        "filtered_items": len(state.filtered_clothes),
        "summary": f"Retrieved {len(wardrobe_items)} items, filtered to {len(state.filtered_clothes)} based on availability"
    })

    return state


def status_update_node(state: VoiceAgentState) -> VoiceAgentState:
    """
    Node 3: Status Update Handler
    Processes clothing availability and ironing status updates.
    """
    if state.intent != "status_update" or not state.status_change:
        return state

    garment_desc = state.status_change["garment_description"]
    avail_status = state.status_change.get("availability_status")
    iron_status = state.status_change.get("ironing_status")
    expected_available_at = state.status_change.get("expected_available_at")

    clothes = _get_user_clothes(state.user_id)
    description_words = [
        word for word in re.findall(r"[a-z0-9]+", garment_desc.lower())
        if word not in {"my", "the", "a", "an", "is", "are", "this", "that"}
    ]
    aliases = {
        "shirt": {"shirt", "shirts", "blouse", "top"},
        "tops": {"top", "tops", "shirt", "blouse"},
        "trouser": {"trouser", "trousers", "pant", "pants"},
        "trousers": {"trouser", "trousers", "pant", "pants"},
        "pants": {"trouser", "trousers", "pant", "pants"},
        "jeans": {"jean", "jeans", "denim"},
        "shoe": {"shoe", "shoes", "footwear", "sneaker", "loafer", "boot"},
        "shoes": {"shoe", "shoes", "footwear", "sneaker", "loafer", "boot"},
    }
    matches = []
    for item in clothes:
        attributes_text = json.dumps(item.get("attributes") or {}).lower()
        searchable = " ".join([
            item.get("title", ""), item.get("category", ""), item.get("color", ""),
            item.get("pattern", ""), item.get("style", ""), attributes_text
        ]).lower()
        terms_match = all(
            any(
                re.search(r"\b" + re.escape(alias) + r"\b", searchable)
                for alias in aliases.get(word, {word})
            )
            for word in description_words
        )
        if description_words and terms_match:
            matches.append(item)

    if len(matches) == 0:
        state.agent_response = f"I couldn't find any item matching '{garment_desc}' in your wardrobe; it was not found."
        state.response_type = "error"
        state.status_update_result = {"success": False, "reason": "not_found"}
        return state

    if len(matches) > 1:
        item_names = ", ".join([f"'{m['title']}'" for m in matches])
        state.agent_response = f"I found multiple items matching '{garment_desc}': {item_names}. Which one would you like to update?"
        state.response_type = "error"
        state.status_update_result = {"success": False, "reason": "ambiguous", "matches": matches}
        return state

    # Single match - update status
    item = matches[0]
    update_data = {}

    if avail_status:
        update_data["availability_status"] = avail_status
        if avail_status in {"to_wash", "in_wash"}:
            update_data["expected_available_at"] = None

    if iron_status:
        update_data["ironing_status"] = iron_status
    if expected_available_at:
        update_data["expected_available_at"] = expected_available_at

    try:
        updated_item = db.update_clothing_item(item["id"], update_data, state.user_id)
        state.status_update_result = {"success": True, "item": updated_item}

        status_text = []
        if avail_status:
            status_text.append(f"availability to '{avail_status}'")
        if iron_status:
            status_text.append(f"ironing status to '{iron_status}'")
        if expected_available_at:
            status_text.append(f"estimated ready time to {expected_available_at}")

        if not status_text:
            raise ValueError("No valid status or expected-ready-time update was provided.")
        state.agent_response = f"Updated {item['title']}: {' and '.join(status_text)}. An estimated time does not mark it ready automatically."
        state.response_type = "status_update"
    except Exception as e:
        state.agent_response = f"Sorry, I couldn't update the status: {str(e)}"
        state.response_type = "error"
        state.status_update_result = {"success": False, "reason": "database_error", "error": str(e)}

    state.execution_trace.append({
        "agent": "Status Update Handler",
        "status": "completed",
        "summary": f"Processed status update for '{garment_desc}'"
    })

    return state


def availability_query_node(state: VoiceAgentState) -> VoiceAgentState:
    """
    Node 4: Availability Query Handler
    Responds to questions about clothing availability.
    """
    import random
    if state.intent != "availability_query":
        return state

    clothes = _get_user_clothes(state.user_id)
    unavailable_items = []

    for item in clothes:
        avail = item.get("availability_status", "available")
        iron = item.get("ironing_status", "ready")

        if avail not in ("ready", "available") or iron != "ready":
            status_desc = []
            if avail != "available":
                status_desc.append(avail)
            if iron != "ready":
                status_desc.append(iron)
            unavailable_items.append({
                "title": item["title"],
                "status": ", ".join(status_desc)
            })

    if not unavailable_items:
        responses = [
            "All your clothes are currently available and ready to wear!",
            "Great news! Everything in your wardrobe is available and ready.",
            "Your wardrobe is fully stocked with all items ready to wear."
        ]
        state.agent_response = random.choice(responses)
    else:
        items_text = ", ".join([f"{i['title']} ({i['status']})" for i in unavailable_items])
        state.agent_response = f"The following items are currently unavailable: {items_text}."

    state.response_type = "text"
    state.execution_trace.append({
        "agent": "Availability Query Handler",
        "status": "completed",
        "unavailable_count": len(unavailable_items),
        "summary": f"Found {len(unavailable_items)} unavailable items"
    })

    return state
    unavailable_items = []

    for item in clothes:
        avail = item.get("availability_status", "available")
        iron = item.get("ironing_status", "ready")

        if avail != "available" or iron != "ready":
            status_desc = []
            if avail != "available":
                status_desc.append(avail)
            if iron != "ready":
                status_desc.append(iron)
            unavailable_items.append({
                "title": item["title"],
                "status": ", ".join(status_desc)
            })

    if not unavailable_items:
        state.agent_response = "All your clothes are currently available and ready to wear."
    else:
        items_text = ", ".join([f"{i['title']} ({i['status']})" for i in unavailable_items])
        state.agent_response = f"The following items are currently unavailable: {items_text}."

    state.response_type = "text"
    state.execution_trace.append({
        "agent": "Availability Query Handler",
        "status": "completed",
        "unavailable_count": len(unavailable_items),
        "summary": f"Found {len(unavailable_items)} unavailable items"
    })

    return state


def outfit_request_node(state: VoiceAgentState) -> VoiceAgentState:
    """
    Node 5: Outfit Request Handler
    Routes to existing multi-agent pipeline with voice-derived constraints.
    """
    if state.intent not in ["outfit_request", "modification"]:
        return state

    # Build context rules from exclusions
    context_rules = ""
    if state.exclude_items:
        context_rules = f"Exclude: {', '.join(state.exclude_items)}"

    # Call existing pipeline
    try:
        clothes_dicts = [item.dict() for item in state.filtered_clothes]
        response = run_multi_agent_pipeline({
            "user_id": state.user_id,
            "occasion": state.occasion or "casual",
            "style_preference": state.style_preference or (
                "ethnic" if (state.occasion or "") in ["wedding", "festival"] else
                "formal" if (state.occasion or "") in ["job interview", "office", "corporate retreat"] else
                "elegant" if (state.occasion or "") in ["wedding anniversary", "anniversary", "prom", "cocktail party"] else
                "casual"
            ),
            "clothes": clothes_dicts,
            "context_rules": context_rules,
            "exclude_bags": False,
            "exclude_accessories": False,
            "required_colors": state.required_colors,
            "required_top_colors": state.required_top_colors,
            "preferred_colors": state.preferred_colors,
            "excluded_colors": state.excluded_colors,
            "excluded_categories": state.excluded_categories,
            "required_garment_types": state.required_garment_types,
            "excluded_item_ids": state.excluded_item_ids,
            "locked_item_ids": state.locked_item_ids,
            "excluded_outfit_signatures": state.excluded_outfit_signatures,
        })

        state.recommended_outfits = response.get("outfits", [])

        if state.recommended_outfits:
            # Generate more dynamic responses based on context
            import random
            occ_label = state.occasion or "this occasion"
            responses = [
                f"I've put together {len(state.recommended_outfits)} stylish outfit{'s' if len(state.recommended_outfits) > 1 else ''} for {occ_label}.",
                f"Here are {len(state.recommended_outfits)} great option{'s' if len(state.recommended_outfits) > 1 else ''} for your {occ_label} look.",
                f"Found {len(state.recommended_outfits)} perfect outfit{'s' if len(state.recommended_outfits) > 1 else ''} for {occ_label}!",
                f"Based on your wardrobe, here are {len(state.recommended_outfits)} outfit{'s' if len(state.recommended_outfits) > 1 else ''} that would work well for {occ_label}."
            ]
            state.agent_response = random.choice(responses)
            state.response_type = "outfit"
        else:
            occ_label = state.occasion or "this occasion"
            all_items_count = len(state.clothes)
            state.agent_response = (
                f"I couldn't find a complete outfit in your wardrobe for {occ_label} right now. "
                f"You have {all_items_count} items — try adding more variety or let me know if you'd like to adjust the style."
            )
            state.response_type = "no_match"

        state.execution_trace.append({
            "agent": "Outfit Request Handler",
            "status": "completed",
            "outfit_count": len(state.recommended_outfits),
            "summary": f"Generated {len(state.recommended_outfits)} outfit recommendations"
        })

    except Exception as e:
        state.agent_response = f"Sorry, I encountered an error generating outfits: {str(e)}"
        state.response_type = "error"
        state.execution_trace.append({
            "agent": "Outfit Request Handler",
            "status": "failed",
            "error": str(e),
            "summary": "Outfit generation failed"
        })

    return state


def response_generation_node(state: VoiceAgentState) -> VoiceAgentState:
    """
    Node 6: Response Generation
    Formats the final response for the user.
    """
    # Response is already set by previous nodes
    state.execution_trace.append({
        "agent": "Response Generation",
        "status": "completed",
        "response_type": state.response_type,
        "summary": "Generated final response"
    })

    return state


class StructuredStylistIntent(BaseModel):
    action: str = "recommend"
    occasion: Optional[str] = None
    style_preference: Optional[str] = None
    required_colors: List[str] = []
    required_top_colors: List[str] = []
    preferred_colors: List[str] = []
    excluded_colors: List[str] = []
    excluded_items: List[str] = []
    ready_to_wear_only: bool = False
    required_garment_types: List[str] = []
    excluded_categories: List[str] = []
    target_slot: Optional[str] = None
    keep_slots: List[str] = []
    selected_option: Optional[int] = None
    clarification: Optional[str] = None


OCCASION_PHRASES = (
    ("job interview", ("job interview", "interview", "placement")),
    ("wedding anniversary", ("wedding anniversary", "anniversary party", "anniversary celebration")),
    ("wedding", ("wedding", "marriage", "reception", "sangeet", "mehndi", "shaadi")),
    ("corporate retreat", ("corporate retreat", "team outing", "company retreat", "office retreat")),
    ("office", ("office", "work meeting", "corporate meeting", "presentation", "business meeting")),
    ("dinner date", ("dinner date", "date night", "romantic dinner")),
    ("cocktail party", ("cocktail party", "cocktail", "gala", "black tie")),
    ("graduation", ("graduation", "convocation", "farewell")),
    ("baby shower", ("baby shower", "gender reveal")),
    ("birthday party", ("birthday party", "birthday celebration", "birthday")),
    ("party", ("evening party", "party", "club", "night out")),
    ("brunch", ("brunch", "sunday brunch")),
    ("festival", ("festival", "diwali", "eid", "holi", "navratri", "christmas", "new year")),
    ("college", ("college", "class", "lecture", "campus")),
    ("travel", ("travel", "trip", "vacation")),
    ("date", ("date",)),
)
COLOR_NAMES = (
    "white", "ivory", "black", "blue", "navy", "red", "maroon", "green",
    "pink", "purple", "yellow", "orange", "brown", "beige", "grey", "gray",
    "gold", "silver", "cream"
)
SLOT_WORDS = {
    "tops": ("top", "shirt", "blouse", "t-shirt", "t shirt", "tshirt", "tee"),
    "bottoms": ("trouser", "trousers", "pant", "pants", "bottom", "jeans"),
    "footwear": ("shoe", "shoes", "footwear", "heel", "heels"),
    "outerwear": ("jacket", "blazer", "coat", "outerwear"),
    "bags": ("bag", "purse", "handbag"),
    "accessories": ("accessory", "accessories", "jewelry", "jewellery"),
}


def _contains_any(text: str, phrases) -> bool:
    return any(re.search(r"\b" + re.escape(phrase) + r"\b", text) for phrase in phrases)


ITEM_TERM_ALIASES = {
    "jeans": ("jean", "jeans", "denim"),
    "trousers": ("trouser", "trousers", "pant", "pants"),
    "pants": ("pant", "pants", "trouser", "trousers"),
    "shoe": ("shoe", "shoes", "footwear", "heel", "heels", "sneaker", "loafer", "boot", "sandal", "jutti", "mojari", "pump"),
    "shoes": ("shoe", "shoes", "footwear", "heel", "heels", "sneaker", "loafer", "boot", "sandal", "jutti", "mojari", "pump"),
    "footwear": ("shoe", "shoes", "footwear", "heel", "heels", "sneaker", "loafer", "boot", "sandal", "jutti", "mojari", "pump"),
    "bag": ("bag", "bags", "purse", "handbag", "tote", "crossbody", "backpack"),
    "dress": ("dress", "dresses", "gown", "frock", "one_piece", "one-piece", "anarkali"),
}


def _item_matches_description(item: Dict[str, Any], words: List[str]) -> bool:
    description = " ".join(
        str(value or "") for value in (
            item.get("title"), item.get("category"), item.get("color"),
            item.get("style"), item.get("attributes")
        )
    ).lower()
    for word in words:
        aliases = ITEM_TERM_ALIASES.get(word, (word,))
        if not any(re.search(r"\b" + re.escape(alias) + r"\b", description) for alias in aliases):
            return False
    return True


def _local_structured_intent(message: str, saved_state: Dict[str, Any]) -> StructuredStylistIntent:
    text = message.lower().strip()
    occasion = None
    for candidate, phrases in OCCASION_PHRASES:
        if _contains_any(text, phrases):
            occasion = candidate
            break
    if "dinner" in text and "date" in text:
        occasion = "dinner date"

    colors = [color for color in COLOR_NAMES if re.search(r"\b" + re.escape(color) + r"\b", text)]
    required_colors = []
    required_top_colors = []
    preferred_colors = []
    excluded_colors = []
    if _contains_any(text, ("only", "just")) and colors:
        required_colors = colors
    elif _contains_any(text, ("prefer", "like", "love")) and colors:
        preferred_colors = colors
    if colors:
        garment_terms = (
            "dress", "jeans", "trousers", "pants", "shirt", "blouse", "top",
            "lehenga", "saree", "kurta", "shoes", "heels", "jacket", "bag"
        )
        for segment in re.split(r"[;,.]|\bbut\b", text):
            segment_colors = [
                color for color in colors
                if re.search(r"\b" + re.escape(color) + r"\b", segment)
            ]
            if (
                segment_colors
                and re.search(r"\b(no|without|avoid|exclude|don't wear|dont wear)\b", segment)
                and not _contains_any(segment, garment_terms)
            ):
                excluded_colors.extend(segment_colors)
        excluded_colors = list(dict.fromkeys(excluded_colors))
    if colors and _contains_any(text, (
        "top", "tops", "shirt", "t-shirt", "t shirt", "tshirt", "tee", "blouse"
    )):
        required_top_colors = colors
        required_colors = [
            color for color in required_colors
            if color not in required_top_colors
        ]

    if re.search(r"\b(no longer|don't|dont|do not|remove|clear|relax)\b.{0,35}\b(white|black|blue|color|colour)\b", text):
        required_colors = []

    excluded_items = []
    excluded_match = re.search(
        r"\b(?:without|avoid|exclude|no|don't suggest|dont suggest|don't use|dont use|don't wear|dont wear)"
        r"\s+(?:(?:the|a|an|my|those|these|any)\s+)*(?P<item>[a-z][a-z -]*?)"
        r"(?:\s+(?:today|tomorrow|please|for|with)\b|[.,!?]|$)",
        text
    )
    if excluded_match:
        description = excluded_match.group("item").strip()
        description_words = description.split()
        if description_words and not all(
            word in COLOR_NAMES or word in {"clothes", "clothing", "items", "outfits"}
            for word in description_words
        ):
            excluded_items.append(description)

    ready_to_wear_only = _contains_any(text, (
        "ready to wear", "ready-to-wear", "ready clothes", "clothes that are ready"
    )) and not re.search(
        r"\b(?:don't|dont|do not|no longer|remove|relax|clear)\b.{0,35}\bready(?:[- ]to[- ]wear)?\b",
        text
    )
    required_types = []
    if (
        _contains_any(text, ("one-piece", "one piece", "dress"))
        and _contains_any(text, ("want", "need", "wear", "only", "prefer"))
        and not re.search(
            r"\b(?:don't|dont|do not|not|instead of)\s+"
            r"(?:(?:want|need|wear|choose)\s+)?(?:a|an)?\s*(?:one[- ]piece|dress)\b",
            text
        )
    ):
        required_types.append("one_piece")
    for garment_type in ("lehenga", "saree", "anarkali", "kurta", "gown", "jumpsuit"):
        if (
            re.search(r"\b" + re.escape(garment_type) + r"\b", text)
            and not re.search(
                r"\b(?:don't|dont|do not|not|without|no)\s+"
                r"(?:(?:want|need|wear|suggest|use)\s+)?(?:a|an|the)?\s*"
                + re.escape(garment_type) + r"\b",
                text
            )
        ):
            required_types.append(garment_type)

    excluded_categories = []
    if re.search(
        r"\b(?:no|without|exclude|remove|omit|skip|don't use|dont use|do not use)"
        r"\s+(?:(?:the|a|an)\s+)?bags?\b",
        text
    ):
        excluded_categories.append("bags")
    if re.search(
        r"\b(?:no|without|exclude|remove|omit|skip|don't use|dont use|do not use)"
        r"\s+(?:(?:the|any)\s+)?accessories\b",
        text
    ):
        excluded_categories.append("accessories")
    if _contains_any(text, ("no outerwear", "without a jacket", "without jacket", "remove jacket")):
        excluded_categories.append("outerwear")
    if _contains_any(text, ("no shoes", "no footwear", "without shoes")):
        excluded_categories.append("footwear")

    target_slot = None
    for slot, words in SLOT_WORDS.items():
        if slot not in excluded_categories and _contains_any(text, words):
            target_slot = slot
            break
    keep_slots = []
    for segment in re.split(r"\bbut\b|[,;]", text):
        if _contains_any(segment, ("with these", "with my", "wear with", "keep", "same")):
            keep_slots.extend(
                slot for slot, words in SLOT_WORDS.items()
                if _contains_any(segment, words)
            )

    selected_option = None
    option_match = re.search(
        r"\b(?:the\s+)?(first|second|third|1st|2nd|3rd)\s+"
        r"(?:option|outfit|look|preference|choice)\b",
        text
    )
    if option_match:
        selected_option = {
            "first": 1, "1st": 1, "second": 2, "2nd": 2, "third": 3, "3rd": 3
        }[option_match.group(1)]

    action = "recommend"
    explicit_day_plan = (
        _contains_any(text, ("save", "add", "plan", "schedule", "put", "reserve", "book", "assign"))
        and bool(re.search(
            r"\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|"
            r"mon|tue|tues|wed|thu|thur|thurs|fri|sat|sun)\b",
            text
        ))
    )
    if (
        _contains_any(text, ("save this look", "save this outfit", "save the look", "save the outfit", "bookmark this"))
        and not (explicit_day_plan and occasion)
    ):
        action = "save"
    elif _contains_any(text, ("start a new", "new outfit", "start over", "start again")):
        action = "new"
    elif _contains_any(text, ("show me another", "another option", "different outfit", "another outfit", "show another")):
        action = "another"
    elif excluded_categories or excluded_colors or excluded_items or ready_to_wear_only or _contains_any(text, ("change", "replace", "different", "don't like", "dont like", "keep the same", "remove the")):
        action = "modify"
    elif re.search(r"\b(?:update|updated|refresh|replace)\b", text):
        action = "modify"
    elif required_colors or required_top_colors or required_types or preferred_colors or target_slot:
        action = "modify" if saved_state.get("current_outfits") else "recommend"
    elif occasion:
        action = "recommend"

    style_preference = None
    if _contains_any(text, ("elegant", "elegance")):
        style_preference = "elegant"
    elif _contains_any(text, ("formal", "professional")):
        style_preference = "formal"
    elif _contains_any(text, ("trendy", "stylish")):
        style_preference = "stylish-trendy"
    elif _contains_any(text, ("casual", "comfortable")):
        style_preference = "casual"
    elif _contains_any(text, ("ethnic", "traditional")):
        style_preference = "ethnic"

    if style_preference and action == "recommend" and saved_state.get("current_outfits"):
        action = "modify"

    if selected_option and action == "recommend" and not occasion and not (
        required_colors or required_top_colors or required_types or preferred_colors or excluded_categories or target_slot or style_preference
    ):
        action = "select"

    clarification = None
    if occasion == "party" and not _contains_any(text, ("birthday", "wedding", "evening", "club", "night out")):
        clarification = "What kind of party is it—a birthday, wedding celebration, or evening party?"
        action = "clarify"

    return StructuredStylistIntent(
        action=action,
        occasion=occasion,
        style_preference=style_preference,
        required_colors=required_colors,
        required_top_colors=required_top_colors,
        preferred_colors=preferred_colors,
        excluded_colors=excluded_colors,
        excluded_items=excluded_items,
        ready_to_wear_only=ready_to_wear_only,
        required_garment_types=required_types,
        excluded_categories=excluded_categories,
        target_slot=target_slot,
        keep_slots=keep_slots,
        selected_option=selected_option,
        clarification=clarification
    )


def _understand_stylist_message(message: str, saved_state: Dict[str, Any]) -> StructuredStylistIntent:
    local_intent = _local_structured_intent(message, saved_state)
    client, model, _provider = get_llm_client_and_model()
    if not client:
        return local_intent

    prompt = (
        "Extract the styling request as JSON only. Do not recommend clothes, infer wardrobe items, "
        "or create IDs. Use only these keys: action (recommend, modify, replace, remove, another, "
        "save, new, clarify, question), occasion, style_preference, required_colors, "
        "required_top_colors, preferred_colors, excluded_colors, excluded_items, "
        "ready_to_wear_only, required_garment_types, excluded_categories, "
        "target_slot (tops, bottoms, footwear, outerwear, bags, accessories), keep_slots, selected_option, "
        "clarification. Be conservative: explicit restrictions are mandatory. "
        f"Current occasion: {saved_state.get('occasion') or 'none'}. "
        f"Current outfit slots: {saved_state.get('current_slot_names') or 'none'}. "
        f"User message: {message}"
    )
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0,
            max_tokens=300
        )
        parsed = StructuredStylistIntent.model_validate_json(response.choices[0].message.content or "{}")
        # Clear deterministic parsing has precedence over model ambiguity.
        if local_intent.action != "recommend" or local_intent.occasion or local_intent.required_colors or local_intent.required_top_colors or local_intent.required_garment_types:
            parsed.action = local_intent.action
        if local_intent.occasion:
            parsed.occasion = local_intent.occasion
        if local_intent.style_preference:
            parsed.style_preference = local_intent.style_preference
        parsed.required_colors = list(dict.fromkeys(local_intent.required_colors + parsed.required_colors))
        parsed.required_top_colors = list(dict.fromkeys(
            local_intent.required_top_colors + parsed.required_top_colors
        ))
        if local_intent.required_top_colors:
            parsed.required_colors = [
                color for color in parsed.required_colors
                if color not in local_intent.required_top_colors
            ]
        parsed.excluded_colors = list(dict.fromkeys(local_intent.excluded_colors + parsed.excluded_colors))
        parsed.excluded_items = list(dict.fromkeys(local_intent.excluded_items + parsed.excluded_items))
        parsed.ready_to_wear_only = local_intent.ready_to_wear_only or parsed.ready_to_wear_only
        parsed.required_garment_types = list(dict.fromkeys(local_intent.required_garment_types + parsed.required_garment_types))
        parsed.excluded_categories = list(dict.fromkeys(local_intent.excluded_categories + parsed.excluded_categories))
        parsed.keep_slots = list(dict.fromkeys(local_intent.keep_slots + parsed.keep_slots))
        if local_intent.selected_option:
            parsed.selected_option = local_intent.selected_option
        if local_intent.target_slot:
            parsed.target_slot = local_intent.target_slot
        if local_intent.clarification:
            parsed.clarification = local_intent.clarification
        return parsed
    except (ValidationError, ValueError, TypeError) as exc:
        print(f"[Stylist] Structured intent validation failed; using deterministic parser: {exc}")
        return local_intent
    except Exception as exc:
        print(f"[Stylist] Configured LLM request understanding failed; using deterministic parser: {exc}")
        return local_intent


def _outfit_signature(outfit: Dict[str, Any]) -> str:
    slots = outfit.get("slotItems") or {}
    return "|".join(
        str((slots.get(key) or {}).get("id") or "-")
        for key in ("topObj", "bottomObj", "shoeObj", "outerObj", "bagObj", "accObj")
    )


def _slot_item_ids(outfit: Dict[str, Any]) -> Dict[str, str]:
    slots = outfit.get("slotItems") or {}
    names = {
        "tops": "topObj",
        "bottoms": "bottomObj",
        "footwear": "shoeObj",
        "outerwear": "outerObj",
        "bags": "bagObj",
        "accessories": "accObj",
    }
    return {
        category: str(slots[key]["id"])
        for category, key in names.items()
        if slots.get(key) and slots[key].get("id") is not None
    }


def _outfit_slot_names(outfit: Optional[Dict[str, Any]]) -> Dict[str, str]:
    if not outfit:
        return {}
    slots = outfit.get("slots") or {}
    return {
        key: value for key, value in slots.items()
        if value and "none needed" not in value.lower()
    }


def _reply(
    conversation_id: str,
    intent: str,
    occasion: Optional[str],
    text: str,
    response_type: str,
    outfits: List[Dict[str, Any]],
    state: Dict[str, Any],
    trace: List[Dict[str, Any]],
    saved_outfit: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    return {
        "status": "success",
        "conversation_id": conversation_id,
        "agent_response": text,
        "response_type": response_type,
        "intent": intent,
        "occasion": occasion,
        "outfits": outfits,
        "conversation_state": json.loads(json.dumps(state)),
        "saved_outfit": saved_outfit,
        "readiness_confirmation": state.get("pending_readiness_confirmation"),
        "execution_trace": trace
    }


def run_voice_agent_pipeline(
    user_message: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    conversation_id: Optional[str] = None,
    selected_outfit_id: Optional[str] = None,
    request_id: Optional[str] = None,
    user_id: int = 1,
    context_outfit: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Process a typed or transcribed voice turn in persistent, single-user chat state."""
    if user_id != 1:
        raise PermissionError("This installation supports only its configured single user.")
    db.ensure_stylist_tables()
    conversation_id = conversation_id or str(uuid.uuid4())
    persisted = db.get_stylist_conversation(conversation_id, user_id)
    saved_state = persisted["state"] if persisted else {}
    messages = persisted["messages"] if persisted else []
    if context_outfit:
        saved_state = {
            **saved_state,
            "current_outfits": [context_outfit],
            "current_outfit_id": context_outfit.get("id"),
            "last_valid_outfit": context_outfit
        }
    if request_id and saved_state.get("last_request_id") == request_id:
        return saved_state.get("last_response") or _reply(
            conversation_id, "duplicate", saved_state.get("occasion"),
            "That message was already processed.", "text",
            saved_state.get("current_outfits", []), saved_state, [], None
        )

    user_message = (user_message or "").strip()
    turn_user_message = user_message
    readiness_answer_prefix = ""
    pending_readiness = saved_state.get("pending_readiness_confirmation")
    if pending_readiness and re.match(r"^(?:yes|yeah|yep)\b", user_message.lower()):
        item_id = str(pending_readiness["item_id"])
        item = db.get_clothing_item(item_id, user_id)
        if not item:
            raise ValueError("The garment waiting for readiness confirmation no longer exists.")
        updated = db.update_clothing_availability(
            item_id,
            user_id,
            "ready",
            item.get("ironing_status", "ready"),
            None,
            item.get("status_note")
        )
        if not updated:
            raise ValueError("The garment readiness confirmation could not be saved.")
        readiness_answer_prefix = f"Thanks, I marked {item['title']} ready and "
        user_message = pending_readiness["request"]
        saved_state["pending_readiness_confirmation"] = None
    elif pending_readiness and re.match(r"^(?:no|nope|not yet|not ready)\b", user_message.lower()):
        item_id = str(pending_readiness["item_id"])
        saved_state["excluded_item_ids"] = list(dict.fromkeys(
            list(saved_state.get("excluded_item_ids", [])) + [item_id]
        ))
        readiness_answer_prefix = f"Understood, {pending_readiness['title']} remains unavailable. "
        user_message = pending_readiness["request"]
        saved_state["pending_readiness_confirmation"] = None
    trace = [{
        "agent": "Conversation Orchestrator",
        "status": "started",
        "summary": "Loading conversation state and understanding the latest message."
    }]

    history = [
        {"role": turn.get("role", ""), "content": turn.get("content", "")}
        for turn in messages[-12:]
        if turn.get("role") in ("user", "assistant")
    ]
    if conversation_history and not history:
        history = conversation_history[-12:]

    state = {
        "occasion": saved_state.get("occasion"),
        "style_preference": saved_state.get("style_preference"),
        "required_colors": list(saved_state.get("required_colors", [])),
        "required_top_colors": list(saved_state.get("required_top_colors", [])),
        "preferred_colors": list(saved_state.get("preferred_colors", [])),
        "excluded_colors": list(saved_state.get("excluded_colors", [])),
        "required_garment_types": list(saved_state.get("required_garment_types", [])),
        "excluded_categories": list(saved_state.get("excluded_categories", [])),
        "excluded_item_ids": list(saved_state.get("excluded_item_ids", [])),
        "current_outfits": list(saved_state.get("current_outfits", [])),
        "current_outfit_id": selected_outfit_id or saved_state.get("current_outfit_id"),
        "last_valid_outfit": saved_state.get("last_valid_outfit"),
        "saved_outfit_ids": list(saved_state.get("saved_outfit_ids", [])),
        "availability_constraints": list(saved_state.get("availability_constraints", [])),
        "readiness_prompted_item_ids": list(saved_state.get("readiness_prompted_item_ids", [])),
        "last_request_id": request_id,
    }

    # ── Image-analysis context: note it for Gemini's conversational response ──
    # The image endpoint writes image_context into saved_state.  We use it only
    # to improve the Gemini/rule-based text response — we do NOT inject hard
    # color constraints (required_top_colors / required_colors) because those
    # make the pipeline fail when the wardrobe doesn't have exact color matches.
    # The pipeline already handles occasion-based outfit generation freely.
    _img_ctx = saved_state.get("image_context")
    if _img_ctx and _img_ctx.get("detected_color"):
        if not state.get("occasion"):
            state["occasion"] = "casual"
    selected = next(
        (outfit for outfit in state["current_outfits"] if outfit.get("id") == state["current_outfit_id"]),
        state["current_outfits"][0] if state["current_outfits"] else None
    )
    if selected:
        state["current_outfit_id"] = selected.get("id")

    # -----------------------------------------------------------------------
    # PRIMARY INTELLIGENCE: Gemini Conversational AI
    # Ask Gemini first — it understands full natural language context, complex
    # scenarios (hairstyles, non-standard occasions, multi-part requests, etc.)
    # -----------------------------------------------------------------------
    all_clothes = _get_user_clothes(user_id)
    gemini_result = None
    if _GEMINI_AVAILABLE:
        try:
            gemini_result = process_with_gemini(
                user_message=user_message,
                conversation_history=history,
                clothes=all_clothes,
                saved_state=saved_state,
            )
        except Exception as _gem_exc:
            print(f"[VoiceAgent] Gemini processing failed, using rule-based fallback: {_gem_exc}")
            gemini_result = None

    if gemini_result:
        trace.append({
            "agent": "Gemini Conversational AI",
            "status": "completed",
            "summary": f"Gemini understood request. needs_outfit_pipeline={gemini_result.get('needs_outfit_pipeline')}, occasion={gemini_result.get('occasion')}"
        })

        # Apply any Gemini-detected occasion / style updates to state
        # Use new_occasion flag to detect when occasion truly changed
        new_occasion = gemini_result.get("new_occasion") or gemini_result.get("occasion")
        current_saved_occasion = state.get("occasion")
        if new_occasion and new_occasion != current_saved_occasion:
            # NEW occasion detected — fully reset outfit state so stale outfits don't carry over
            state["occasion"] = new_occasion
            state["current_outfits"] = []
            state["current_outfit_id"] = None
            state["required_colors"] = []
            state["required_top_colors"] = []
            state["excluded_item_ids"] = []
            selected = None
        elif new_occasion:
            state["occasion"] = new_occasion
        if gemini_result.get("style_preference"):
            state["style_preference"] = gemini_result["style_preference"]

        # Handle Gemini-detected status updates (laundry, ironing, etc.)
        # Works both when LLM returns status_update AND when rule-based engine detects laundry intent
        gem_status = gemini_result.get("status_update")
        if gemini_result.get("response_type") == "status_update" and gem_status and gem_status.get("item_description"):
            pass  # handled below
        if gem_status and gem_status.get("item_description"):
            # Delegate to the legacy status update node via VoiceAgentState
            legacy_status_state = VoiceAgentState(
                user_id=user_id,
                user_message=user_message,
                conversation_history=history,
                intent="status_update",
                status_change={
                    "garment_description": gem_status["item_description"],
                    "availability_status": gem_status.get("new_status") if gem_status.get("new_status") in (
                        "to_wash", "in_wash", "drying", "ready", "missing", "damaged", "borrowed"
                    ) else None,
                    "ironing_status": gem_status.get("new_status") if gem_status.get("new_status") in (
                        "needs_ironing", "being_ironed"
                    ) else None,
                },
                execution_trace=trace
            )
            legacy_status_state = wardrobe_retrieval_node(legacy_status_state)
            legacy_status_state = status_update_node(legacy_status_state)
            status_response_text = gemini_result["agent_response"]
            if legacy_status_state.status_update_result and legacy_status_state.status_update_result.get("success"):
                # Gemini's wording + actual confirmation
                status_response_text = (
                    gemini_result["agent_response"]
                    or f"Done! I've updated {gem_status['item_description']} status."
                )
            response = _reply(
                conversation_id, "status_update", state["occasion"],
                status_response_text, "status_update", [], state, trace
            )
            _persist_turn(conversation_id, user_id, turn_user_message, response, state, messages, request_id)
            return response

        # Handle general style advice, color questions, greetings, thanks — no outfit pipeline needed
        if not gemini_result.get("needs_outfit_pipeline") and gemini_result.get("response_type") in (
            "general_advice", "text", "clarification", "status_update"
        ):
            response_text = gemini_result["agent_response"]
            if not response_text:
                # Extra fallback for general questions
                response_text = answer_general_style_question(user_message, history, all_clothes)
            rtype = gemini_result.get("response_type", "text")
            response = _reply(
                conversation_id, "general_advice", state["occasion"],
                response_text, rtype, [], state, trace
            )
            _persist_turn(conversation_id, user_id, turn_user_message, response, state, messages, request_id)
            return response

        # Gemini says to run the outfit pipeline — carry over its interpretation
        # and let the rest of the pipeline handle outfit generation.
        # We mark gemini_response_text so it's used as the conversational prefix.
        _gemini_prefix = gemini_result.get("agent_response", "")
    else:
        _gemini_prefix = ""
        trace.append({
            "agent": "Gemini Conversational AI",
            "status": "skipped",
            "summary": "Gemini unavailable or failed — using rule-based parser."
        })

    # -----------------------------------------------------------------------
    # FALLBACK / OUTFIT PIPELINE: Rule-based understanding (existing code)
    # -----------------------------------------------------------------------
    parsed = _understand_stylist_message(user_message, saved_state)
    if parsed.selected_option and parsed.selected_option <= len(saved_state.get("current_outfits", [])):
        option = saved_state["current_outfits"][parsed.selected_option - 1]
        selected_outfit_id = option.get("id")
    trace.append({
        "agent": "Request Understanding",
        "status": "completed",
        "summary": f"Interpreted message as '{parsed.action}'"
    })

    did_not_wear = bool(re.search(
        r"\b(?:i did not wear|i didn't wear|i didnt wear|did not wear|didn't wear|didnt wear)\b",
        user_message.lower()
    ))
    confirms_worn = not did_not_wear and bool(re.search(
        r"\b(?:i wore|i have worn|i've worn|i put on)\b",
        user_message.lower()
    ))
    if did_not_wear or confirms_worn:
        weekday_id = datetime.now().strftime("%a").lower()[:3]
        scheduled_entries = db.get_weekday_outfits(user_id).get(weekday_id, [])
        is_planned_confirmation = bool(re.search(r"\bplanned\b|\bscheduled\b", user_message.lower()))
        current_context_outfit = next(
            (item for item in state["current_outfits"] if item.get("id") == state["current_outfit_id"]),
            state["current_outfits"][0] if state["current_outfits"] else None
        )
        scheduled_entry = next(
            (
                entry for entry in scheduled_entries
                if current_context_outfit and entry.get("outfit", {}).get("id") == current_context_outfit.get("id")
            ),
            None
        )
        if is_planned_confirmation and not scheduled_entry:
            message_text = user_message.lower()
            scheduled_entry = next(
                (
                    entry for entry in scheduled_entries
                    if entry.get("occasion")
                    and re.search(r"\b" + re.escape(entry["occasion"].lower()) + r"\b", message_text)
                ),
                None
            )
        if is_planned_confirmation and not scheduled_entry and len(scheduled_entries) == 1:
            scheduled_entry = scheduled_entries[0]
        if is_planned_confirmation and not scheduled_entry and len(scheduled_entries) > 1:
            occasions = ", ".join(entry.get("occasion", "Outfit") for entry in scheduled_entries)
            answer = f"There are several looks planned for today ({occasions}). Tell me which occasion you wore."
            response = _reply(conversation_id, "wear_confirmation", state["occasion"], answer, "clarification", [], state, trace)
            _persist_turn(conversation_id, user_id, turn_user_message, response, state, messages, request_id)
            return response
        outfit = scheduled_entry.get("outfit") if is_planned_confirmation and scheduled_entry else None
        if not outfit:
            outfit = current_context_outfit
        if not outfit and scheduled_entries:
            scheduled_entry = scheduled_entries[0] if len(scheduled_entries) == 1 else None
            outfit = scheduled_entry.get("outfit") if scheduled_entry else None
        if not outfit:
            answer = "I couldn't find a planned outfit to record for this conversation. Select or ask for an outfit first."
            response = _reply(conversation_id, "wear_confirmation", state["occasion"], answer, "clarification", [], state, trace)
        else:
            try:
                event = db.create_outfit_wear_event(
                    user_id,
                    outfit,
                    list(_slot_item_ids(outfit).values()),
                    datetime.now().date().isoformat(),
                    weekday_id if scheduled_entry and scheduled_entry.get("outfit", {}).get("id") == outfit.get("id") else None,
                    worn=confirms_worn
                )
                state["last_wear_event_id"] = event["id"]
                if confirms_worn:
                    answer = (
                        "Thanks for confirming. I recorded that you wore this outfit. "
                        "Please answer the laundry check shown in the app; no garment will be marked for laundry until you confirm it."
                    )
                    response_type = "wear_reminder"
                else:
                    answer = "Got it — I recorded that you didn't wear this outfit. No garments were marked as worn or sent to laundry."
                    response_type = "text"
                if event.get("duplicate"):
                    answer = "This outfit already has a wear check recorded for today, so I didn't create a duplicate reminder."
                    response_type = "text"
                response = _reply(conversation_id, "wear_confirmation", state["occasion"], answer, response_type, [], state, trace)
            except (ValueError, sqlite3.Error) as exc:
                answer = f"I couldn't save the wear confirmation, so no laundry status was changed: {exc}"
                response = _reply(conversation_id, "wear_confirmation", state["occasion"], answer, "error", [], state, trace)
        _persist_turn(conversation_id, user_id, turn_user_message, response, state, messages, request_id)
        return response

    legacy_state = VoiceAgentState(
        user_id=user_id,
        user_message=user_message,
        conversation_history=history,
        constraints=state["availability_constraints"],
        execution_trace=trace
    )
    legacy_state = intent_understanding_node(legacy_state)
    if legacy_state.intent in ("status_update", "availability_query"):
        legacy_state = wardrobe_retrieval_node(legacy_state)
        response_outfits = []
        response_type = legacy_state.response_type
        response_text = legacy_state.agent_response
        if legacy_state.intent == "status_update":
            legacy_state = status_update_node(legacy_state)
            response_type = legacy_state.response_type
            response_text = legacy_state.agent_response
            state["last_status_update"] = legacy_state.status_update_result
            updated_item = (legacy_state.status_update_result or {}).get("item")
            unavailable_now = bool(updated_item) and (
                updated_item.get("availability_status") not in ("ready", "available")
                or updated_item.get("ironing_status", "ready") != "ready"
            )
            affected_outfits = [
                outfit for outfit in state["current_outfits"]
                if updated_item and str(updated_item["id"]) in set(_slot_item_ids(outfit).values())
            ]
            if unavailable_now and affected_outfits:
                changed_item_id = str(updated_item["id"])
                for saved_message in messages:
                    if saved_message.get("role") != "assistant":
                        continue
                    for saved_outfit in saved_message.get("outfits", []):
                        if changed_item_id in set(_slot_item_ids(saved_outfit).values()):
                            saved_outfit["availabilityWarning"] = (
                                f"{updated_item['title']} is now marked {updated_item.get('availability_status') or updated_item.get('ironing_status')}."
                            )
                selected_affected = next(
                    (outfit for outfit in affected_outfits if outfit.get("id") == state.get("current_outfit_id")),
                    affected_outfits[0]
                )
                locked_item_ids = [
                    item_id for item_id in _slot_item_ids(selected_affected).values()
                    if item_id != changed_item_id
                ]
                try:
                    replacement_response = run_multi_agent_pipeline({
                        "user_id": user_id,
                        "occasion": state.get("occasion") or "college",
                        "style_preference": state.get("style_preference") or "casual",
                        "clothes": _get_user_clothes(user_id),
                        "required_colors": state["required_colors"],
                        "required_top_colors": state["required_top_colors"],
                        "preferred_colors": state["preferred_colors"],
                        "excluded_colors": state["excluded_colors"],
                        "excluded_categories": state["excluded_categories"],
                        "required_garment_types": state["required_garment_types"],
                        "excluded_item_ids": list(dict.fromkeys(
                            state["excluded_item_ids"] + [changed_item_id]
                        )),
                        "locked_item_ids": locked_item_ids,
                        "excluded_outfit_signatures": state.get("excluded_outfit_signatures", []),
                    })
                    response_outfits = replacement_response.get("outfits", [])
                    if response_outfits:
                        state["current_outfits"] = response_outfits
                        state["current_outfit_id"] = response_outfits[0].get("id")
                        state["last_valid_outfit"] = response_outfits[0]
                        response_type = "outfit"
                        response_text = (
                            f"{updated_item['title']} is no longer ready to wear. I found a replacement look "
                            "while keeping your other selected pieces and active requirements where possible."
                        )
                    else:
                        state["current_outfits"] = []
                        state["current_outfit_id"] = None
                        state["last_valid_outfit"] = None
                        response_type = "no_match"
                        response_text = (
                            f"Your current look includes {updated_item['title']}, which is no longer ready to wear. "
                            "I couldn't find a valid replacement that preserves your other selected pieces and requirements, "
                            "so I won't treat that look as ready."
                        )
                except Exception as exc:
                    state["current_outfits"] = []
                    state["current_outfit_id"] = None
                    state["last_valid_outfit"] = None
                    response_type = "error"
                    response_text = (
                        f"The status was saved, but I couldn't revalidate the current outfit: {exc}. "
                        "The previous look is marked unavailable and should not be worn as-is."
                    )
        else:
            legacy_state = availability_query_node(legacy_state)
        response = _reply(
            conversation_id, legacy_state.intent, state["occasion"],
            response_text, response_type, response_outfits,
            state, legacy_state.execution_trace
        )
        _persist_turn(conversation_id, user_id, turn_user_message, response, state, messages, request_id)
        return response

    if parsed.action == "clarify":
        answer = parsed.clarification or "Could you clarify what kind of event or outfit you mean?"
        response = _reply(conversation_id, "clarification", state["occasion"], answer, "clarification", [], state, trace)
        _persist_turn(conversation_id, user_id, turn_user_message, response, state, messages, request_id)
        return response
    if parsed.action == "select":
        if not selected:
            answer = "I couldn't find that option in this conversation. Ask me for an outfit to get new choices."
            response = _reply(conversation_id, "selection", state["occasion"], answer, "clarification", [], state, trace)
        else:
            answer = f"Selected {parsed.selected_option or 'your'} outfit option for {state['occasion']}."
            response = _reply(conversation_id, "selection", state["occasion"], answer, "outfit", [selected], state, trace)
        _persist_turn(conversation_id, user_id, turn_user_message, response, state, messages, request_id)
        return response

    if parsed.action == "new":
        state["current_outfits"] = []
        state["current_outfit_id"] = None
        state["last_valid_outfit"] = None
        state["excluded_item_ids"] = []
    if parsed.occasion:
        state["occasion"] = parsed.occasion
        state["current_outfits"] = []
        state["current_outfit_id"] = None
        selected = None
    if parsed.style_preference:
        state["style_preference"] = parsed.style_preference
    if parsed.required_colors:
        state["required_colors"] = list(dict.fromkeys(parsed.required_colors))
    if parsed.required_top_colors:
        state["required_top_colors"] = list(dict.fromkeys(parsed.required_top_colors))
        state["required_colors"] = [
            color for color in state["required_colors"]
            if color not in state["required_top_colors"]
        ]
    state["preferred_colors"] = list(dict.fromkeys(state["preferred_colors"] + parsed.preferred_colors))
    state["excluded_colors"] = list(dict.fromkeys(state["excluded_colors"] + parsed.excluded_colors))
    if parsed.required_garment_types:
        if re.search(r"\binstead\b", user_message.lower()):
            state["required_garment_types"] = list(dict.fromkeys(parsed.required_garment_types))
        else:
            state["required_garment_types"] = list(dict.fromkeys(
                state["required_garment_types"] + parsed.required_garment_types
            ))
    state["excluded_categories"] = list(dict.fromkeys(state["excluded_categories"] + parsed.excluded_categories))
    if parsed.ready_to_wear_only:
        state["availability_constraints"] = list(dict.fromkeys(
            state["availability_constraints"] + ["ready_to_wear_only"]
        ))
    elif re.search(
        r"\b(?:don't|dont|do not|no longer|remove|relax|clear)\b.{0,35}\bready(?:[- ]to[- ]wear)?\b",
        user_message.lower()
    ):
        state["availability_constraints"] = [
            constraint for constraint in state["availability_constraints"]
            if constraint != "ready_to_wear_only"
        ]
    if re.search(r"\b(include|allow|with)\s+(the\s+)?bag\b|\bbag\s+is\s+(okay|fine)\b", user_message.lower()):
        state["excluded_categories"] = [category for category in state["excluded_categories"] if category != "bags"]
    if re.search(r"\b(no longer|don't|dont|do not|remove|clear|relax)\b.{0,35}\b(white|black|blue|color|colour)\b", user_message.lower()) or re.search(
        r"\b(any|no preference)\b.{0,20}\bcolors?\b|\bcolors?\b.{0,20}\b(any|no preference)\b",
        user_message.lower()
    ):
        state["required_colors"] = []
    if re.search(r"\b(allow|include|wear|use)\b.{0,30}\b(white|black|blue|navy|red|maroon|green|pink|purple|yellow|orange|brown|beige|grey|gray|gold|silver|cream)\b", user_message.lower()):
        state["excluded_colors"] = [
            color for color in state["excluded_colors"]
            if not re.search(r"\b" + re.escape(color) + r"\b", user_message.lower())
        ]
    if re.search(r"\b(no longer|don't|dont|do not|remove|clear|relax|instead of|not)\b.{0,35}\b(one[- ]piece|dress)\b", user_message.lower()):
        state["required_garment_types"] = []

    # Resolve simple garment references against the current outfit or actual wardrobe.
    # all_clothes was already fetched above for Gemini context; reuse it here.
    clothes = all_clothes
    full_clothes = clothes
    if "ready_to_wear_only" in state["availability_constraints"]:
        clothes = [
            item for item in clothes
            if item.get("availability_status", "ready") in ("ready", "available")
            and item.get("ironing_status", "ready") == "ready"
        ]
    locked_ids: List[str] = []
    excluded_item_ids = list(state["excluded_item_ids"])
    allow_match = re.search(
        r"\b(?:include|allow|use|wear|with|bring back)\s+(?:(?:the|my|those|these|any)\s+)?"
        r"(?P<item>[a-z][a-z -]*?)(?:\s+(?:now|again|instead|please)\b|[.,!?]|$)",
        user_message.lower()
    )
    if allow_match:
        allowed_words = [
            word for word in re.findall(r"[a-z]+", allow_match.group("item"))
            if word not in {"today", "tomorrow", "clothes", "items", "outfit", "look"}
        ]
        if allowed_words:
            allowed_ids = {
                str(item.get("id")) for item in full_clothes
                if _item_matches_description(item, allowed_words)
            }
            excluded_item_ids = [
                item_id for item_id in excluded_item_ids if item_id not in allowed_ids
            ]
    for item in full_clothes:
        for excluded_item in parsed.excluded_items:
            words = [
                word for word in re.findall(r"[a-z_]+", excluded_item.lower())
                if word not in {"the", "a", "an", "my", "those", "these", "any", "today", "tomorrow", "please", "clothes", "clothing", "items", "outfit"}
            ]
            if words and _item_matches_description(item, words):
                item_id = str(item.get("id"))
                if item_id not in excluded_item_ids:
                    excluded_item_ids.append(item_id)
    state["excluded_item_ids"] = excluded_item_ids
    target_slot = parsed.target_slot
    if parsed.action in ("modify", "replace", "remove") and target_slot and selected:
        slot_ids = _slot_item_ids(selected)
        if target_slot in parsed.keep_slots:
            locked_ids = [slot_ids[target_slot]]
        else:
            locked_ids = [item_id for category, item_id in slot_ids.items() if category != target_slot]
        if target_slot in slot_ids and target_slot not in parsed.keep_slots:
            excluded_item_ids.append(slot_ids[target_slot])
    if parsed.keep_slots and selected:
        slot_ids = _slot_item_ids(selected)
        locked_ids = [
            item_id for category, item_id in slot_ids.items()
            if category in parsed.keep_slots
        ]
        locked_ids.extend(
            item_id for category, item_id in slot_ids.items()
            if category not in parsed.keep_slots and category != target_slot
        )
        if target_slot in slot_ids and target_slot not in parsed.keep_slots:
            excluded_item_ids.append(slot_ids[target_slot])

    if parsed.action == "modify" and selected and parsed.excluded_categories and not target_slot:
        locked_ids = [
            item_id for category, item_id in _slot_item_ids(selected).items()
            if category not in parsed.excluded_categories
        ]

    # "Keep the same trousers" without naming a replacement slot locks the current bottom.
    if parsed.action == "modify" and selected and not target_slot and parsed.keep_slots:
        locked_ids = [
            item_id for category, item_id in _slot_item_ids(selected).items()
            if category in parsed.keep_slots or category != "bottoms"
        ]

    state["excluded_item_ids"] = list(dict.fromkeys(excluded_item_ids))
    if parsed.action == "another":
        state["current_outfits"] = state["current_outfits"] or ([selected] if selected else [])
        excluded_signatures = [_outfit_signature(outfit) for outfit in state["current_outfits"]]
        locked_ids = []
    else:
        excluded_signatures = []

    if parsed.action == "save":
        target_id = selected_outfit_id or state.get("current_outfit_id")
        outfit_to_save = next(
            (outfit for outfit in state["current_outfits"] if outfit.get("id") == target_id),
            selected
        )
        if not outfit_to_save:
            text = "There isn't a validated outfit in this conversation to save yet."
            response = _reply(conversation_id, "save", state["occasion"], text, "text", [], state, trace)
        else:
            saved = db.save_stylist_outfit(
                str(outfit_to_save["id"]), user_id, conversation_id, outfit_to_save
            )
            state["saved_outfit_ids"] = list(dict.fromkeys(state["saved_outfit_ids"] + [saved["id"]]))
            text = f"Saved “{saved['title']}” to your looks."
            response = _reply(conversation_id, "save", state["occasion"], text, "saved", [], state, trace, saved)
        _persist_turn(conversation_id, user_id, turn_user_message, response, state, messages, request_id)
        return response

    if parsed.action == "modify" and not selected and not parsed.occasion:
        text = "I don't have a current outfit to modify yet. Tell me the occasion and I'll find one from your wardrobe."
        response = _reply(conversation_id, "modification", state["occasion"], text, "clarification", [], state, trace)
        _persist_turn(conversation_id, user_id, turn_user_message, response, state, messages, request_id)
        return response

    # Non-styling voice commands retain the existing status/availability handlers.
    if not state["occasion"]:
        # Use gemini's detected occasion if available, otherwise fall back to legacy parser result
        state["occasion"] = (gemini_result.get("occasion") if gemini_result else None) or legacy_state.occasion or "casual"
    if not state["style_preference"]:
        state["style_preference"] = (gemini_result.get("style_preference") if gemini_result else None) or legacy_state.style_preference or "casual"
    constraints_changed = (
        parsed.required_colors or parsed.excluded_colors
        or parsed.required_top_colors or parsed.required_garment_types
        or parsed.ready_to_wear_only
    )
    if constraints_changed and parsed.action == "modify":
        locked_ids = []
        selected = None

    # When Gemini says outfit pipeline needed, don't block on ready_to_wear_only
    # unless user explicitly asked for it. This allows showing outfits even when
    # some items are in laundry — the pipeline filters only what's needed.
    if gemini_result and gemini_result.get("needs_outfit_pipeline") and "ready_to_wear_only" not in state["availability_constraints"]:
        # Use all available clothes (don't filter by laundry status)
        clothes_for_pipeline = all_clothes
    else:
        clothes_for_pipeline = clothes

    current = VoiceAgentState(
        user_id=user_id,
        user_message=user_message,
        conversation_history=history,
        intent="modification" if parsed.action in ("modify", "replace", "remove", "another") else "outfit_request",
        occasion=state["occasion"],
        style_preference=state["style_preference"] or (gemini_result.get("style_preference") if gemini_result else None) or "casual",
        required_colors=state["required_colors"],
        required_top_colors=state["required_top_colors"],
        preferred_colors=state["preferred_colors"],
        excluded_colors=state["excluded_colors"],
        required_garment_types=state["required_garment_types"],
        excluded_categories=state["excluded_categories"],
        excluded_item_ids=list(dict.fromkeys(excluded_item_ids)),
        locked_item_ids=locked_ids,
        excluded_outfit_signatures=excluded_signatures,
        clothes=[WardrobeItem(**item) for item in clothes_for_pipeline],
        filtered_clothes=[WardrobeItem(**item) for item in clothes_for_pipeline],
        execution_trace=trace
    )
    current = outfit_request_node(current)
    new_outfits = current.recommended_outfits
    if new_outfits:
        state["current_outfits"] = new_outfits
        state["current_outfit_id"] = new_outfits[0].get("id")
        state["last_valid_outfit"] = new_outfits[0]
        response_type = "outfit"
        # Use Gemini's rich conversational answer if available, otherwise default message
        if _gemini_prefix and parsed.action not in ("modify", "replace", "remove", "another"):
            answer = readiness_answer_prefix + _gemini_prefix
        else:
            answer = readiness_answer_prefix + f"here are {len(new_outfits)} wardrobe-checked option{'s' if len(new_outfits) != 1 else ''} for {state['occasion']}."
        if (
            parsed.action in ("modify", "replace", "remove")
            and selected and (target_slot or parsed.keep_slots)
        ):
            answer = "Updated just the requested part of your outfit while keeping the other selected pieces."
        elif parsed.action == "modify":
            answer = "I refreshed the outfit using your updated preferences and active requirements."
        elif parsed.action == "another":
            answer = "Here is another option that keeps your active requirements."
    elif current.response_type == "error":
        response_type = "error"
        answer = current.agent_response or "I couldn't complete that outfit update. Your previous outfit is unchanged."
        state["current_outfits"] = saved_state.get("current_outfits", [])
        state["current_outfit_id"] = saved_state.get("current_outfit_id")
    else:
        response_type = "no_match"
        # Give a helpful response — don't just blame laundry
        occasion_label = state.get("occasion") or "your occasion"
        if "ready_to_wear_only" in state["availability_constraints"]:
            unavailable_items = [
                item for item in full_clothes
                if item.get("availability_status", "ready") not in ("ready", "available")
                or item.get("ironing_status", "ready") != "ready"
            ]
            if unavailable_items:
                answer = (
                    f"I couldn't find an outfit for {occasion_label} using only your ready-to-wear clothes. "
                    f"{len(unavailable_items)} item(s) are in laundry/unavailable. "
                    "Try removing the 'ready only' filter or add more clothes to your wardrobe."
                )
            else:
                answer = f"I couldn't find a matching outfit for {occasion_label} in your wardrobe. Try adding more items or relaxing the requirements."
        else:
            answer = (
                f"I couldn't find a perfect outfit match for {occasion_label} in your wardrobe right now. "
                "Try adding more clothes, or let me know if you'd like to adjust the style or occasion."
            )
        if parsed.action in ("modify", "replace", "remove") and selected:
            answer = "I couldn't find a valid replacement that meets your requirements. Your previous validated outfit is still saved in this conversation."
            state["current_outfits"] = saved_state.get("current_outfits", [])
            state["current_outfit_id"] = saved_state.get("current_outfit_id")
        if not readiness_answer_prefix:
            deadline = _planned_wearing_deadline(user_message)
            prompted_ids = set(state["readiness_prompted_item_ids"])
            uncertain_items = []
            for item in full_clothes:
                if item.get("availability_status") not in {"to_wash", "in_wash", "drying"}:
                    continue
                if item.get("ironing_status", "ready") != "ready" or str(item.get("id")) in prompted_ids:
                    continue
                expected_text = item.get("expected_available_at")
                if not expected_text:
                    continue
                try:
                    expected_at = datetime.fromisoformat(expected_text.replace("Z", "+00:00"))
                    if expected_at.tzinfo is None:
                        expected_at = expected_at.astimezone()
                except ValueError:
                    continue
                if expected_at <= deadline:
                    uncertain_items.append(item)

            for item in uncertain_items[:5]:
                probe_clothes = [
                    {**wardrobe_item, "availability_status": "ready"}
                    if str(wardrobe_item.get("id")) == str(item.get("id"))
                    else wardrobe_item
                    for wardrobe_item in full_clothes
                ]
                probe_state = current.copy(deep=True, update={
                    "clothes": [WardrobeItem(**wardrobe_item) for wardrobe_item in probe_clothes],
                    "filtered_clothes": [WardrobeItem(**wardrobe_item) for wardrobe_item in probe_clothes],
                    "recommended_outfits": [],
                    "execution_trace": []
                })
                probe_state = outfit_request_node(probe_state)
                unavailable_item_id = str(item["id"])
                probe_used_item_ids = {
                    used_id
                    for outfit in probe_state.recommended_outfits
                    for used_id in _slot_item_ids(outfit).values()
                }
                if unavailable_item_id in probe_used_item_ids:
                    state["pending_readiness_confirmation"] = {
                        "item_id": str(item["id"]),
                        "title": item["title"],
                        "request": user_message
                    }
                    state["readiness_prompted_item_ids"] = list(dict.fromkeys(
                        state["readiness_prompted_item_ids"] + [str(item["id"])]
                    ))
                    answer = (
                        f"{item['title']} was estimated ready by the requested wearing time, but it is not confirmed ready. "
                        f"Is it ready to wear now? Reply yes or no."
                    )
                    response_type = "readiness_confirmation"
                    break
        if readiness_answer_prefix and response_type == "no_match":
            answer = readiness_answer_prefix + answer[0].lower() + answer[1:]
        elif readiness_answer_prefix and response_type == "outfit" and not answer.startswith(readiness_answer_prefix):
            answer = readiness_answer_prefix + answer[0].lower() + answer[1:]
        trace.append({
            "agent": "Final Constraint Validation",
            "status": "no_match",
            "summary": "No outfit passed every mandatory requirement; no outfit cards were returned."
        })

    response = _reply(
        conversation_id, current.intent, state["occasion"], answer, response_type,
        new_outfits, state, current.execution_trace
    )
    state["last_response"] = response
    _persist_turn(conversation_id, user_id, turn_user_message, response, state, messages, request_id)
    return response


def _persist_turn(
    conversation_id: str,
    user_id: int,
    user_message: str,
    response: Dict[str, Any],
    state: Dict[str, Any],
    messages: List[Dict[str, Any]],
    request_id: Optional[str]
):
    messages = list(messages)
    messages.append({
        "id": request_id or str(uuid.uuid4()),
        "role": "user",
        "content": user_message,
        "created_at": datetime.now().isoformat()
    })
    messages.append({
        "id": str(uuid.uuid4()),
        "role": "assistant",
        "content": response["agent_response"],
        "response_type": response["response_type"],
        "outfits": response.get("outfits", []),
        "saved_outfit": response.get("saved_outfit"),
        "readiness_confirmation": response.get("readiness_confirmation"),
        "created_at": datetime.now().isoformat()
    })
    response["messages"] = messages
    state["last_response"] = response
    db.save_stylist_conversation(conversation_id, user_id, state, messages)
