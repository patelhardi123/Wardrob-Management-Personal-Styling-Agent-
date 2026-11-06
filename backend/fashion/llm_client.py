"""
Unified OpenRouter & OpenAI LLM Client Module for AI Smart Wardrobe
Supports OpenRouter (Claude 3.5 Sonnet, Gemini 2.0 Flash, GPT-4o, Llama 3.3)
and standard OpenAI models.
"""

import os
import json
import base64
from typing import Dict, Any, Optional
from openai import OpenAI
from fashion.attribute_extractor import normalize_garment_attributes

def get_llm_client_and_model():
    """
    Determines the appropriate API client (OpenRouter vs OpenAI) and target model.
    Prioritizes OPENROUTER_API_KEY if present, or OPENAI_API_KEY.
    """
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if openrouter_key:
        api_key = openrouter_key
        base_url = "https://openrouter.ai/api/v1"
        model = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-001")
        extra_headers = {
            "HTTP-Referer": "http://localhost:5173",
            "X-Title": "AI Smart Wardrobe & Personal Stylist"
        }
        client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=8.0, max_retries=0, default_headers=extra_headers
        )
        return client, model, "openrouter"
    elif openai_key:
        # Check if the key starts with 'sk-or-' (OpenRouter key pasted in OPENAI_API_KEY)
        if openai_key.strip().startswith("sk-or-"):
            api_key = openai_key.strip()
            base_url = "https://openrouter.ai/api/v1"
            model = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-001")
            extra_headers = {
                "HTTP-Referer": "http://localhost:5173",
                "X-Title": "AI Smart Wardrobe & Personal Stylist"
            }
            client = OpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=8.0, max_retries=0, default_headers=extra_headers
            )
            return client, model, "openrouter"
        else:
            client = OpenAI(api_key=openai_key, timeout=8.0, max_retries=0)
            model = os.getenv("OPENAI_MODEL", "gpt-4o")
            return client, model, "openai"
    else:
        return None, None, None


def analyze_garment_vision(image_bytes: bytes) -> Dict[str, Any]:
    """
    Performs AI vision analysis on clothing images via OpenRouter/OpenAI.
    Returns normalized garment attributes dictionary.
    """
    client, model, provider = get_llm_client_and_model()

    if not client:
        # Graceful rule-based fallback if no API keys are present
        return _fallback_vision_analysis(image_bytes)

    base64_image = base64.b64encode(image_bytes).decode('utf-8')

    prompt = """Analyze this clothing item image and return a JSON object with precise fashion attributes:
{
  "category": "one of: tops, bottoms, one_piece, outerwear, footwear, bags, accessories",
  "subcategory": "specific item name (e.g. T-Shirt, Jeans, Kurti, Sharara, Blazer, Sneakers, Dress, Jumpsuit)",
  "type": "exact style type (e.g. bell_bottom, wide_leg, skinny_jeans, cargo, kurti, crop_top, oversized_tshirt, fitted_shirt, bodycon_dress, sharara, blazer)",
  "color": "dominant primary color (e.g., Black, Blue, Red, White, Beige, Navy, Gold, Maroon)",
  "secondary_color": "accent color or null",
  "pattern": "pattern (e.g., solid, striped, floral, graphic, plaid, denim, embroidered)",
  "style": "aesthetic (e.g., casual, formal, smart-casual, streetwear, ethnic, sporty)",
  "formality": integer from 1 (ultra-casual) to 10 (black tie formal),
  "fit": "fit (e.g., fitted, regular, relaxed, oversized, slim, loose)",
  "silhouette": "shape profile (e.g. flared, straight, A-line, boxy, fitted_thigh)",
  "volume": "low, medium, or high",
  "length": "cropped, waist, hip, mid_thigh, knee, ankle, full",
  "rise": "for bottoms: high, mid, or low (else null)",
  "leg_shape": "for bottoms: bell_bottom, wide_leg, straight, skinny, cargo, jogger (else null)",
  "crop_level": "for tops: cropped, non_cropped (else null)",
  "sleeve_length": "for tops/dresses: sleeveless, short, 3/4, long (else null)",
  "neckline": "for tops/dresses: crew, v-neck, collar, boat, scoop, turtleneck (else null)",
  "confidence": 0.95
}
Return ONLY valid JSON. No markdown syntax."""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500,
            temperature=0.2
        )

        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.replace("```json", "").replace("```", "").strip()

        raw_json = json.loads(content)
        return normalize_garment_attributes(raw_json)

    except Exception as e:
        print(f"[LLM Client] OpenRouter/OpenAI Vision call failed ({e}), falling back to heuristic extraction.")
        return _fallback_vision_analysis(image_bytes)


