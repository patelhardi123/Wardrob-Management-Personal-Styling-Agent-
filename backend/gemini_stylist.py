"""
Conversational Stylist AI — Multi-Provider with Smart Fallback
==============================================================
Handles ANY style/wardrobe question with full natural language understanding.

Provider priority:
  1. Google Gemini (google-genai SDK, new API format) — uses GEMINI_API_KEY / GOOGLE_API_KEY
  2. OpenAI (via OPENAI_API_KEY if credits available)
  3. Smart Rule-Based Engine (works 100% offline, no API needed — always succeeds)

Use cases handled:
  - "I have a bun hairstyle and going to a wedding anniversary party"
  - "Which colours go well with my blue denim jeans"
  - "It's a corporate retreat this weekend, casual but professional"
  - "Add my jeans to laundry"
  - "What should I wear for a graduation brunch?"
  - Any general style/fashion question
  - Non-standard occasions beyond the fixed list
"""

import os
import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime


# ─────────────────────────────────────────────────────────────
# LLM PROVIDER — PRIORITY CHAIN
# ─────────────────────────────────────────────────────────────

def _call_llm(prompt: str) -> Optional[str]:
    """
    Try LLM providers in order until one works.
    Returns raw text response or None if all fail.
    """
    # 1. Google Gemini — try new SDK first
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")
    # Validate key looks like a real Gemini key (starts with AIza)
    if gemini_key and gemini_key.startswith("AIza") and len(gemini_key) > 20:
        # Try new google-genai SDK
        try:
            from google import genai as google_genai  # type: ignore
            client = google_genai.Client(api_key=gemini_key, http_options={"timeout": 6000})
            model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            text = (response.text or "").strip()
            if text:
                print(f"[ConvStylist] Used Gemini SDK ({model_name})")
                return text
        except ImportError:
            pass  # SDK not installed, try REST
        except Exception as exc:
            print(f"[ConvStylist] Gemini SDK failed: {exc}")
            return None

        # Try Gemini REST API directly (no extra package needed)
        try:
            import urllib.request
            import urllib.error
            model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
            url = (
                f"https://generativelanguage.googleapis.com/v1beta/models/"
                f"{model_name}:generateContent?key={gemini_key}"
            )
            body = json.dumps({
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.7, "maxOutputTokens": 800}
            }).encode("utf-8")
            req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read())
            text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            if text:
                print(f"[ConvStylist] Used Gemini REST ({model_name})")
                return text
        except Exception as exc:
            print(f"[ConvStylist] Gemini REST failed: {exc}")

    # 2. OpenAI fallback
    openai_key = os.getenv("OPENAI_API_KEY", "")
    if openai_key and len(openai_key) > 20:
        try:
            from openai import OpenAI  # type: ignore
            client = OpenAI(api_key=openai_key, timeout=6.0, max_retries=0)
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=700,
                temperature=0.7,
            )
            text = (resp.choices[0].message.content or "").strip()
            if text:
                print("[ConvStylist] Used OpenAI gpt-4o-mini")
                return text
        except Exception as exc:
            print(f"[ConvStylist] OpenAI failed: {exc}")

    print("[ConvStylist] All LLM providers unavailable — using rule-based engine")
    return None


# ─────────────────────────────────────────────────────────────
# WARDROBE SUMMARY
# ─────────────────────────────────────────────────────────────

def _build_wardrobe_summary(clothes: List[Dict[str, Any]]) -> str:
    if not clothes:
        return "Wardrobe: (empty — no clothes added yet)"
    categories: Dict[str, list] = {}
    for item in clothes:
        cat = item.get("category", "other")
        avail = item.get("availability_status", "ready")
        iron = item.get("ironing_status", "ready")
        ready = avail in ("ready", "available") and iron == "ready"
        status = "" if ready else f" [{avail}]"
        label = f"{item.get('title','?')} ({item.get('color','?')}, {item.get('style','?')}){status}"
        categories.setdefault(cat, []).append(label)
    lines = ["=== WARDROBE ==="]
    for cat, items in categories.items():
        lines.append(f"{cat.upper()}: " + "; ".join(items))
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# SYSTEM PROMPT FOR LLM
# ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are Aria, a warm expert AI personal stylist and wardrobe assistant.
You help with:
1. Outfit suggestions for ANY occasion — standard (wedding, office) or non-standard (anniversary party, corporate retreat, graduation brunch, baby shower, picnic, etc.)
2. Color coordination advice (what tops go with blue jeans, what shoes match a red dress, etc.)
3. Style advice considering context like hairstyle, body type, weather, accessories
4. Wardrobe management (laundry status, ironing, availability)
5. General fashion questions

RULES:
- Reference SPECIFIC items from the user's wardrobe by name when possible
- For color advice questions, give direct color pairing recommendations — DO NOT suggest outfits
- Support ALL occasions, not just a fixed list
- For laundry/status requests, identify the item and the new status
- Keep answers conversational, warm, helpful (2-4 sentences)
- If an occasion is mentioned, always set needs_outfit_pipeline=true to show outfit cards
- If the question is purely about color pairing (no occasion mentioned), set needs_outfit_pipeline=false

