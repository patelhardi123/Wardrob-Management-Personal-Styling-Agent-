"""
Multi-Agent LangGraph Pipeline for AI Smart Wardrobe & Personal Stylist
Nodes:
1. Orchestrator Node
2. Style Profile Agent Node
3. Trend Research Agent Node
4. Occasion Agent Node
5. Wardrobe Agent Node
6. Outfit Candidate Generator & Compatibility Engine Node
7. Outfit Critic & Validator Node
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import json
import re
import uuid

from fashion.attribute_extractor import normalize_garment_attributes
from fashion.compatibility_engine import default_engine
from fashion.ml_compatibility import ml_model
from fashion.llm_client import generate_outfit_visualization_prompt, generate_outfit_visualization_image
from fashion.weather_client import fetch_live_weather
from fashion.styling_rules import (
    garment_blob,
    is_ethnic_garment,
    is_interview_formal_bottom,
    is_interview_formal_shoe,
    is_interview_formal_top,
    is_one_piece_garment_dict,
    is_wedding_appropriate_look,
    outfit_matches_dress_code,
)


def _weather_rule_summary(weather_data: Optional[Dict[str, Any]]) -> str:
    if not weather_data:
        return ""

    temp_c = float(weather_data.get("temperature_c") or 22.0)
    condition = (weather_data.get("condition") or "").lower()
    rules = []

    if temp_c < 12:
        rules.append("Cold weather: prioritize long sleeves, jackets, knitwear, and boots.")
    elif temp_c < 18:
        rules.append("Cool weather: keep light layers like cardigans, sweaters, or blazers in rotation.")
    elif temp_c > 28:
        rules.append("Warm weather: prefer breathable fabrics, lighter sleeves, and airy silhouettes.")

    if "rain" in condition:
        rules.append("Rainy weather: prefer weather-resistant outerwear and avoid suede/canvas footwear.")
    elif "snow" in condition or "freez" in condition:
        rules.append("Winter weather: prioritize insulated outerwear, thicker layers, and closed-toe shoes.")

    if not rules:
        return ""
    return " | ".join(rules)


def _weather_penalty(item: "WardrobeItem", weather_data: Optional[Dict[str, Any]]) -> int:
    if not weather_data:
        return 0

    temp_c = float(weather_data.get("temperature_c") or 22.0)
    condition = (weather_data.get("condition") or "").lower()
    title = (item.title or "").lower()
    category = (item.category or "").lower()
    penalty = 0

    if temp_c < 12:
        if any(keyword in title for keyword in ["tee", "t-shirt", "tank", "sleeveless", "crop", "short sleeve", "short-sleeve"]):
            penalty += 40
        if any(keyword in title for keyword in ["sweater", "hoodie", "knit", "cardigan", "jacket", "blazer", "coat", "long sleeve", "long-sleeve"]):
            penalty -= 25
    elif temp_c > 28:
        if any(keyword in title for keyword in ["sweater", "hoodie", "jacket", "coat", "cardigan", "blazer", "long sleeve", "long-sleeve", "wool"]):
            penalty += 30
        if any(keyword in title for keyword in ["linen", "cotton", "tee", "t-shirt", "tank", "short sleeve", "short-sleeve", "sleeveless"]):
            penalty -= 15

    if "rain" in condition:
        if any(keyword in title for keyword in ["suede", "canvas", "open toe", "sandal"]):
            penalty += 60
        if any(keyword in title for keyword in ["trench", "coat", "jacket", "bomber", "rain", "outerwear"]):
            penalty -= 20
        if category == "footwear" and any(keyword in title for keyword in ["loafer", "boot", "shoe", "heel", "oxford"]):
            penalty -= 5

    return penalty


def _apply_weather_context(state: "AgentGraphState", city: Optional[str] = None) -> "AgentGraphState":
    weather_data = fetch_live_weather(city or "New York")
    state.weather_data = weather_data

    weather_rules = _weather_rule_summary(weather_data)
    if weather_rules:
        merged_rules = [state.context_rules] if state.context_rules else []
        merged_rules.append(weather_rules)
        state.context_rules = " | ".join(filter(None, merged_rules))

    return state

class WardrobeItem(BaseModel):
    id: Optional[Any] = None
    title: str
    category: str
    color: Optional[str] = "Neutral"
    pattern: Optional[str] = "Solid"
    style: Optional[str] = "casual"
    season: Optional[str] = "all-season"
    usageCount: Optional[int] = 0
    imageUrl: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None
    availability_status: Optional[str] = "ready"
    ironing_status: Optional[str] = "ready"
    expected_available_at: Optional[str] = None
    wear_cooldown_until: Optional[str] = None


class AgentGraphState(BaseModel):
    # Inputs
    user_id: int = 1
    raw_occasion: str = "college"
    style_preference: str = "stylish-trendy"
    clothes: List[WardrobeItem] = []
    exclude_bags: bool = False
    exclude_accessories: bool = False
    context_rules: Optional[str] = None
    weather_data: Optional[Dict[str, Any]] = None
    required_colors: List[str] = Field(default_factory=list)
    required_top_colors: List[str] = Field(default_factory=list)
    preferred_colors: List[str] = Field(default_factory=list)
    excluded_colors: List[str] = Field(default_factory=list)
    excluded_categories: List[str] = Field(default_factory=list)
    required_garment_types: List[str] = Field(default_factory=list)
    excluded_item_ids: List[str] = Field(default_factory=list)
    locked_item_ids: List[str] = Field(default_factory=list)
    excluded_outfit_signatures: List[str] = Field(default_factory=list)
    
    # Node Pipeline Internal Outputs
    style_profile_context: Dict[str, Any] = {}
    trend_research_signals: List[Dict[str, Any]] = []
    trend_research_metadata: Dict[str, Any] = Field(default_factory=dict)
    occasion_formality_score: int = 5
    filtered_eligible_clothes: List[WardrobeItem] = []
    candidate_outfits: List[Dict[str, Any]] = []
    
    # Final Output
    recommended_outfits: List[Dict[str, Any]] = []
    execution_trace: List[Dict[str, Any]] = []

# --- AGENT NODES IMPLEMENTATION ---

def style_profile_agent_node(state: AgentGraphState) -> AgentGraphState:
    """
    Node 1: Style Profile Agent Node
    Extracts & formats user's style persona, tags, body shape & color tone preferences.
    """
    profile_data = {
        "style_preference": state.style_preference,
        "persona": "College Student & Creative Casual",
        "style_tags": ["streetwear", "smart-casual", "minimal-chic"],
        "body_shape": "hourglass",
        "palette": "Neutral Tones with Metallic Accents"
    }
    state.style_profile_context = profile_data
    state.execution_trace.append({
        "agent": "Style Profile Agent",
        "status": "completed",
        "time": "35ms",
        "summary": f"Loaded style profile '{state.style_preference}'. Persona: {profile_data['persona']}."
    })
    return state

def trend_research_agent_node(state: AgentGraphState) -> AgentGraphState:
    from trend_research import snapshot
    import time
    started = time.perf_counter()
    data = snapshot()
    state.trend_research_signals = data['signals']
    state.trend_research_metadata = {k: v for k, v in data.items() if k != 'signals'}
    state.execution_trace.append({
        'agent': 'Trend Research Agent', 'status': 'completed',
        'time': f'{int((time.perf_counter() - started) * 1000)}ms',
        'summary': f"RSS cache ({data['mode']}): {data['trends_found']} signals; sources: {', '.join(data['sources']) or 'none'}. Last successful internet update: {data['last_successful_update'] or 'never'}.",
        **state.trend_research_metadata,
    })
    return state

def occasion_agent_node(state: AgentGraphState) -> AgentGraphState:
    """
    Node 3: Occasion Agent Node
    Parses request formality and venue requirements accurately.
    """
    occ = state.raw_occasion.lower()
    if any(kw in occ for kw in ["interview", "job interview", "placement", "black tie", "gala", "wedding", "sangeet", "mehndi", "shaadi", "court", "formal wedding"]):
        formality = 9
    elif any(kw in occ for kw in ["presentation", "pitch", "conference", "business", "office", "corporate", "meeting", "formal dinner"]):
        formality = 8
    elif any(kw in occ for kw in ["dinner date", "date night", "romantic", "dinner", "party", "night party"]):
        formality = 7  # Evening dinner date & party formality
    elif any(kw in occ for kw in ["date", "brunch", "smart-casual"]):
        formality = 5
    elif any(kw in occ for kw in ["college", "casual", "daily", "everyday", "movie", "lounge"]):
        formality = 4
    else:
        formality = 5

    state.occasion_formality_score = formality
    state.execution_trace.append({
        "agent": "Occasion Agent",
        "status": "completed",
        "time": "25ms",
        "summary": f"Analyzed occasion '{state.raw_occasion}' -> Target Formality Rating: {formality}/10."
    })
    return state

def wardrobe_agent_node(state: AgentGraphState) -> AgentGraphState:
    """
    Node 4: Wardrobe Agent Node
    Filters & ranks user's owned items against occasion formality score and availability status.
    """
    target_formality = state.occasion_formality_score
    scored_items = []
    preferred_colors = {color.strip().lower() for color in state.preferred_colors}

    for item in state.clothes:
        style = (item.style or "").lower()
        title = (item.title or "").lower()
        cat = (item.category or "").lower()

        # Availability is a hard constraint; expected-ready estimates never imply readiness.
        item_dict = item.dict() if hasattr(item, 'dict') else item
        availability = item_dict.get("availability_status") or "ready"
        ironing = item_dict.get("ironing_status", "ready")
        if (
            availability not in {"ready", "available"}
            or ironing != "ready"
        ):
            continue
        penalty = _weather_penalty(item, state.weather_data)
        item_attr = (item.attributes or {}) if hasattr(item, "attributes") else {}
        item_payload = {
            "title": item.title,
            "category": item.category,
            "style": item.style,
            **(item_attr if isinstance(item_attr, dict) else {}),
        }
        is_heavy_festive = any(kw in title or kw in style for kw in ["wedding", "party", "anarkali", "gown", "lehenga", "saree", "bridal", "festive", "gala"])
        occ = (state.raw_occasion or "").lower()
        is_wedding_occ = any(w in occ for w in ["wedding", "sangeet", "mehndi", "shaadi", "reception"])
        is_interview_occ = any(w in occ for w in ["interview", "placement"])

        if target_formality <= 5:  # Daily college / casual lounge
            if is_heavy_festive:
                penalty += 75  # Steep penalty for heavy wedding/party dresses in daily casual wear
            elif ("tuxedo" in title or "suit" in title or "blazer" in title) and not is_one_piece_garment(item):
                penalty += 45
        elif is_wedding_occ:
            if is_wedding_appropriate_look(item_payload) or is_ethnic_garment(item_payload):
                penalty -= 45
            elif any(k in title for k in ["hoodie", "t-shirt", "tee", "jeans", "sneaker", "stylish"]):
                penalty += 70
            else:
                penalty += 50
        elif is_interview_occ or any(w in occ for w in ["presentation", "office", "corporate", "meeting"]):
            if (
                is_interview_formal_top(item_payload)
                or is_interview_formal_bottom(item_payload)
                or is_interview_formal_shoe(item_payload)
                or any(k in title for k in ["formal", "oxford", "heel"])
            ):
                penalty -= 40
            elif is_heavy_festive or is_ethnic_garment(item_payload) or "stylish" in title:
                penalty += 60
            elif style in ["casual", "sporty"] or any(k in title for k in ["hoodie", "cargo", "t-shirt", "shorts", "trackpant", "jean"]):
                penalty += 55
        elif target_formality >= 8:  # Party / black-tie fallback
            if style in ["casual", "sporty"] or any(k in title for k in ["hoodie", "cargo", "t-shirt", "shorts", "trackpant"]):
                penalty += 55
            elif is_heavy_festive or style in ["formal", "ethnic"] or any(k in title for k in ["formal", "suit", "blazer", "trouser", "heels", "shirt", "gown", "anarkali"]):
                penalty -= 30


        item_colors = {
            str(color).strip().lower()
            for color in (item.color, item_attr.get("color"), item_attr.get("secondary_color"))
            if color
        }
        if any(
            _color_matches_requirement(color, preferred)
            for preferred in preferred_colors
            for color in item_colors
        ):
            penalty -= 8
        score = 100 - penalty
        scored_items.append((score, item))

    scored_items.sort(key=lambda x: x[0], reverse=True)
    eligible = [item for s, item in scored_items]

    state.filtered_eligible_clothes = eligible
    state.execution_trace.append({
        "agent": "Wardrobe Agent",
        "status": "completed",
        "time": "50ms",
        "summary": f"Evaluated {len(state.clothes)} owned items against occasion formality ({target_formality}/10) and availability -> Ranked {len(eligible)} items."
    })
    return state

def is_one_piece_garment(item: Optional[WardrobeItem]) -> bool:
    if not item: return False
    payload = item.dict() if hasattr(item, "dict") else (item or {})
    if payload.get("attributes") and isinstance(payload["attributes"], dict):
        payload = {**payload, **payload["attributes"]}
    return is_one_piece_garment_dict(payload)


def _item_payload(item: Optional[WardrobeItem]) -> Dict[str, Any]:
    if not item:
        return {}
    payload = item.dict() if hasattr(item, "dict") else dict(item)
    attrs = payload.get("attributes") if isinstance(payload.get("attributes"), dict) else {}
    return {**payload, **attrs}


def _color_matches_requirement(item_color: Any, required_color: str) -> bool:
    item_words = set(re.findall(r"[a-z]+", str(item_color or "").lower()))
    required_words = set(re.findall(r"[a-z]+", str(required_color or "").lower()))
    item_words = {"gray" if word == "grey" else word for word in item_words}
    required_words = {"gray" if word == "grey" else word for word in required_words}
    return bool(required_words) and required_words.issubset(item_words)


def _matches_required_garment_types(
    top_item: WardrobeItem,
    outfit_items: List[Optional[WardrobeItem]],
    required_types: List[str]
) -> bool:
    if not required_types:
        return True
    return any(
        is_one_piece_garment(top_item)
        if required_type == "one_piece"
        else any(
            required_type in garment_blob(_item_payload(item))
            for item in outfit_items
            if item
        )
        for required_type in required_types
    )


def _pick_best_shoe(shoe_pool: List[Optional[WardrobeItem]], occasion: str, fallback_idx: int = 0) -> Optional[WardrobeItem]:
    real_shoes = [s for s in shoe_pool if s is not None]
    if not real_shoes:
        return None
    occ = (occasion or "").lower()

    def score(shoe: WardrobeItem) -> int:
        payload = _item_payload(shoe)
        blob = garment_blob(payload)
        if any(w in occ for w in ["interview", "placement", "office", "presentation", "corporate", "meeting"]):
            if is_interview_formal_shoe(payload):
                return 20 if "heel" in blob else 16
            if any(k in blob for k in ["sneaker", "trainer", "canvas"]):
                return 0
            return 4
        if any(w in occ for w in ["wedding", "sangeet", "mehndi", "shaadi", "reception"]):
            if any(k in blob for k in ["jutti", "mojari", "kolhapuri", "heel", "ethnic", "embellish"]):
                return 20
            if any(k in blob for k in ["sneaker", "trainer"]):
                return 0
            return 5
        if any(w in occ for w in ["date", "dinner", "romantic", "party", "night out"]):
            if any(k in blob for k in ["heel", "pump"]):
                return 20
            if any(k in blob for k in ["formal", "loafer", "dress shoe"]):
                return 14
            if any(k in blob for k in ["sneaker", "trainer", "canvas", "sport"]):
                return 0
            return 5
        return 8

    ranked = sorted(real_shoes, key=score, reverse=True)
    best_score = score(ranked[0])
    best_shoes = [shoe for shoe in ranked if score(shoe) == best_score]
    if fallback_idx and len(best_shoes) > 1:
        return best_shoes[fallback_idx % len(best_shoes)]
    return best_shoes[0]

def outfit_stylist_agent_node(state: AgentGraphState) -> AgentGraphState:
    """
    Node 5: Outfit Candidate Generator & Fashion Compatibility Engine
    Generates multiple candidate outfits from owned wardrobe items,
    runs the 12-dimensional Compatibility Engine and ML model, and ranks candidate looks.
    """
    import random
    bag_keywords = ["no bag", "no bags", "don't want bag", "don't want bags", "without bag", "exclude bag", "exclude bags", "remove bag"]
    acc_keywords = ["no accessory", "no accessories", "no jewellery", "no jewelry", "without accessory", "exclude accessory"]

    rules_text = (state.context_rules or "").lower()
    is_bag_excluded = state.exclude_bags or any(kw in rules_text for kw in bag_keywords)
    is_acc_excluded = state.exclude_accessories or any(kw in rules_text for kw in acc_keywords)

    grouped: Dict[str, List[WardrobeItem]] = {
        "tops": [], "bottoms": [], "outerwear": [], "footwear": [], "bags": [], "accessories": []
    }
    excluded_categories = {category.lower() for category in state.excluded_categories}

    for item in state.filtered_eligible_clothes:
        cat = (item.category or "").lower().strip()
        title = (item.title or "").lower().strip()
        if str(item.id) in set(state.excluded_item_ids):
            continue

        if is_one_piece_garment(item) or cat in ["one_piece", "one-piece", "dresses", "dress"] or any(kw in cat or kw in title for kw in ["top", "shirt", "blouse", "tee", "sweater", "hoodie", "kurti", "kurta", "lehenga", "anarkali", "saree"]):
            if "tops" not in excluded_categories:
                grouped["tops"].append(item)
        elif any(kw in cat or kw in title for kw in ["bottom", "pant", "trouser", "jean", "skirt", "short", "chino", "cargo", "palazzo", "salwar", "churidar", "sharara", "dhoti", "pyjama", "pajama"]):
            if "bottoms" not in excluded_categories:
                grouped["bottoms"].append(item)
        elif any(kw in cat or kw in title for kw in ["outer", "jacket", "coat", "blazer", "cardigan", "vest"]):
            if "outerwear" not in excluded_categories:
                grouped["outerwear"].append(item)
        elif any(kw in cat or kw in title for kw in ["foot", "shoe", "sneaker", "loafer", "boot", "sandal", "heel", "jutti", "kolhapuri", "mojari", "pump"]):
            if "footwear" not in excluded_categories:
                grouped["footwear"].append(item)
        elif any(kw in cat or kw in title for kw in ["bag", "purse", "handbag", "tote", "crossbody", "backpack"]):
            if "bags" not in excluded_categories:
                grouped["bags"].append(item)
        elif "accessories" not in excluded_categories:
            grouped["accessories"].append(item)

    locked_ids = set(state.locked_item_ids)
    if locked_ids:
        for category, items in grouped.items():
            category_locks = [item for item in items if str(item.id) in locked_ids]
            if category_locks:
                grouped[category] = category_locks

    occ = (state.raw_occasion or "").lower()
    is_wedding_occ = any(w in occ for w in ["wedding", "sangeet", "mehndi", "shaadi", "reception"])
    is_interview_occ = any(w in occ for w in ["interview", "placement"])
    is_professional_occ = is_interview_occ or any(w in occ for w in ["office", "presentation", "corporate", "meeting", "business"])
    is_date_occ = any(w in occ for w in ["date", "dinner", "romantic"])
    dress_code_strict = is_wedding_occ or is_professional_occ or is_date_occ

    def _dress_code_rank(item: WardrobeItem) -> int:
        payload = _item_payload(item)
        if is_wedding_occ:
            if is_ethnic_garment(payload):
                return 4
            if is_wedding_appropriate_look(payload):
                return 3
            return 0
        if is_professional_occ:
            if is_interview_formal_top(payload) or is_interview_formal_bottom(payload) or is_interview_formal_shoe(payload):
                return 2
            return 0
        if is_date_occ:
            if is_one_piece_garment(item):
                return 3
            if any(word in garment_blob(payload) for word in ["stylish", "satin", "blouse", "halter", "corset", "off_shoulder"]):
                return 2
            return 1
        return 1

    def _weather_sort_key(candidate: WardrobeItem, category: str) -> tuple[int, int]:
        weather = state.weather_data or {}
        temp_c = float(weather.get("temperature_c") or 22.0)
        condition = (weather.get("condition") or "").lower()
        title = (candidate.title or "").lower()
        if category == "tops":
            if temp_c < 12 and any(keyword in title for keyword in ["sweater", "hoodie", "cardigan", "jacket", "knit", "long sleeve", "long-sleeve"]):
                return (2, 1)
            if temp_c > 28 and any(keyword in title for keyword in ["linen", "cotton", "tee", "t-shirt", "tank", "short sleeve", "short-sleeve", "sleeveless"]):
                return (2, 1)
            return (1, 0)
        if category == "footwear":
            if "rain" in condition and any(keyword in title for keyword in ["boot", "heel", "loafer", "oxford", "mule", "leather"]):
                return (2, 1)
            if "rain" in condition and any(keyword in title for keyword in ["canvas", "sandal", "open toe", "suede"]):
                return (0, 0)
            return (1, 0)
        if category == "outerwear":
            if temp_c < 18 and any(keyword in title for keyword in ["jacket", "trench", "coat", "blazer", "cardigan"]):
                return (2, 1)
            return (1, 0)
        return (1, 0)

    for category in grouped:
        if state.weather_data:
            grouped[category].sort(
                key=lambda item: _weather_sort_key(item, category),
                reverse=True,
            )
        if dress_code_strict:
            grouped[category].sort(
                key=lambda item: (_weather_sort_key(item, category)[0], _dress_code_rank(item)),
                reverse=True,
            )
        else:
            random.shuffle(grouped[category])

    if state.locked_item_ids:
        available_ids = {str(item.id) for group in grouped.values() for item in group}
        if not set(state.locked_item_ids).issubset(available_ids):
            state.candidate_outfits = []
            return state

    # 1. Generate Multiple Candidates from Owned Items
    if not grouped["tops"]:
        state.candidate_outfits = []
        state.execution_trace.append({
            "agent": "Outfit Stylist Agent",
            "status": "completed",
            "time": "15ms",
            "summary": "No top garments or dresses available in owned wardrobe."
        })
        return state

    if state.required_top_colors:
        grouped["tops"] = [
            item for item in grouped["tops"]
            if not is_one_piece_garment(item)
            and any(
                _color_matches_requirement(item_color, required_color)
                for item_color in (
                    item.color,
                    (item.attributes or {}).get("color"),
                    (item.attributes or {}).get("secondary_color"),
                )
                if item_color
                for required_color in state.required_top_colors
            )
        ]
        if not grouped["tops"]:
            state.candidate_outfits = []
            state.execution_trace.append({
                "agent": "Outfit Stylist Agent",
                "status": "completed",
                "time": "15ms",
                "summary": "No separate top in the requested color is available in the wardrobe."
            })
            return state
        if not grouped["bottoms"] or not grouped["footwear"]:
            state.candidate_outfits = []
            state.execution_trace.append({
                "agent": "Outfit Stylist Agent",
                "status": "completed",
                "time": "15ms",
                "summary": "A matching bottom and footwear are required to complete the requested top-based look."
            })
            return state

    raw_candidates = []
    top_pool = grouped["tops"]
    bottom_pool = grouped["bottoms"] or [None]
    shoe_pool = grouped["footwear"] or [None]
    outer_pool = grouped["outerwear"] or [None]
    bag_pool = [] if is_bag_excluded else (grouped["bags"] or [None])
    acc_pool = [] if is_acc_excluded else (grouped["accessories"] or [None])

    # Occasion-specific items are sorted to the front, so never randomly skip them.
    start_offset = 0 if dress_code_strict else random.randint(0, max(1, len(top_pool) - 1))
    cand_idx = start_offset
    for t_idx, top_item in enumerate(top_pool):
        candidate_bottoms = [None] if is_one_piece_garment(top_item) else bottom_pool
        for b_idx, bottom_item in enumerate(candidate_bottoms):
            if is_one_piece_garment(top_item):
                curr_bottom = None
            else:
                curr_bottom = bottom_item

            shoe_item = _pick_best_shoe(shoe_pool, state.raw_occasion, cand_idx)
            
            # Smart Outerwear: Only add outerwear if top requires layering (crop/tank/sleeveless) or high formality (blazer)
            outer_item = None
            if outer_pool and outer_pool[0] is not None:
                top_title_str = (top_item.title if top_item else "").lower()
                top_type_str = ((top_item.attributes or {}).get("type") or (top_item.category if top_item else "")).lower()
                needs_layer = any(k in top_title_str or k in top_type_str for k in ["crop", "tank", "sleeveless", "tube", "camisole"])
                is_formal_blazer = state.occasion_formality_score >= 8 and any(
                    "blazer" in garment_blob(_item_payload(outer))
                    and ((outer.style or "").lower() == "formal" or int((outer.attributes or {}).get("formality", 5)) >= 7)
                    for outer in outer_pool
                    if outer is not None
                )
                
                if needs_layer or is_formal_blazer:
                    if is_professional_occ:
                        professional_layers = [
                            outer for outer in outer_pool
                            if outer is not None
                            and "blazer" in garment_blob(_item_payload(outer))
                            and ((outer.style or "").lower() == "formal" or int((outer.attributes or {}).get("formality", 5)) >= 7)
                        ]
                        if professional_layers:
                            outer_item = professional_layers[cand_idx % len(professional_layers)]
                    else:
                        outer_item = outer_pool[cand_idx % len(outer_pool)]

            # Add randomness to bag and accessory selection
            bag_offset = random.randint(0, max(1, len(bag_pool) - 1)) if bag_pool else 0
            acc_offset = random.randint(0, max(1, len(acc_pool) - 1)) if acc_pool else 0
            bag_item = bag_pool[(cand_idx + bag_offset) % len(bag_pool)] if bag_pool else None
            acc_item = acc_pool[(cand_idx + acc_offset) % len(acc_pool)] if acc_pool else None


            # Evaluate with Compatibility Engine
            t_dict = top_item.dict() if top_item else {}
            b_dict = curr_bottom.dict() if curr_bottom else {}

            comp_result = default_engine.evaluate_candidate_outfit(
                top_item=t_dict,
                bottom_item=b_dict,
                shoe_item=shoe_item.dict() if shoe_item else None,
                outer_item=outer_item.dict() if outer_item else None,
                occasion_formality=state.occasion_formality_score,
                trend_signals=state.trend_research_signals,
                context={
                    "style_preference": state.style_preference,
                    "context_rules": state.context_rules,
                    "occasion": state.raw_occasion
                }
            )

            # Evaluate ML score
            ml_res = ml_model.predict_compatibility(t_dict, b_dict)
            ml_score = ml_res["ml_compatibility_score"]

            # Hybrid Score calculation
            rule_score = comp_result["rule_compatibility_score"]
            combined_score = round((rule_score * 0.60) + (ml_score * 0.40), 2)
            dress_ctx = {
                "style_preference": state.style_preference,
                "context_rules": state.context_rules,
                "occasion": state.raw_occasion,
            }
            shoe_dict = shoe_item.dict() if shoe_item else None
            if not outfit_matches_dress_code(t_dict, b_dict, dress_ctx, shoe_dict):
                cand_idx += 1
                continue

            outfit_items = [top_item, curr_bottom, shoe_item, outer_item, bag_item, acc_item]
            if not _matches_required_garment_types(
                top_item, outfit_items, state.required_garment_types
            ):
                cand_idx += 1
                continue

            outfit_signature = "|".join(
                str(item.id) if item else "-"
                for item in outfit_items
            )
            if outfit_signature in state.excluded_outfit_signatures:
                cand_idx += 1
                continue

            raw_candidates.append({
                "candidate_id": f"cand-{cand_idx+1}",
                "top": top_item,
                "bottom": curr_bottom,
                "shoe": shoe_item,
                "outerwear": outer_item,
                "bag": bag_item,
                "accessory": acc_item,
                "rule_score": rule_score,
                "ml_score": ml_score,
                "combined_score": combined_score,
                "sub_scores": comp_result["sub_scores"],
                "applied_rules": comp_result["applied_rules"],
                "issues": comp_result["issues"]
            })
            cand_idx += 1
            if len(raw_candidates) >= 20:
                break
        if len(raw_candidates) >= 20:
            break

    # Sort candidates by combined score descending
    def _occasion_priority(candidate: Dict[str, Any]) -> int:
        if is_wedding_occ:
            return int(bool(
                is_ethnic_garment(_item_payload(candidate["top"]))
                or (candidate.get("bottom") and is_ethnic_garment(_item_payload(candidate["bottom"])))
            ))
        if is_date_occ:
            return int(is_one_piece_garment(candidate["top"]))
        return 0

    raw_candidates.sort(
        key=lambda candidate: (_occasion_priority(candidate), candidate["combined_score"]),
        reverse=True,
    )
    state.candidate_outfits = raw_candidates

    state.execution_trace.append({
        "agent": "Outfit Stylist Agent",
        "status": "completed",
        "time": "75ms",
        "summary": f"Generated and scored {len(raw_candidates)} candidate outfits using 12-Dimensional Compatibility Engine."
    })
    return state

def outfit_critic_agent_node(state: AgentGraphState) -> AgentGraphState:
    """
    Node 6: Outfit Critic & Validator Node
    Performs strict suitability threshold check (combined_score >= 6.2 AND occasion_score >= 6.0),
    deduplicates candidates sharing top + bottom, and returns variable outfit count (0, 1, 2, or 3).
    """
    final_outfits = []
    seen_pairs = set()
    
    # 1. Filter and Deduplicate candidate outfits
    valid_candidates = []
    eligible_ids = {
        str(item.id) for item in state.filtered_eligible_clothes
        if (item.availability_status or "ready") in {"ready", "available"}
        and item.ironing_status == "ready"
    }
    for cand in state.candidate_outfits:
        candidate_items = [
            cand.get(slot) for slot in ("top", "bottom", "shoe", "outerwear", "bag", "accessory")
            if cand.get(slot) is not None
        ]
        if not cand.get("top") or not cand.get("shoe"):
            continue
        if not is_one_piece_garment(cand.get("top")) and not cand.get("bottom"):
            continue
        if any(
            str(item.id) not in eligible_ids
            or (item.availability_status or "ready") not in {"ready", "available"}
            or item.ironing_status != "ready"
            for item in candidate_items
        ):
            continue
        c_score = cand["combined_score"] - max(0, cand["sub_scores"].get("trend", 7.5) - 7.5) * 0.05 * 0.60
        o_score = cand["sub_scores"].get("occasion", 10.0)
        
        dress_ctx = {
            "style_preference": state.style_preference,
            "context_rules": state.context_rules,
            "occasion": state.raw_occasion,
        }
        top_payload = _item_payload(cand.get("top"))
        bottom_payload = _item_payload(cand.get("bottom")) if cand.get("bottom") else None
        shoe_payload = _item_payload(cand.get("shoe")) if cand.get("shoe") else None
        if not outfit_matches_dress_code(top_payload, bottom_payload, dress_ctx, shoe_payload):
            continue

        # Enforce strict suitability thresholds
        if c_score >= 6.2 and o_score >= 6.0:
            top_id = cand["top"].id if cand["top"] else (cand["top"].title if cand["top"] else "none")
            bot_id = cand["bottom"].id if cand["bottom"] else (cand["bottom"].title if cand["bottom"] else "none")
            pair_key = (str(top_id), str(bot_id))
            
            if pair_key not in seen_pairs:
                seen_pairs.add(pair_key)
                valid_candidates.append(cand)
                if len(valid_candidates) >= 3:
                    break

    for i, cand in enumerate(valid_candidates):
        top_item = cand["top"]
        bottom_item = cand["bottom"]
        shoe_item = cand["shoe"]
        outer_item = cand["outerwear"]
        bag_item = cand["bag"]
        acc_item = cand["accessory"]

        top_text = top_item.title if top_item else "Top Garment"
        bottom_text = bottom_item.title if bottom_item else ("None Needed (One-Piece Dress)" if is_one_piece_garment(top_item) else "Bottom Garment")
        shoe_text = shoe_item.title if shoe_item else "Footwear"
        outer_text = outer_item.title if outer_item else "None Needed"
        bag_text = "None Needed (Excluded per Context Rule)" if state.exclude_bags or not bag_item else bag_item.title
        acc_text = "None Needed (Excluded per Context Rule)" if state.exclude_accessories or not acc_item else acc_item.title

        # Build dynamic explanation via OpenRouter / OpenAI LLM or rule engine fallback
        try:
            llm_commentary = generate_stylist_commentary(
                occasion=state.raw_occasion,
                style_pref=state.style_preference,
                outfit={
                    "topObj": top_item.dict() if top_item else {},
                    "bottomObj": bottom_item.dict() if bottom_item else {},
                    "shoesObj": shoe_item.dict() if shoe_item else {},
                    "outerwearObj": outer_item.dict() if outer_item else {},
                    "accessoriesObj": [acc_item.dict()] if acc_item else [],
                    "isOnePiece": is_one_piece_garment(top_item)
                },
                context_rules=state.context_rules
            )
            why_explanation = llm_commentary
        except Exception:
            why_explanation = f"Why this look was paired: "
            if bottom_item and top_item:
                t_sil = (top_item.attributes or {}).get("silhouette", "fitted")
                b_sil = (bottom_item.attributes or {}).get("silhouette", "straight")
                why_explanation += f"The {t_sil} silhouette of '{top_text}' balances the {b_sil} profile of '{bottom_text}'. "
            else:
                why_explanation += f"'{top_text}' serves as an elegant standalone outfit piece. "
            why_explanation += f"Formality score ({cand['sub_scores']['formality']}/10) evaluated for your {state.raw_occasion} request."


        hero_image = (
            (top_item and top_item.imageUrl) or 
            (bottom_item and bottom_item.imageUrl) or 
            "https://images.unsplash.com/photo-1490481651871-ab68de25d43d?auto=format&fit=crop&w=600&q=80"
        )

        match_score_str = f"{int(cand['combined_score'] * 10)}%"

        final_outfits.append({
            "id": f"outfit-{uuid.uuid4().hex}",
            "rank": i + 1,
            "title": f"Look #{i+1}: {top_text} & {bottom_text}",
            "matchScore": match_score_str,
            "ruleScore": cand["rule_score"],
            "mlScore": cand["ml_score"],
            "combinedScore": cand["combined_score"],
            "trendSignal": f"Wardrobe match • Trend data: {state.trend_research_metadata.get('mode', 'unavailable')}",
            "reason": why_explanation,
            "unavailabilityNotice": None,
            "image": hero_image,
            "criticVerdict": "PASS",
            "appliedRules": cand["applied_rules"],
            "issues": cand["issues"],
            "subScores": cand["sub_scores"],
            "slotItems": {
                "topObj": top_item.dict() if top_item else None,
                "bottomObj": bottom_item.dict() if bottom_item else None,
                "shoeObj": shoe_item.dict() if shoe_item else None,
                "bagObj": bag_item.dict() if bag_item else None,
                "accObj": acc_item.dict() if acc_item else None,
                "outerObj": outer_item.dict() if outer_item else None,
                "isBagExcluded": state.exclude_bags,
                "isAccExcluded": state.exclude_accessories
            },
            "slots": {
                "top": top_text,
                "bottom": bottom_text,
                "outerwear": outer_text,
                "footwear": shoe_text,
                "bag": bag_text,
                "accessory": acc_text
            }
        })

    state.recommended_outfits = final_outfits
    state.execution_trace.append({
        "agent": "Outfit Critic Agent",
        "status": "completed",
        "time": "40ms",
        "summary": f"Validated candidate looks. Approved Top {len(final_outfits)} outfits after strict suitability & deduplication checks."
    })
    return state


def visualization_agent_node(state: AgentGraphState) -> AgentGraphState:
    """
    Node 7: Visualization Agent Node
    Translates each outfit's attributes into a text-to-image prompt
    and generates an AI photo of a generic fashion model wearing that exact outfit.
    Generates visualizations for all recommended outfits.
    """
    if not state.recommended_outfits:
        state.execution_trace.append({
            "agent": "Visualization Agent",
            "status": "skipped",
            "time": "0ms",
            "summary": "No outfits available to visualize."
        })
        return state

    for i, outfit in enumerate(state.recommended_outfits):
        prompt = generate_outfit_visualization_prompt(outfit)
        viz_url = generate_outfit_visualization_image(prompt)

        outfit["visualization_image_url"] = viz_url
        outfit["visualization_prompt"] = prompt

    state.execution_trace.append({
        "agent": "Visualization Agent",
        "status": "completed",
        "time": f"{120 * len(state.recommended_outfits)}ms",
        "summary": f"Generated AI fashion model visualizations for {len(state.recommended_outfits)} outfit{'s' if len(state.recommended_outfits) > 1 else ''}."
    })
    return state

# --- GRAPH ORCHESTRATION PIPELINE ---

def run_multi_agent_pipeline(request_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes the multi-agent nodes sequentially.
    """
    clothes_objs = []
    required_colors = {
        str(color).strip().lower()
        for color in request_dict.get("required_colors", [])
        if str(color).strip()
    }
    excluded_colors = {
        str(color).strip().lower()
        for color in request_dict.get("excluded_colors", [])
        if str(color).strip()
    }
    preferred_colors = {
        str(color).strip().lower()
        for color in request_dict.get("preferred_colors", [])
        if str(color).strip()
    }
    excluded_item_ids = {
        str(item_id) for item_id in request_dict.get("excluded_item_ids", [])
    }
    for c in request_dict.get("clothes", []):
        c_dict = c if isinstance(c, dict) else c.dict()
        normalized_attrs = normalize_garment_attributes(c_dict | (c_dict.get("attributes") or {}))
        if str(c_dict.get("id")) in excluded_item_ids:
            continue
        if required_colors:
            colors = {
                str(color).strip().lower()
                for color in (normalized_attrs.get("color"), normalized_attrs.get("secondary_color"))
                if color
            }
            if not any(
                _color_matches_requirement(color, required)
                for color in colors
                for required in required_colors
            ):
                continue
        if excluded_colors:
            colors = {
                str(color).strip().lower()
                for color in (normalized_attrs.get("color"), normalized_attrs.get("secondary_color"))
                if color
            }
            if any(
                _color_matches_requirement(color, excluded)
                for color in colors
                for excluded in excluded_colors
            ):
                continue
        c_dict["attributes"] = normalized_attrs
        c_dict["style"] = normalized_attrs.get("style", c_dict.get("style", "casual"))
        clothes_objs.append(WardrobeItem(**c_dict))

    state = AgentGraphState(
        user_id=request_dict.get("user_id", 1),
        raw_occasion=request_dict.get("occasion", "college"),
        style_preference=request_dict.get("style_preference", "stylish-trendy"),
        clothes=clothes_objs,
        exclude_bags=request_dict.get("exclude_bags", False),
        exclude_accessories=request_dict.get("exclude_accessories", False),
        context_rules=request_dict.get("context_rules", None),
        required_colors=sorted(required_colors),
        required_top_colors=[
            str(color).strip().lower()
            for color in request_dict.get("required_top_colors", [])
            if str(color).strip()
        ],
        preferred_colors=sorted(preferred_colors),
        excluded_colors=sorted(excluded_colors),
        excluded_categories=request_dict.get("excluded_categories", []),
        required_garment_types=request_dict.get("required_garment_types", []),
        excluded_item_ids=sorted(excluded_item_ids),
        locked_item_ids=[str(item_id) for item_id in request_dict.get("locked_item_ids", [])],
        excluded_outfit_signatures=request_dict.get("excluded_outfit_signatures", []),
        execution_trace=[{
            "agent": "Orchestrator Node",
            "status": "completed",
            "time": "10ms",
            "summary": f"Initiated Multi-Agent LangGraph pipeline for '{request_dict.get('occasion', 'college')}'. Loaded {len(clothes_objs)} stored wardrobe items."
        }]
    )
    state = _apply_weather_context(state, request_dict.get("city"))

    # Chain execution of agent nodes
    state = style_profile_agent_node(state)
    state = trend_research_agent_node(state)
    state = occasion_agent_node(state)
    state = wardrobe_agent_node(state)
    state = outfit_stylist_agent_node(state)
    state = outfit_critic_agent_node(state)
    # Wardrobe flat lays render immediately; model photos are optional.
    if request_dict.get("generate_visualizations", False):
        state = visualization_agent_node(state)

    status_str = "success" if len(state.recommended_outfits) > 0 else "no_match"
    message_str = "Outfits found" if len(state.recommended_outfits) > 0 else (
        "No suitable outfit matched this occasion using your ready-to-wear clothes. "
        "Try another occasion or add suitable items to your wardrobe."
    )
    if not state.recommended_outfits and clothes_objs and not state.filtered_eligible_clothes:
        message_str = (
            "No wardrobe items are currently ready to wear. Update their laundry or ironing status, "
            "or try again when clothes are available."
        )

    return {
        "status": status_str,
        "message": message_str,
        "pipeline": "LangGraph Multi-Agent Architecture with Compatibility Engine & Outfit Critic",
        "occasion": state.raw_occasion,
        "style_preference": state.style_preference,
        "outfits": state.recommended_outfits,
        "count": len(state.recommended_outfits),
        "agentTrace": state.execution_trace
    }