def generate_stylist_commentary(occasion: str, style_pref: str, outfit: Dict[str, Any], context_rules: Optional[str] = None) -> str:
    """
    Generates rich personalized styling commentary using OpenRouter / OpenAI LLM.
    """
    client, model, provider = get_llm_client_and_model()

    if not client:
        return _fallback_commentary(occasion, outfit)

    top = outfit.get("topObj", {})
    bottom = outfit.get("bottomObj", {})
    shoes = outfit.get("shoesObj", {})
    outer = outfit.get("outerwearObj", {})
    accessories = outfit.get("accessoriesObj", [])
    one_piece = outfit.get("isOnePiece", False)

    prompt = f"""You are an expert luxury personal stylist creating custom outfit advice.
Occasion: {occasion}
Style Aesthetic: {style_pref}
User Personal Rules/Context: {context_rules or 'None'}

Outfit Components:
- Garment: {top.get('title', 'N/A')} (Category: {top.get('category', '')}, Style: {top.get('style', '')})
- Bottom: {"None Needed (One-Piece Dress/Garment)" if one_piece else bottom.get('title', 'N/A')}
- Outerwear: {outer.get('title', 'None')}
- Footwear: {shoes.get('title', 'None')}
- Accessories: {", ".join([a.get('title', '') for a in accessories]) or 'None'}

Provide a concise, 2-3 sentence sleek stylist recommendation explaining why this outfit is ideal for {occasion}, how to wear it (tuck/sleeve styling), and why the shoes/accessories harmonize perfectly. Return raw text only."""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[LLM Client] Commentary generation error ({e}). Returning default recommendation text.")
        return _fallback_commentary(occasion, outfit)


def generate_outfit_visualization_prompt(outfit: Dict[str, Any]) -> str:
    """
    Builds a text-to-image prompt from an outfit's structured attributes
    describing a generic fashion model wearing the exact outfit combination.
    """
    slots = outfit.get("slots", {})
    slot_items = outfit.get("slotItems", {})
    
    top_name = slots.get("top") or "stylish top"
    bottom_name = slots.get("bottom") or ""
    outer_name = slots.get("outerwear") or ""
    shoe_name = slots.get("footwear") or ""
    bag_name = slots.get("bag") or ""
    acc_name = slots.get("accessory") or ""

    garment_parts = [top_name]
    if bottom_name and "None Needed" not in bottom_name:
        garment_parts.append(bottom_name)
    if outer_name and "None Needed" not in outer_name:
        garment_parts.append(f"with {outer_name}")
    if shoe_name and "None Needed" not in shoe_name and "Footwear" not in shoe_name:
        garment_parts.append(f"paired with {shoe_name}")
    if bag_name and "None Needed" not in bag_name and "Excluded" not in bag_name:
        garment_parts.append(f"carrying a {bag_name}")
    if acc_name and "None Needed" not in acc_name and "Excluded" not in acc_name:
        garment_parts.append(f"accented with {acc_name}")

    outfit_desc = ", ".join(garment_parts)
    prompt = (
        f"Full-body high fashion photograph of a stylish model standing in a natural studio pose on a clean neutral background, "
        f"wearing {outfit_desc}. Professional studio lighting, soft shadows, 8k resolution, elegant magazine editorial look."
    )
    return prompt


def generate_outfit_visualization_image(prompt: str) -> str:
    """
    Generates an AI image of a generic fashion model wearing the outfit.
    Prioritizes OpenAI DALL-E 3 if API key present, or falls back to Pollinations FLUX engine.
    """
    import urllib.parse
    import random
    import time
    import os

    # Priority 1: OpenAI DALL-E 3 if API key is present
    if os.getenv("OPENAI_API_KEY"):
        try:
            from openai import OpenAI
            openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=15.0, max_retries=0)
            response = openai_client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )
            if response.data and response.data[0].url:
                print(f"[Visualization Agent] Generated image using OpenAI DALL-E 3")
                return response.data[0].url
        except Exception as e:
            print(f"[Visualization Agent] DALL-E 3 call failed: {e}. Falling back to Pollinations FLUX model.")

    # Priority 2 / Fallback: Pollinations AI FLUX Image Generation (Fast, Free, High Quality)
    # Add randomness to seed to avoid rate limits and get different images
    encoded_prompt = urllib.parse.quote(prompt)
    # Combine prompt hash with timestamp and random number for unique seeds
    base_seed = abs(hash(prompt)) % 100000
    time_seed = int(time.time() * 1000) % 100000
    random_seed = random.randint(1, 999999)
    seed = (base_seed + time_seed + random_seed) % 1000000
    pollinations_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&seed={seed}&model=flux&nologo=true"
    print(f"[Visualization Agent] Generated image using Pollinations FLUX (seed: {seed})")
    return pollinations_url


def _fallback_vision_analysis(image_bytes: bytes) -> Dict[str, Any]:
    import random
    seed = len(image_bytes) % 1000
    random.seed(seed)
    categories = ["tops", "bottoms", "one_piece", "outerwear", "footwear", "bags", "accessories"]
    colors = ["Black", "Blue", "Red", "White", "Grey", "Brown", "Green", "Pink", "Yellow", "Navy"]
    selected_cat = categories[seed % len(categories)]
    selected_color = colors[seed % len(colors)]
    return normalize_garment_attributes({
        "category": selected_cat,
        "subcategory": "garment",
        "color": selected_color,
        "style": "casual",
        "confidence": 0.85
    })


def _fallback_commentary(occasion: str, outfit: Dict[str, Any]) -> str:
    top = outfit.get("topObj", {})
    bottom = outfit.get("bottomObj", {})
    is_one_piece = outfit.get("isOnePiece", False)

    if is_one_piece:
        return f"A stunning standalone {top.get('title', 'one-piece outfit')} perfectly balanced for {occasion}. Elevate with sleek footwear and subtle statement accessories."
    else:
        return f"This pairing of {top.get('title', 'top')} with {bottom.get('title', 'bottom')} delivers an effortless, polished silhouette tailored for {occasion}."