Return ONLY this JSON (no markdown, no extra text):
{
  "response_text": "Your warm conversational answer here",
  "response_type": "outfit | text | status_update | general_advice",
  "occasion": "detected occasion label or null",
  "style_preference": "casual | formal | ethnic | smart-casual | elegant | sporty | null",
  "needs_outfit_pipeline": true or false,
  "status_update": null or {"item_description": "...", "new_status": "to_wash | in_wash | drying | ready | needs_ironing | missing | damaged"}
}"""


# ─────────────────────────────────────────────────────────────
# EXTENDED OCCASION PATTERNS — handles non-standard occasions
# ─────────────────────────────────────────────────────────────

# Each entry: (canonical_label, [keywords_list])
# ORDER MATTERS — more specific phrases first
OCCASION_PATTERNS = [
    ("wedding anniversary",   ["wedding anniversary", "anniversary party", "anniversary celebration"]),
    ("anniversary",           ["anniversary"]),
    ("wedding",               ["wedding", "shaadi", "marriage ceremony", "reception", "sangeet", "mehndi", "nikah", "baraat", "bridal"]),
    ("job interview",         ["job interview", "interview", "placement drive", "campus placement", "campus interview"]),
    ("corporate retreat",     ["corporate retreat", "team outing", "company retreat", "office retreat", "company trip"]),
    ("office",                ["office", "work meeting", "corporate meeting", "board meeting", "client meeting", "presentation", "business meeting"]),
    ("graduation",            ["graduation", "convocation", "farewell", "farewell party"]),
    ("baby shower",           ["baby shower", "gender reveal", "gender-reveal"]),
    ("bachelorette",          ["bachelorette", "hen party", "hen night"]),
    ("prom",                  ["prom", "prom night", "school dance", "formal dance"]),
    ("cocktail party",        ["cocktail party", "cocktail", "gala", "charity event", "black tie", "semi-formal"]),
    ("birthday party",        ["birthday party", "birthday celebration", "birthday"]),
    ("house party",           ["house party", "home party", "kitty party"]),
    ("party",                 ["party", "evening party", "night out", "club", "clubbing"]),
    ("brunch",                ["brunch", "lunch party", "sunday brunch", "birthday brunch"]),
    ("festival",              ["festival", "diwali", "eid", "holi", "navratri", "durga puja", "ganesh", "onam", "pongal", "baisakhi", "christmas", "new year", "lohri", "ugadi"]),
    ("date",                  ["date night", "dinner date", "romantic dinner", "first date", "lunch date"]),
    ("casual outing",         ["mall", "shopping", "coffee", "cafe", "outing", "hangout", "get-together", "gathering"]),
    ("college",               ["college", "class", "lecture", "campus", "university", "school", "study"]),
    ("travel",                ["travel", "trip", "vacation", "holiday", "flight", "trek", "picnic", "hike", "hiking"]),
    ("gym",                   ["gym", "workout", "exercise", "yoga", "pilates", "sports", "running", "jogging"]),
    ("beach",                 ["beach", "pool party", "poolside", "resort"]),
    ("dinner",                ["dinner", "dinner party", "fine dining"]),
    ("concert",               ["concert", "music festival", "gig", "show", "performance"]),
]

STYLE_DEFAULTS: Dict[str, str] = {
    "wedding anniversary": "elegant",
    "anniversary": "elegant",
    "wedding": "ethnic",
    "job interview": "formal",
    "corporate retreat": "smart-casual",
    "office": "formal",
    "graduation": "smart-casual",
    "baby shower": "smart-casual",
    "bachelorette": "smart-casual",
    "prom": "elegant",
    "cocktail party": "elegant",
    "birthday party": "smart-casual",
    "house party": "casual",
    "party": "smart-casual",
    "brunch": "casual",
    "festival": "ethnic",
    "date": "smart-casual",
    "casual outing": "casual",
    "college": "casual",
    "travel": "casual",
    "gym": "sporty",
    "beach": "casual",
    "dinner": "smart-casual",
    "concert": "smart-casual",
}

# ─────────────────────────────────────────────────────────────
# COLOR KNOWLEDGE BASE
# ─────────────────────────────────────────────────────────────

COLOR_COMBOS: Dict[str, List[str]] = {
    "blue": ["white", "cream", "grey", "black", "beige", "light pink", "mustard yellow", "olive", "burgundy", "navy"],
    "denim": ["white", "grey", "black", "striped", "beige", "olive", "mustard", "pink", "red", "chambray"],
    "navy": ["white", "cream", "beige", "gold", "light blue", "pink", "coral", "mustard"],
    "black": ["white", "red", "pink", "gold", "silver", "grey", "beige", "cream", "blue", "burgundy"],
    "white": ["any color", "blue", "black", "navy", "beige", "olive", "red", "pastel tones", "earth tones"],
    "red": ["white", "black", "navy", "gold", "cream", "beige"],
    "maroon": ["white", "cream", "beige", "gold", "olive", "navy"],
    "beige": ["white", "brown", "olive", "navy", "black", "rust", "gold", "tan"],
    "cream": ["camel", "brown", "navy", "olive", "black", "rust", "blush pink"],
    "green": ["white", "beige", "cream", "brown", "mustard", "coral", "gold"],
    "olive": ["white", "black", "beige", "tan", "rust", "mustard", "cream"],
    "pink": ["white", "grey", "nude", "beige", "navy", "black", "pastel green"],
    "blush": ["white", "grey", "navy", "gold", "beige", "cream"],
    "grey": ["white", "black", "pastel pink", "navy", "yellow", "red", "teal", "lavender"],
    "yellow": ["white", "navy", "black", "grey", "olive", "brown", "denim blue"],
    "mustard": ["white", "navy", "black", "brown", "olive", "denim blue"],
    "orange": ["white", "navy", "brown", "olive", "cream", "denim blue"],
    "brown": ["beige", "cream", "white", "olive", "orange", "rust", "tan", "gold"],
    "tan": ["white", "black", "navy", "olive", "beige", "rust"],
    "purple": ["white", "grey", "black", "pink", "gold", "beige", "lavender"],
    "lavender": ["white", "grey", "navy", "dusty rose", "sage green"],
    "gold": ["white", "black", "navy", "beige", "maroon", "cream", "deep green"],
    "silver": ["white", "black", "grey", "navy", "icy blue", "blush pink"],
    "teal": ["white", "beige", "gold", "navy", "coral", "rust"],
    "coral": ["white", "navy", "beige", "gold", "teal"],
    "rust": ["white", "cream", "navy", "brown", "beige", "olive"],
}

HAIRSTYLE_NECKLINE: Dict[str, str] = {
    "bun": "With a bun, any neckline works beautifully — V-necks and off-shoulder styles especially frame your neck and look very elegant.",
    "ponytail": "A ponytail pairs beautifully with off-shoulder or boat necklines, and higher necklines look polished too.",
    "open hair": "Open hair works with most styles — avoid too much neckline detail so the hair can flow freely.",
    "braids": "Braids look stunning with ethnic wear or boho-casual styles. Scoop and boat necklines complement them nicely.",
    "curly": "Curly hair is gorgeous with simple tops or bold prints — avoid busy necklines that compete with the texture.",
    "short hair": "Short hair pairs beautifully with statement earrings and higher necklines like turtlenecks or collared shirts.",
    "half up": "Half-up styles work with almost any neckline — halter necks and V-necks look especially chic.",
    "low bun": "A low bun is elegant with off-shoulder, halter, or V-neck styles that showcase your neckline.",
    "messy bun": "A messy bun gives off a relaxed vibe — pair with casual or boho outfits for effortless style.",
}


# ─────────────────────────────────────────────────────────────
# DETECTION HELPERS
# ─────────────────────────────────────────────────────────────

def _detect_occasion(text: str) -> Optional[str]:
    """Detect occasion from text. Returns canonical label or None."""
    text_lower = text.lower()
    for occasion_label, keywords in OCCASION_PATTERNS:
        for kw in keywords:
            # Use word boundary check for single words, substring for phrases
            if " " in kw:
                if kw in text_lower:
                    return occasion_label
            else:
                if re.search(r"\b" + re.escape(kw) + r"\b", text_lower):
                    return occasion_label
    return None


def _detect_color_question(text: str):
    """
    Returns (base_color, item_description) if this is a color question.
    Both can be None if not detected.
    """
    text_lower = text.lower().strip()
    color_question_patterns = [
        r"which\s+colou?rs?\s+(?:tops?|shirts?|blouses?|bottoms?|trousers?|jeans?|shoes?|dress(?:es)?|outfits?|clothes)\s+(?:go|work|look|match|suit|pair)\s+(?:well\s+)?(?:with|to)?\s+(?:my\s+)?(.+)",
        r"which\s+colou?rs?\s+(?:go|work|look|match|suit|pair)\s+(?:well\s+)?with\s+(?:my\s+)?(.+)",
        r"what\s+colou?rs?\s+(?:tops?|shirts?|blouses?|bottoms?|trousers?|jeans?|shoes?|outfits?|clothes)\s+(?:go|work|look|match|suit|pair)\s+(?:well\s+)?(?:with|to)?\s+(?:my\s+)?(.+)",
        r"what\s+colou?rs?\s+(?:go|work|look|suit|match|pair)\s+(?:well\s+)?(?:with|for)?\s+(?:my\s+)?(.+)",
        r"(?:colou?r|shade)s?\s+(?:for|to match|that go with|that suit|matching)\s+(?:my\s+)?(.+)",
        r"what\s+(?:colou?r|shade)s?\s+(?:should\s+i|can\s+i|to)\s+(?:wear|pick|choose)\s+with\s+(?:my\s+)?(.+)",
        r"(?:suggest|recommend)\s+(?:me\s+)?(?:colou?r|shade)s?\s+(?:for|that go with|with)\s+(?:my\s+)?(.+)",
        r"which\s+colou?rs?\s+tops?\s+go\s+well\s+with\s+(?:my\s+)?(.+)",
        r"what\s+(?:colou?r|colors?)\s+(?:can|should)\s+i\s+(?:wear|pair|combine|match)\s+with\s+(?:my\s+)?(.+)",
    ]

    for pattern in color_question_patterns:
        m = re.search(pattern, text_lower)
        if m:
            item_desc = m.group(1).strip().rstrip("?.,!")
            # Extract the base color from the item description
            for color in sorted(COLOR_COMBOS.keys(), key=len, reverse=True):
                if re.search(r"\b" + re.escape(color) + r"\b", item_desc):
                    return color, item_desc
            return None, item_desc

    # Catch shorter "what goes with X" or "goes well with X" patterns
    short_patterns = [
        r"(?:what|which)\s+(?:goes?|looks?|works?|pairs?|matches?)\s+(?:well\s+)?with\s+(?:my\s+)?(.+)",
        r"what\s+(?:to\s+)?(?:wear|pair)\s+with\s+(?:my\s+)?(.+)",
        r"(.+)\s+what\s+colou?r\s+(?:goes?|matches?|pairs?)",
    ]
    if any(w in text_lower for w in ["colour", "color", "go well", "match", "pair", "suit", "goes with", "wear with"]):
        for pattern in short_patterns:
            m = re.search(pattern, text_lower)
            if m:
                item_desc = m.group(1).strip().rstrip("?.,!")
                for color in sorted(COLOR_COMBOS.keys(), key=len, reverse=True):
                    if re.search(r"\b" + re.escape(color) + r"\b", item_desc):
                        return color, item_desc
                # even without a named color, it's still a color question
                return None, item_desc

    return None, None


def _detect_laundry_intent(text: str):
    """Returns (item_description, new_status) or (None, None)."""
    text_lower = text.lower()
    laundry_patterns = [
        (r"(?:add|put|send|throw|move)\s+(?:my\s+)?(.+?)\s+(?:to|in(?:to)?)\s+(?:the\s+)?laundry(?:\s+list)?", "to_wash"),
        (r"(?:my\s+)?(.+?)\s+(?:needs?|need|require)\s+(?:to\s+be\s+)?wash(?:ing|ed)?", "to_wash"),
        (r"(?:wash|washing|clean)\s+(?:my\s+)?(.+?)(?:\s+please|\s+now|[.,!?]|$)", "to_wash"),
        (r"(?:my\s+)?(.+?)\s+is\s+(?:in\s+the\s+)?(?:wash|laundry|washing\s+machine)", "in_wash"),
        (r"(?:my\s+)?(.+?)\s+(?:needs?|need)\s+ironing", "needs_ironing"),
        (r"(?:iron(?:ing)?)\s+(?:my\s+)?(.+?)(?:\s+please|\s+now|[.,!?]|$)", "needs_ironing"),
        (r"(?:my\s+)?(.+?)\s+is\s+drying", "drying"),
        (r"(?:my\s+)?(.+?)\s+is\s+(?:missing|lost)", "missing"),
        (r"(?:my\s+)?(.+?)\s+is\s+(?:damaged|torn|broken|ruined)", "damaged"),
        (r"(?:my\s+)?(.+?)\s+is\s+(?:ready|clean|washed|available|done)", "ready"),
        (r"(?:i\s+(?:have\s+)?(?:washed|cleaned|ironed))\s+(?:my\s+)?(.+?)(?:\s+please|\s+now|[.,!?]|$)", "ready"),
        (r"(?:my\s+)?(.+?)\s+is\s+now\s+ready", "ready"),
    ]
    for pattern, status in laundry_patterns:
        m = re.search(pattern, text_lower)
        if m:
            item = m.group(1).strip().strip(".,!? ")
            noise = {"it", "this", "that", "them", "these", "those", "the", "a", "an", "my"}
            if item and item not in noise and len(item) > 2:
                return item, status
    return None, None


def _detect_hairstyle(text: str) -> Optional[str]:
    """Detect mentioned hairstyle."""
    text_lower = text.lower()
    for style in HAIRSTYLE_NECKLINE:
        if style in text_lower:
            return style
    # Extra regex patterns
    if re.search(r"\bmessy\s+bun\b", text_lower):
        return "messy bun"
    if re.search(r"\blow\s+bun\b", text_lower):
        return "low bun"
    if re.search(r"\bhalf[\s-]up\b", text_lower):
        return "half up"
    if re.search(r"\bbun\b", text_lower):
        return "bun"
    if re.search(r"\bponytail\b", text_lower):
        return "ponytail"
    if re.search(r"\bopen\s+hair\b|\bhair\s+down\b", text_lower):
        return "open hair"
    if re.search(r"\bbraids?\b|\bplaits?\b", text_lower):
        return "braids"
    if re.search(r"\bcurly\b|\bcurls?\b", text_lower):
        return "curly"
    if re.search(r"\bshort\s+hair\b", text_lower):
        return "short hair"
    return None


def _get_available_items(clothes: List[Dict]) -> List[Dict]:
    return [
        item for item in clothes
        if item.get("availability_status", "ready") in ("ready", "available")
        and item.get("ironing_status", "ready") == "ready"
    ]


def _is_outfit_request(text: str) -> bool:
    """Does the text ask for an outfit suggestion? Returns False for pure color questions."""
    tl = text.lower()
    # Exclude color/style advice questions
    if re.search(r"\bwhich\s+colo(?:u)?r\b|\bwhat\s+colo(?:u)?r\b|\bcolo(?:u)?rs?\s+(?:go|suit|match|pair|work)\b", tl):
        return False
    if re.search(r"\bsuggests?\s+(?:a\s+)?colo(?:u)?r\b|\brecommend\s+(?:a\s+)?colo(?:u)?r\b", tl):
        return False
    return bool(re.search(
        r"\b(wear|outfit|outfits|full\s+look|whole\s+look|complete\s+look|"
        r"look\s+from|give\s+me\s+a\s+look|dress|style\s+me|put\s+together|"
        r"what\s+should\s+i\s+wear|suggest.*outfit|give.*outfit)\b",
        tl
    ))


def _is_general_style_question(text: str) -> bool:
    patterns = [
        r"\bhow\s+(?:do\s+i|should\s+i|to)\b",
        r"\bwhat\s+(?:is|are)\s+(?:the\s+)?(?:trend|style|fashion|tip|rule)\b",
        r"\b(?:tip|advice|guide|help)\s+(?:for|on|about)\b",
        r"\bcan\s+i\s+(?:wear|pair|combine|mix)\b",
        r"\bshould\s+i\s+(?:wear|choose|pick|go\s+with)\b",
        r"\bcapsule\s+wardrobe\b",
        r"\bwhat\s+(?:color|colour|shade|style|type)\s+(?:goes?|suits?|matches?|works?|looks?)\b",
        r"\bdress\s+code\b",
        r"\bfashion\s+(?:tip|rule|advice)\b",
    ]
    return any(re.search(p, text.lower()) for p in patterns)


# ─────────────────────────────────────────────────────────────
# RULE-BASED RESPONSE ENGINE (primary when LLM unavailable)
# ─────────────────────────────────────────────────────────────

def _rule_based_response(
    user_message: str,
    clothes: List[Dict[str, Any]],
    saved_state: Dict[str, Any],
    conversation_history: List[Dict[str, str]],
) -> Dict[str, Any]:
    """
    Powerful rule-based stylist engine.
    Handles: color questions, occasion-based outfits, laundry, general style,
    greetings, and non-standard occasions.
    Always returns a valid response dict.
    """
    text = user_message.strip()
    text_lower = text.lower()

    # ── 0. IMAGE-CONTEXT FOLLOW-UP ──────────────────────────────
    # If the user asks for a look/outfit AND there's an image_context in saved_state,
    # route to the outfit pipeline.  Do NOT set color constraints here — the pipeline
    # generates better results when it runs freely against the full wardrobe.
    _img_ctx = saved_state.get("image_context")
    _is_outfit_ask = bool(re.search(
        r"\b(outfit|full\s+look|whole\s+look|complete\s+look|look\s+from|"
        r"give\s+me\s+a\s+look|put\s+together|style\s+me|suggest.*outfit|"
        r"give.*outfit|outfit\s+look|based\s+on|preferences|"
        r"pair\s+(?:this|it)|what\s+(?:goes|pairs?)\s+with\s+this|dress\s+me)\b",
        text_lower
    ))
    if _img_ctx and _is_outfit_ask:
        _dc = _img_ctx.get("detected_color", "")
        _gl = _img_ctx.get("garment_label", "garment")
        occasion = saved_state.get("occasion") or _detect_occasion(text) or "casual"
        style_pref = STYLE_DEFAULTS.get(occasion, "smart-casual")
        resp = (
            f"Based on your {_dc} {_gl}, let me find a complete outfit from your wardrobe "
            f"that works beautifully with it. Here are your best looks:"
        )
        return {
            "agent_response": resp,
            "response_type": "outfit",
            "needs_outfit_pipeline": True,
            "occasion": occasion,
            "style_preference": style_pref,
            "status_update": None,
            "extra_context": f"image_context: {_dc} {_gl}",
            "gemini_used": False,
        }

    # ── 1. LAUNDRY / STATUS UPDATE ──────────────────────────────
    item_desc, new_status = _detect_laundry_intent(text)
    if item_desc and new_status:
        action_map = {
            "to_wash": "added to the laundry",
            "in_wash": "marked as in the wash",
            "drying": "marked as currently drying",
            "needs_ironing": "flagged as needing ironing",
            "ready": "marked as ready to wear",
            "missing": "marked as missing",
            "damaged": "marked as damaged",
        }
        action_phrase = action_map.get(new_status, "updated")
        return {
            "agent_response": (
                f"Done! Your {item_desc} has been {action_phrase}. "
                "I'll keep it out of outfit suggestions until it's ready again. 👍"
            ),
            "response_type": "status_update",
            "needs_outfit_pipeline": False,
            "occasion": saved_state.get("occasion"),
            "style_preference": None,
            "status_update": {"item_description": item_desc, "new_status": new_status},
            "extra_context": None,
            "gemini_used": False,
        }

    # ── 2. COLOR COORDINATION QUESTION ──────────────────────────
    # Check this BEFORE occasion/outfit detection so "which color top suits this" 
    # never gets mis-routed to the outfit pipeline.
    base_color, item_ref = _detect_color_question(text)
    # Also catch "which color/style/type top suits with this" patterns
    _is_style_type_question = bool(re.search(
        r"\bwhich\s+(color|colour|style|type|kind)\s+(top|shirt|bottom|trouser|pant|shoe|dress)\b",
        text_lower
    ))
    is_color_question = (
        (base_color is not None)
        or _is_style_type_question
        or (
            item_ref is not None
            and any(
                w in text_lower
                for w in ["colour", "color", "go well", "match", "pair", "suit", "goes with"]
            )
        )
    )

    if is_color_question:
        # Find base color if not already found
        if not base_color and item_ref:
            for c in sorted(COLOR_COMBOS.keys(), key=len, reverse=True):
                if re.search(r"\b" + re.escape(c) + r"\b", item_ref.lower()):
                    base_color = c
                    break

        if base_color and base_color in COLOR_COMBOS:
            combos = COLOR_COMBOS[base_color]
            # Check which colors user actually has in wardrobe (tops)
            available = _get_available_items(clothes)
            wardrobe_tops = [
                i for i in available
                if i.get("category") in ("tops", "outerwear", "one_piece", "dresses")
            ]
            wardrobe_colors = [i.get("color", "").lower() for i in wardrobe_tops]

            # Find matches in their actual wardrobe
            matching_wardrobe = []
            for c in combos:
                if any(c in wc or wc in c for wc in wardrobe_colors):
                    matching_wardrobe.append(c)

            item_label = item_ref or f"{base_color} bottoms"
            if matching_wardrobe:
                top_matches = matching_wardrobe[:4]
                resp = (
                    f"Great question! For your {item_label}, these colors from your wardrobe pair beautifully: "
                    f"**{', '.join(top_matches)}**. "
                    f"Classic pairings like {combos[0]} and {combos[1]} always look great with {base_color}. "
                    "Want me to pull together a full outfit suggestion?"
                )
            else:
                top_picks = combos[:5]
                resp = (
                    f"For your {item_label}, the best color pairings are **{', '.join(top_picks[:4])}**. "
                    f"{combos[0].capitalize()} and {combos[1]} are the most versatile classics that work in any situation. "
                    "Shall I suggest a complete outfit from your wardrobe?"
                )
        elif item_ref:
            resp = (
                f"For {item_ref}, neutral tones like white, beige, grey, and black are your safest bets — "
                "they go with almost everything. For a bolder look, try a complementary or contrast color. "
                "Want me to suggest a complete outfit?"
            )
        else:
            resp = (
                "Neutral tones like white, black, beige, and grey are incredibly versatile and pair with almost any color. "
                "For a pop of personality, try earthy tones like mustard, olive, or rust with your basics. "
                "Which specific item are you trying to match?"
            )

        return {
            "agent_response": resp,
            "response_type": "general_advice",
            "needs_outfit_pipeline": False,
            "occasion": saved_state.get("occasion"),
            "style_preference": None,
            "status_update": None,
            "extra_context": f"color question about {base_color or item_ref}",
            "gemini_used": False,
        }

    # ── 3. OCCASION DETECTION → OUTFIT PIPELINE ─────────────────
    occasion = _detect_occasion(text)
    hairstyle = _detect_hairstyle(text)
    style_pref = STYLE_DEFAULTS.get(occasion, "smart-casual") if occasion else None

    if occasion or _is_outfit_request(text):
        available = _get_available_items(clothes)
        unavail_count = len(clothes) - len(available)

        hairstyle_tip = ""
        if hairstyle and hairstyle in HAIRSTYLE_NECKLINE:
            hairstyle_tip = f" {HAIRSTYLE_NECKLINE[hairstyle]}"

        if occasion:
            resp = f"Love it! Let me pull together some looks for your {occasion}."
            if hairstyle_tip:
                resp += hairstyle_tip
            if unavail_count > 0:
                resp += f" ({unavail_count} item(s) are unavailable, so I'll suggest from your ready wardrobe.)"
            resp += " Here are some great options for you:"
        else:
            resp = "Sure! Let me find the best outfit options from your wardrobe:"

        # If NEW occasion is different from saved, signal reset
        current_occasion = saved_state.get("occasion")
        needs_reset = bool(occasion and occasion != current_occasion)

        return {
            "agent_response": resp,
            "response_type": "outfit",
            "needs_outfit_pipeline": True,
            "occasion": occasion or current_occasion,
            "style_preference": style_pref,
            "status_update": None,
            "extra_context": f"hairstyle: {hairstyle}" if hairstyle else None,
            "new_occasion": occasion if needs_reset else None,
            "gemini_used": False,
        }

    # ── 4. AVAILABILITY / WARDROBE STATUS QUERY ─────────────────
    if any(kw in text_lower for kw in [
        "what's in laundry", "what is in laundry", "unavailable", "what clothes",
        "what items", "which items", "which clothes", "available clothes"
    ]):
        return {
            "agent_response": "Let me check what's available in your wardrobe right now.",
            "response_type": "text",
            "needs_outfit_pipeline": False,
            "occasion": saved_state.get("occasion"),
            "style_preference": None,
            "status_update": None,
            "extra_context": "availability_check",
            "gemini_used": False,
        }

    # ── 5. GENERAL STYLE / FASHION QUESTION ─────────────────────
    if _is_general_style_question(text):
        resp = _smart_style_answer(text, clothes, saved_state)
        return {
            "agent_response": resp,
            "response_type": "general_advice",
            "needs_outfit_pipeline": False,
            "occasion": saved_state.get("occasion"),
            "style_preference": None,
            "status_update": None,
            "extra_context": None,
            "gemini_used": False,
        }

    # ── 6. GREETING / SMALL TALK ─────────────────────────────────
    if re.search(r"^(hi|hello|hey|hola|good\s+\w+|namaste|sup|what'?s\s+up)\b", text_lower):
        available_count = len(_get_available_items(clothes))
        return {
            "agent_response": (
                f"Hey there! I'm Aria, your personal AI stylist. 👗 "
                f"You have {available_count} items ready to wear right now. "
                "I can suggest outfits for any occasion, help with color combinations, "
                "or manage your wardrobe. What can I do for you today?"
            ),
            "response_type": "text",
            "needs_outfit_pipeline": False,
            "occasion": saved_state.get("occasion"),
            "style_preference": None,
            "status_update": None,
            "extra_context": None,
            "gemini_used": False,
        }

    # ── 7. THANKS / FEEDBACK ─────────────────────────────────────
    if re.search(r"^(thanks?|thank\s+you|great|awesome|perfect|cool|nice|wow)\b", text_lower):
        return {
            "agent_response": "You're welcome! 😊 Let me know if you'd like to explore more outfit options or have any other style questions.",
            "response_type": "text",
            "needs_outfit_pipeline": False,
            "occasion": saved_state.get("occasion"),
            "style_preference": None,
            "status_update": None,
            "extra_context": None,
            "gemini_used": False,
        }

    # ── 8. DEFAULT: Route to outfit pipeline with current/inferred occasion ─
    # Rather than returning nothing, always try to be helpful
    current_occasion = saved_state.get("occasion")
    if current_occasion:
        resp = f"Based on our conversation, let me find some more outfit options for your {current_occasion}:"
        return {
            "agent_response": resp,
            "response_type": "outfit",
            "needs_outfit_pipeline": True,
            "occasion": current_occasion,
            "style_preference": saved_state.get("style_preference"),
            "status_update": None,
            "extra_context": None,
            "gemini_used": False,
        }

    return {
        "agent_response": (
            "I'm here to help with your style! Tell me about an occasion you're dressing for, "
            "ask about color combinations, or let me know if you'd like to manage your wardrobe. "
            "What would you like help with?"
        ),
        "response_type": "text",
        "needs_outfit_pipeline": False,
        "occasion": None,
        "style_preference": None,
        "status_update": None,
        "extra_context": None,
        "gemini_used": False,
    }


def _smart_style_answer(text: str, clothes: List[Dict], saved_state: Dict) -> str:
    """Generate a contextual style answer using wardrobe knowledge."""
    text_lower = text.lower()
    available = _get_available_items(clothes)

    if "can i wear" in text_lower or "should i wear" in text_lower:
        return (
            "Absolutely! The key is to match the occasion's dress code and pick pieces that make you feel confident. "
            "From your wardrobe, mixing one solid basic with one statement piece always looks polished and intentional."
        )
    if "capsule" in text_lower:
        tops = [i for i in available if i.get("category") == "tops"]
        bottoms = [i for i in available if i.get("category") == "bottoms"]
        return (
            f"A great capsule wardrobe focuses on versatile basics you can mix and match freely. "
            f"You have {len(tops)} tops and {len(bottoms)} bottoms — a solid foundation! "
            "Stick to neutrals as your base and add 2-3 statement pieces for personality and variety."
        )
    if "trend" in text_lower or "trendy" in text_lower:
        return (
            "Current trends include oversized blazers, wide-leg trousers, and earthy/neutral tones. "
            "The best trend is one that complements your personal style and lifestyle. "
            "Work with what you already have and add one trendy piece at a time — that's the smart approach!"
        )
    if "body type" in text_lower or "figure" in text_lower or "shape" in text_lower:
        return (
            "The golden rule: wear what makes YOU feel confident and comfortable! "
            "A-line skirts and straight-leg trousers are universally flattering, and high-waisted "
            "bottoms beautifully elongate the silhouette. Would you like a more tailored suggestion?"
        )
    if "dress code" in text_lower:
        return (
            "Dress codes in brief: Formal = suits/gowns; Smart-casual = blazer+chinos or midi dress; "
            "Business casual = clean trousers+blouse; Casual = jeans+clean top. "
            "When in doubt, always go one level up from what you think is required — overdressing is easier to fix than underdressing!"
        )
    return (
        "Great style is really about wearing what makes you feel confident for the occasion. "
        "From your wardrobe, mixing and matching items you already love is the most sustainable and stylish approach. "
        "Would you like me to suggest a specific outfit or answer another style question?"
    )


# ─────────────────────────────────────────────────────────────
# LLM-POWERED RESPONSE (with fallback)
# ─────────────────────────────────────────────────────────────

def _llm_response(
    user_message: str,
    clothes: List[Dict],
    saved_state: Dict,
    conversation_history: List[Dict],
) -> Optional[Dict[str, Any]]:
    """Call an LLM for a richer response. Returns None if all LLMs fail."""
    wardrobe_summary = _build_wardrobe_summary(clothes)
    current_occasion = saved_state.get("occasion")

    history_text = ""
    if conversation_history:
        recent = conversation_history[-6:]
        lines = []
        for turn in recent:
            role = turn.get("role", "")
            content = (turn.get("content") or "")[:250]
            if role in ("user", "assistant"):
                lines.append(f"{role.upper()}: {content}")
        if lines:
            history_text = "\nRecent conversation:\n" + "\n".join(lines) + "\n"

    now = datetime.now().strftime("%A, %B %d, %Y %I:%M %p")
    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"Current date/time: {now}\n"
        f"{wardrobe_summary}\n"
        f"{f'Current session occasion: {current_occasion}' if current_occasion else ''}\n"
        f"{history_text}"
        f"User message: {user_message}\n\n"
        "Respond with JSON only:"
    )

    raw = _call_llm(prompt)
    if not raw:
        return None

    # Strip markdown fences if any
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw.strip())

    try:
        parsed = json.loads(raw)
        needs_pipeline = bool(parsed.get("needs_outfit_pipeline", False))
        resp_type = parsed.get("response_type", "text")
        if resp_type == "outfit":
            needs_pipeline = True
        llm_occasion = parsed.get("occasion") or current_occasion
        needs_reset = bool(llm_occasion and llm_occasion != current_occasion)
        return {
            "agent_response": parsed.get("response_text", ""),
            "response_type": resp_type,
            "needs_outfit_pipeline": needs_pipeline,
            "occasion": llm_occasion,
            "new_occasion": llm_occasion if needs_reset else None,
            "style_preference": parsed.get("style_preference"),
            "status_update": parsed.get("status_update"),
            "extra_context": None,
            "gemini_used": True,
        }
    except json.JSONDecodeError as exc:
        print(f"[ConvStylist] LLM JSON parse failed: {exc} | raw[:200]: {raw[:200]}")
        return None


# ─────────────────────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────────────────────

def process_with_gemini(
    user_message: str,
    conversation_history: List[Dict[str, str]],
    clothes: List[Dict[str, Any]],
    saved_state: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Main entry point from voice_agent_graph.py.
    Always returns a result — LLM if available, otherwise rule-based engine.
    Never returns None.
    """
    # Try LLM first for richer responses
    llm_result = _llm_response(user_message, clothes, saved_state, conversation_history)
    if llm_result and llm_result.get("agent_response"):
        return llm_result

    # Fallback: powerful rule-based engine (zero API dependency)
    return _rule_based_response(user_message, clothes, saved_state, conversation_history)


def answer_general_style_question(
    user_message: str,
    conversation_history: List[Dict[str, str]],
    clothes: List[Dict[str, Any]],
) -> str:
    """Answer a general style question. Returns plain text."""
    llm_prompt = (
        "You are Aria, a warm expert personal stylist.\n"
        f"Wardrobe context: {_build_wardrobe_summary(clothes)}\n"
        f"User question: {user_message}\n"
        "Give a helpful, specific, warm answer in 2-4 sentences. "
        "Reference wardrobe items by name if relevant. Plain text only, no JSON."
    )
    raw = _call_llm(llm_prompt)
    if raw:
        return raw.strip()
    return _smart_style_answer(user_message, clothes, {})


def classify_message_type(message: str) -> str:
    """Quick local classification without LLM."""
    text = message.lower()
    _, status = _detect_laundry_intent(message)
    if status:
        return "laundry"
    if _detect_occasion(text):
        return "outfit"
    color, _ = _detect_color_question(text)
    if color or any(w in text for w in ["colour", "color", "match", "pair", "go with", "goes with"]):
        return "general"
    if re.search(r"\b(wear|outfit|dress|look|style|suggest|recommend)\b", text):
        return "outfit"
    if _is_general_style_question(text):
        return "general"
    return "text"
