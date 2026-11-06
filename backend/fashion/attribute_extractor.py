"""
Attribute Extractor & Schema Definition for AI Smart Wardrobe
Defines granular clothing attributes and fallback parsing routines.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class GarmentAttributes(BaseModel):
    category: str = "tops"               # tops, bottoms, outerwear, footwear, bags, accessories
    subcategory: str = "tshirt"          # tshirt, jeans, jacket, Kurti, trousers, etc.
    type: str = "fitted_tshirt"          # bell_bottom, oversized_tshirt, kurti, wide_leg, crop_top, etc.
    color: str = "Black"                 # dominant color
    secondary_color: Optional[str] = None
    pattern: str = "solid"               # solid, striped, floral, graphic, denim, plaid, etc.
    material: Optional[str] = "cotton"
    texture: Optional[str] = "smooth"
    style: str = "casual"                # casual, formal, smart-casual, streetwear, ethnic, sporty
    formality: int = 5                   # 1 (extremely casual) to 10 (black-tie formal)
    
    # Fit & Silhouette
    fit: str = "regular"                 # fitted, relaxed, oversized, slim, skinny, loose
    silhouette: str = "straight"         # flared, straight, A-line, boxy, fitted_thigh, loose
    volume: str = "medium"               # low, medium, high
    
    # Length
    length: str = "regular"              # cropped, waist, hip, mid_thigh, knee, ankle, full
    relative_length: Optional[str] = "standard"
    
    # Top specific
    sleeve_length: Optional[str] = None  # sleeveless, short, 3/4, long
    neckline: Optional[str] = None       # crew, v-neck, collar, boat, scoop, turtleneck
    shoulder_shape: Optional[str] = None # natural, padded, drop-shoulder
    crop_level: Optional[str] = None     # high_crop, low_crop, non_cropped
    
    # Bottom specific
    leg_shape: Optional[str] = None      # skinny, straight, wide_leg, bell_bottom, flared, bootcut, cargo, jogger
    rise: Optional[str] = None           # high, mid, low
    waist_type: Optional[str] = None     # elastic, button, drawstring, tailored
    thigh_fit: Optional[str] = None      # tight, fitted, relaxed, loose
    ankle_fit: Optional[str] = None      # tapered, wide, elastic, flared
    
    # Outerwear specific
    jacket_type: Optional[str] = None    # blazer, leather, denim, puffer, cardigan
    structure: Optional[str] = None      # structured, unstructured, relaxed
    
    # Vision Confidence
    confidence: float = 0.90
    alternative_type: Optional[str] = None

def normalize_garment_attributes(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensures raw JSON dictionary complies with default values and standard string formats.
    """
    if not isinstance(raw_data, dict):
        raw_data = {}

    cat = str(raw_data.get("category") or "tops").lower().strip()
    if cat in ["one_piece", "one-piece", "dresses", "dress"]:
        cat = "one_piece"
    valid_categories = ["tops", "bottoms", "one_piece", "outerwear", "footwear", "bags", "accessories"]
    if cat not in valid_categories:
        cat = "tops"

    title = str(raw_data.get("title") or "").lower().strip()
    subcat = str(raw_data.get("subcategory") or title or "garment").lower().strip()
    garment_type = str(raw_data.get("type") or subcat).lower().replace(" ", "_").strip()
    
    color = str(raw_data.get("color") or "Black").title().strip()
    pattern = str(raw_data.get("pattern") or "solid").lower().strip()
    style = str(raw_data.get("style") or "casual").lower().strip()
    
    # Infer style from title/subcat if default or generic
    if any(k in title or k in subcat or k in garment_type for k in ["formal", "blazer", "tuxedo", "oxford"]):
        style = "formal"
    elif any(k in title or k in subcat or k in garment_type for k in ["ethnic", "kurta", "kurti", "sherwani", "anarkali", "saree", "lehenga", "sharara", "salwar"]):
        style = "ethnic"
    elif any(k in title or k in subcat or k in garment_type for k in ["streetwear", "hoodie", "graphic"]):
        style = "streetwear"

    # Infer formality (1-10) based on style and keywords
    raw_formality = raw_data.get("formality")
    if raw_formality is not None and int(raw_formality) != 5:
        formality = int(raw_formality)
    else:
        if style == "formal" or any(k in title or k in subcat for k in ["formal", "blazer", "suit", "tuxedo"]):
            formality = 9
        elif style == "smart-casual" or any(k in title or k in subcat for k in ["chino", "polo", "sweater", "loafer"]):
            formality = 7
        elif style == "ethnic" or any(k in title or k in subcat for k in ["kurta", "kurti", "sherwani", "anarkali", "lehenga", "saree"]):
            formality = 8
        elif any(k in title or k in subcat for k in ["t-shirt", "tee", "hoodie", "short", "cargo", "sneaker"]):
            formality = 3
        else:
            formality = 5
            
    formality = max(1, min(10, formality))

    fit = str(raw_data.get("fit") or "regular").lower().replace(" ", "_").strip()
    silhouette = str(raw_data.get("silhouette") or "straight").lower().replace(" ", "_").strip()
    volume = str(raw_data.get("volume") or "medium").lower().strip()
    length = str(raw_data.get("length") or "regular").lower().replace(" ", "_").strip()

    # Derived attributes based on category & type heuristics if missing
    leg_shape = raw_data.get("leg_shape")
    if not leg_shape and cat == "bottoms":
        if "bell" in garment_type or "flare" in silhouette:
            leg_shape = "bell_bottom"
        elif "wide" in garment_type or "wide" in fit:
            leg_shape = "wide_leg"
        elif "cargo" in garment_type:
            leg_shape = "cargo"
        elif "skinny" in garment_type or "skinny" in fit:
            leg_shape = "skinny"
        elif "straight" in garment_type:
            leg_shape = "straight"
        else:
            leg_shape = "straight"

    rise = raw_data.get("rise")
    if not rise and cat == "bottoms":
        if "high" in garment_type or "high" in subcat or "high" in fit:
            rise = "high"
        elif "low" in garment_type:
            rise = "low"
        else:
            rise = "mid"

    crop_level = raw_data.get("crop_level")
    if not crop_level and cat == "tops":
        if "crop" in garment_type or "crop" in fit or "crop" in length:
            crop_level = "cropped"
        else:
            crop_level = "non_cropped"

    attr_obj = GarmentAttributes(
        category=cat,
        subcategory=subcat,
        type=garment_type,
        color=color,
        secondary_color=raw_data.get("secondary_color"),
        pattern=pattern,
        material=raw_data.get("material", "cotton"),
        texture=raw_data.get("texture", "smooth"),
        style=style,
        formality=formality,
        fit=fit,
        silhouette=silhouette,
        volume=volume,
        length=length,
        relative_length=raw_data.get("relative_length", "standard"),
        sleeve_length=raw_data.get("sleeve_length"),
        neckline=raw_data.get("neckline"),
        shoulder_shape=raw_data.get("shoulder_shape"),
        crop_level=crop_level,
        leg_shape=leg_shape,
        rise=rise,
        waist_type=raw_data.get("waist_type"),
        thigh_fit=raw_data.get("thigh_fit"),
        ankle_fit=raw_data.get("ankle_fit"),
        jacket_type=raw_data.get("jacket_type"),
        structure=raw_data.get("structure"),
        confidence=float(raw_data.get("confidence", 0.90)),
        alternative_type=raw_data.get("alternative_type")
    )

    return attr_obj.model_dump()
