"""
Centralized Soft Styling Rules System for AI Smart Wardrobe & Personal Stylist
Evaluates clothing pairings across:
- Silhouette & Shape Compatibility
- Proportion & Volume Balance
- Fit Relationships
- Formality & Occasion Alignment (Weddings, Sangeet/Mehndi, Interviews, Office, College, Date, Parties, Custom)
- Color & Pattern Compatibility
- Style & Trend Resonance
- User Preference Adjustments
"""

from typing import Dict, Any, List, Optional, Tuple

ETHNIC_KEYWORDS = [
    "ethnic", "kurti", "kurta", "sherwani", "lehenga", "saree", "anarkali",
    "bandhgala", "indo-western", "traditional", "festive", "bridal", "sangeet",
    "mehndi", "sharara", "gharara", "salwar", "churidar", "palazzo", "dupatta",
    "ghagra", "chaniya", "mojari",
    "jutti", "kolhapuri", "potli"
]
CASUAL_REJECT_KEYWORDS = [
    "hoodie", "t-shirt", "tshirt", "tee", "graphic", "sweatshirt", "tank",
    "crop", "shorts", "cargo", "jogger", "track", "sneaker"
]
INTERVIEW_STYLISH_REJECT = ["stylish", "trendy", "party", "crop", "bodycon", "club"]
FORMAL_TOP_KEYWORDS = ["shirt", "blouse", "oxford", "button-down", "button down", "button_down"]
FORMAL_BOTTOM_KEYWORDS = ["trouser", "pant", "pleated", "tailored", "formal"]
FORMAL_SHOE_KEYWORDS = ["heel", "heels", "pump", "oxford", "loafer", "derby", "formal"]


def garment_blob(attr: Optional[Dict[str, Any]]) -> str:
    if not attr:
        return ""
    nested = attr.get("attributes") if isinstance(attr.get("attributes"), dict) else {}
    parts = [
        attr.get("title"), attr.get("category"), attr.get("subcategory"),
        attr.get("type"), attr.get("style"),
        nested.get("type") if nested else None,
        nested.get("style") if nested else None,
        nested.get("subcategory") if nested else None,
    ]
    return " ".join(str(p) for p in parts if p).lower()


def is_one_piece_garment_dict(attr: Dict[str, Any]) -> bool:
    blob = garment_blob(attr)
    cat = (attr.get("category") or "").lower()
    if cat in ["one_piece", "one-piece", "dresses", "dress"]:
        return True
    keywords = [
        "dress", "maxi", "gown", "jumpsuit", "romper", "one-piece", "one piece",
        "one_piece", "anarkali", "saree", "frock", "bodycon", "lehenga", "sharara"
    ]
    return any(kw in blob for kw in keywords)


def is_ethnic_garment(attr: Optional[Dict[str, Any]]) -> bool:
    return any(k in garment_blob(attr) for k in ETHNIC_KEYWORDS)


def is_wedding_appropriate_look(top_attr: Dict[str, Any], bottom_attr: Optional[Dict[str, Any]] = None) -> bool:
    """Require a standalone festive garment or coordinated ethnic separates."""
    if is_one_piece_garment_dict(top_attr):
        nested = top_attr.get("attributes") if isinstance(top_attr.get("attributes"), dict) else {}
        formality = top_attr.get("formality", nested.get("formality", 5))
        try:
            formality = int(formality)
        except (TypeError, ValueError):
            formality = 5
        festive_one_piece = any(
            keyword in garment_blob(top_attr)
            for keyword in ["wedding", "bridal", "festive", "gala"]
        )
        style = str(top_attr.get("style") or nested.get("style") or "").lower()
        formal_one_piece = formality >= 7 and ("formal" in style or "formal" in garment_blob(top_attr))
        return is_ethnic_garment(top_attr) or festive_one_piece or formality >= 8 or formal_one_piece
    return bool(bottom_attr and is_ethnic_garment(top_attr) and is_ethnic_garment(bottom_attr))


def is_interview_formal_top(attr: Optional[Dict[str, Any]]) -> bool:
    blob = garment_blob(attr)
    style = ((attr or {}).get("style") or "").lower()
    formality = int((attr or {}).get("formality") or 5)
    if any(k in blob for k in CASUAL_REJECT_KEYWORDS + ["kurti", "lehenga", "saree", "anarkali"]):
        return False
    if any(k in blob for k in INTERVIEW_STYLISH_REJECT) and "formal" not in blob and "formal" not in style:
        return False
    has_shirt_shape = any(k in blob for k in FORMAL_TOP_KEYWORDS)
    is_formal = "formal" in style or "formal" in blob or formality >= 8
    return has_shirt_shape and is_formal


def is_interview_formal_bottom(attr: Optional[Dict[str, Any]]) -> bool:
    blob = garment_blob(attr)
    style = ((attr or {}).get("style") or "").lower()
    formality = int((attr or {}).get("formality") or 5)
    if any(k in blob for k in ["jean", "denim", "danim", "cargo", "short", "jogger", "track", "legging"]):
        return False
    if any(k in blob for k in INTERVIEW_STYLISH_REJECT) and "formal" not in blob and "formal" not in style:
        return False
    has_pant_shape = any(k in blob for k in ["trouser", "pant", "chino"])
    is_formal = "formal" in style or "formal" in blob or formality >= 7 or "tailored" in blob or "pleated" in blob
    return has_pant_shape and is_formal


def is_interview_formal_shoe(attr: Optional[Dict[str, Any]]) -> bool:
    blob = garment_blob(attr)
    style = ((attr or {}).get("style") or "").lower()
    if any(k in blob for k in ["sneaker", "trainer", "canvas", "sport", "chunky"]):
        return False
    return any(k in blob for k in FORMAL_SHOE_KEYWORDS) or "formal" in style


def outfit_matches_dress_code(
    top_attr: Dict[str, Any],
    bottom_attr: Optional[Dict[str, Any]],
    context: Optional[Dict[str, Any]] = None,
    shoe_attr: Optional[Dict[str, Any]] = None,
) -> bool:
    context = context or {}
    raw_occ = str(context.get("occasion") or "").lower()
    user_pref = str(context.get("style_preference") or "").lower()
    user_rules = str(context.get("context_rules") or "").lower()
    is_western_wedding = any(w in user_pref or w in user_rules for w in ["western", "tuxedo"]) or (
        "suit" in user_pref and "ethnic" not in user_pref
    )

    is_wedding = any(w in raw_occ for w in ["wedding", "sangeet", "mehndi", "shaadi", "reception", "festive"])
    is_interview = any(w in raw_occ for w in ["interview", "placement"])
    is_office = any(w in raw_occ for w in ["office", "corporate", "meeting", "business", "presentation", "pitch", "conference"])

    if is_wedding and not is_western_wedding:
        return is_wedding_appropriate_look(top_attr, bottom_attr)
    if is_interview or is_office:
        if is_one_piece_garment_dict(top_attr):
            nested = top_attr.get("attributes") if isinstance(top_attr.get("attributes"), dict) else {}
            try:
                formality = int(top_attr.get("formality", nested.get("formality", 5)))
            except (TypeError, ValueError):
                formality = 5
            is_formal_one_piece = (
                "formal" in str(top_attr.get("style") or nested.get("style") or "").lower()
                or formality >= 8
            )
            return is_formal_one_piece and bool(shoe_attr) and is_interview_formal_shoe(shoe_attr)
        top_ok = is_interview_formal_top(top_attr)
        bottom_ok = is_interview_formal_bottom(bottom_attr) if bottom_attr else False
        if not (top_ok and bottom_ok):
            return False
        if not shoe_attr or not is_interview_formal_shoe(shoe_attr):
            return False
        return True
    return True

def evaluate_styling_rules(top_attr: Dict[str, Any], bottom_attr: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Evaluates soft fashion styling rules between a top and bottom garment.
    Returns scores (0-10) for individual attributes, bonuses, penalties, and applied rule logs.
    """
    if context is None:
        context = {}

    user_pref = (context.get("style_preference") or "").lower()
    user_rules = (context.get("context_rules") or "").lower()
    raw_occ = (context.get("occasion") or "").lower()

    is_streetwear_req = "streetwear" in user_pref or "oversized" in user_pref or "streetwear" in user_rules or "oversized" in user_rules
    is_western_wedding_req = any(w in user_pref or w in user_rules for w in ["western", "tuxedo"]) or (
        "suit" in user_pref and "ethnic" not in user_pref
    )

    t_cat = (top_attr.get("category") or "tops").lower()
    b_cat = (bottom_attr.get("category") or "bottoms").lower()

    t_type = (top_attr.get("type") or top_attr.get("subcategory") or "").lower()
    b_type = (bottom_attr.get("type") or bottom_attr.get("subcategory") or "").lower()

    t_fit = (top_attr.get("fit") or "regular").lower()
    b_fit = (bottom_attr.get("fit") or "regular").lower()

    t_sil = (top_attr.get("silhouette") or "straight").lower()
    b_sil = (bottom_attr.get("silhouette") or "straight").lower()

    t_len = (top_attr.get("length") or "regular").lower()
    b_len = (bottom_attr.get("length") or "full").lower()

    b_leg = (bottom_attr.get("leg_shape") or "").lower()
    b_rise = (bottom_attr.get("rise") or "mid").lower()
    t_crop = (top_attr.get("crop_level") or "").lower()

    t_form = top_attr.get("formality", 5)
    b_form = bottom_attr.get("formality", 5)

    t_style = (top_attr.get("style") or "casual").lower()
    b_style = (bottom_attr.get("style") or "casual").lower()

    t_col = (top_attr.get("color") or "").lower()
    b_col = (bottom_attr.get("color") or "").lower()

    t_pat = (top_attr.get("pattern") or "solid").lower()
    b_pat = (bottom_attr.get("pattern") or "solid").lower()

    applied_rules: List[str] = []
    issues: List[str] = []
    occasion_penalty = 0.0

    # Initial base scores (0-10 scale)
    silhouette_score = 7.5
    proportion_score = 7.5
    fit_score = 7.5
    length_score = 7.5
    formality_score = 8.0
    style_score = 7.5
    color_score = 8.0
    pattern_score = 8.5
    volume_score = 7.5

    # OCCASION SPECIFIC RULES (Weddings, Sangeet/Mehndi, Interviews, Presentation, Office, College, Date, Parties, Custom)
    is_wedding = any(w in raw_occ for w in ["wedding", "sangeet", "mehndi", "shaadi", "reception", "festive", "traditional"])
    is_interview = any(w in raw_occ for w in ["interview", "job interview", "placement"])
    is_office_presentation = any(w in raw_occ for w in ["office", "corporate", "meeting", "business", "presentation", "pitch", "conference"])
    is_college = any(w in raw_occ for w in ["college", "campus", "class", "university"])
    is_date_night = any(w in raw_occ for w in ["date", "romantic", "dinner date", "date night", "evening date", "night out", "party", "dinner"])

    is_ethnic_top = is_ethnic_garment(top_attr)
    is_ethnic_bottom = is_ethnic_garment(bottom_attr)
    is_ethnic_outfit = is_ethnic_top or is_ethnic_bottom or is_one_piece_garment_dict(top_attr)

    is_casual_top = any(k in t_type for k in ["t-shirt", "graphic", "hoodie", "sweatshirt", "tank"]) or t_style in ["casual", "streetwear", "sporty"]
    is_casual_bottom = any(k in b_type for k in ["short", "cargo", "jogger", "sweatpants"]) or b_style in ["casual", "sporty"]

    is_fitted_short_top = "fitted" in t_fit or "crop" in t_crop or "cropped" in t_len or "tight" in t_fit
    is_wide_or_bell_bottom = "bell_bottom" in b_leg or "wide" in b_leg or "flared" in b_sil

    if is_wedding:
        if not is_western_wedding_req:
            if is_wedding_appropriate_look(top_attr, bottom_attr):
                style_score += 2.5
                formality_score += 2.0
                applied_rules.append("✓ Wedding Rule: Traditional/ethnic attire (lehenga, one-piece, kurta set) prioritized for festive wedding event.")
            else:
                style_score -= 5.0
                formality_score -= 5.0
                occasion_penalty += 6.5
                issues.append("Occasion mismatch: Western top-and-trouser looks are not festive wedding wear. Prefer lehenga, one-piece, anarkali, or kurta set.")
                applied_rules.append("⚠ Wedding Penalty: Non-ethnic separates deducted for wedding occasion.")
        else:
            if "formal" in t_style or "blazer" in t_type or "suit" in t_type or t_form >= 8:
                style_score += 2.0
                formality_score += 1.5
                applied_rules.append("✓ Western Wedding Rule: Black-tie/Western formal suit pairing applied per user request.")
            elif is_casual_top or is_casual_bottom:
                style_score -= 4.0
                formality_score -= 4.0
                occasion_penalty += 4.5
                issues.append("Occasion mismatch: Casual wear is unsuitable for a Western formal wedding.")

    elif is_interview or is_office_presentation:
        if is_one_piece_garment_dict(top_attr):
            try:
                top_formality = int(top_attr.get("formality", 5))
            except (TypeError, ValueError):
                top_formality = 5
            is_formal_one_piece = (
                "formal" in t_style or top_formality >= 8
            )
        else:
            is_formal_one_piece = False
        formal_top_ok = is_interview_formal_top(top_attr)
        formal_bottom_ok = is_interview_formal_bottom(bottom_attr)

        if is_formal_one_piece or (formal_top_ok and formal_bottom_ok):
            style_score += 2.5
            formality_score += 2.5
            occasion_penalty = 0.0
            applied_rules.append(
                "✓ Job Interview/Presentation/Office Rule: Formal one-piece attire or formal separates."
            )
        else:
            style_score -= 5.0
            formality_score -= 5.0
            occasion_penalty += 6.0
            issues.append("Occasion mismatch: Interview/office looks need a formal shirt, formal trousers, and formal heels — not stylish casual separates.")
            applied_rules.append("⚠ Interview/Presentation Penalty: Stylish/casual items penalized for professional setting.")

    elif is_date_night:
        is_chic_top = any(k in t_type or k in t_style or k in (top_attr.get("title") or "").lower() for k in ["crop", "fitted", "satin", "halter", "stylish", "blouse", "off_shoulder", "sleeveless", "corset"]) or is_fitted_short_top
        is_stylish_bottom = is_wide_or_bell_bottom or any(k in b_type or k in (bottom_attr.get("title") or "").lower() for k in ["bell", "flare", "skirt", "wide", "high_waist", "palazzo"])
        is_stiff_office_top = ("shirt" in t_type or "formal" in t_style) and not is_chic_top and "stylish" not in (top_attr.get("title") or "").lower()

        if is_one_piece_garment_dict(top_attr):
            style_score += 4.5
            silhouette_score += 2.5
            proportion_score += 2.5
            fit_score += 2.5
            formality_score += 2.0
            occasion_penalty = 0.0
            applied_rules.append("✓ Date Night Rule: Elegant one-piece dress/gown is top priority pick for a romantic dinner date.")
        elif is_chic_top and is_stylish_bottom:
            style_score += 3.0
            silhouette_score += 2.0
            proportion_score += 1.5
            occasion_penalty = 0.0
            applied_rules.append("✓ Date Night Rule: Stylish chic top paired with flared/bell-bottom pants creates an alluring evening date silhouette.")
        elif is_stiff_office_top:
            style_score -= 2.5
            formality_score -= 1.5
            occasion_penalty += 2.0
            issues.append("Occasion notice: Plain corporate office shirt lacks romantic evening date flair.")
            applied_rules.append("⚠ Date Night Penalty: Stiff corporate office shirt de-prioritized for romantic date.")
        elif is_casual_top or is_casual_bottom:
            style_score -= 2.0
            formality_score -= 1.5
            occasion_penalty += 1.5
            issues.append("Occasion notice: Daily casual tee/shorts de-prioritized for romantic date.")
            applied_rules.append("⚠ Date Night Notice: Daily casual wear de-prioritized for romantic date.")
        else:
            style_score += 1.5
            applied_rules.append("✓ Date Night Rule: Smart casual pairing evaluated for dinner date.")

    elif is_college:
        is_heavy_festive_dress = any(kw in (top_attr.get("title") or "").lower() or kw in t_style for kw in ["wedding", "party", "anarkali", "gown", "lehenga", "saree", "festive", "bridal"])
        if is_heavy_festive_dress:
            style_score -= 5.0
            formality_score -= 4.5
            occasion_penalty += 6.0
            issues.append("Occasion mismatch: Heavy wedding/party dress is overdressed for daily college campus wear.")
            applied_rules.append("⚠ College Penalty: Heavy wedding/party dresses penalized for daily college routine.")
        elif is_ethnic_outfit:
            style_score -= 2.5
            formality_score -= 2.0
            occasion_penalty += 3.0
            issues.append("Occasion notice: Festive ethnic attire is overdressed for daily college class.")
            applied_rules.append("⚠ College Penalty: Festive ethnic wear penalized for daily college.")
        elif "short" in b_type or "cargo" in b_type:
            formality_score -= 1.5
            style_score -= 1.5
            occasion_penalty += 1.5
            issues.append("College notice: Very casual shorts/cargo bottoms have reduced formality for campus.")
            applied_rules.append("⚠ College Penalty: Cargo shorts penalized for college classroom setting.")
        elif ("casual" in t_style or "smart-casual" in t_style or t_form <= 6) and ("casual" in b_style or "smart-casual" in b_style or b_form <= 6):
            style_score += 1.5
            applied_rules.append("✓ College Rule: Comfortable casual/smart-casual look ideal for campus.")
        elif t_form >= 9 and b_form >= 9:
            style_score -= 2.5
            issues.append("Overdressed notice: Full tuxedo/formal suit is overly stiff for daily college.")
            applied_rules.append("⚠ College Penalty: Ultra-formal suit penalized for relaxed college campus.")


    # RULE 1 & 11: Cropped/fitted top + High-waist wide-leg/bell-bottom
    is_fitted_short_top = "fitted" in t_fit or "crop" in t_crop or "cropped" in t_len or "tight" in t_fit
    is_wide_or_bell_bottom = "bell_bottom" in b_leg or "wide" in b_leg or "flared" in b_sil
    
    if is_fitted_short_top and is_wide_or_bell_bottom and ("high" in b_rise or b_rise == "high"):
        silhouette_score += 2.0
        proportion_score += 2.0
        fit_score += 1.5
        applied_rules.append("✓ RULE 1 & 11: Cropped/fitted top + High-waist flared/bell-bottom creates high proportion balance.")

    # RULE 2 & 13: Fitted top + Wide-leg bottom
    elif "fitted" in t_fit and is_wide_or_bell_bottom:
        silhouette_score += 1.5
        proportion_score += 1.5
        applied_rules.append("✓ RULE 2 & 13: Fitted top balances wide-leg/flared bottom silhouette.")

    # RULE 3 & 14: Long oversized top + Very wide/oversized bottom
    is_long_oversized_top = ("oversized" in t_fit or "loose" in t_sil) and ("mid_thigh" in t_len or "long" in t_len or "hip" in t_len)
    is_oversized_wide_bottom = "oversized" in b_fit or "wide" in b_leg or "relaxed" in b_fit

    if is_long_oversized_top and is_oversized_wide_bottom:
        if is_streetwear_req:
            silhouette_score += 1.0
            proportion_score += 0.5
            applied_rules.append("✓ RULE 3/14 (Streetwear Context): Oversized top + wide bottom accepted for requested streetwear aesthetic.")
        else:
            silhouette_score -= 2.0
            proportion_score -= 2.0
            volume_score -= 1.5
            issues.append("High visual volume: Long oversized top with wide/relaxed bottom creates an unanchored silhouette.")
            applied_rules.append("⚠ RULE 3 & 14: Oversized top + wide bottom proportion penalty (no explicit streetwear preference).")

    # RULE 4 & 15: Long oversized top + Straight/slim bottom
    is_slim_straight_bottom = "straight" in b_leg or "slim" in b_fit or "skinny" in b_leg or "jeans" in b_type
    if is_long_oversized_top and is_slim_straight_bottom:
        silhouette_score += 1.5
        proportion_score += 1.5
        applied_rules.append("✓ RULE 4 & 15: Long oversized top anchored by straight/slim bottom silhouette.")

    # RULE 5 & 6: Oversized hoodie + relaxed jeans / cargo
    is_hoodie = "hoodie" in t_type or "sweatshirt" in t_type
    if is_hoodie and ("jeans" in b_type or "relaxed" in b_fit):
        style_score += 1.5
        fit_score += 1.0
        applied_rules.append("✓ RULE 5: Oversized hoodie + relaxed jeans forms an authentic casual/streetwear look.")

    # RULE 7 & 8: Long Kurti / tunic + straight vs wide cargo trousers
    is_kurti = "kurti" in t_type or "tunic" in t_type or "ethnic" in t_style
    if is_kurti:
        if "straight" in b_leg or "trouser" in b_type or "legging" in b_type or "pyjama" in b_type:
            silhouette_score += 2.0
            style_score += 2.0
            applied_rules.append("✓ RULE 7: Long Kurti/Tunic paired with straight trousers/pyjamas for classic fusion symmetry.")
        elif "cargo" in b_type:
            style_score -= 3.5
            issues.append("Stylistic mismatch: Traditional Kurti paired with utilitarian cargo pants.")
            applied_rules.append("⚠ RULE 8: Kurti + Cargo pants style mismatch penalty.")

    # RULE 9: Formal fitted shirt + formal tailored trousers
    is_formal_top = "formal" in t_style or t_form >= 7 or "shirt" in t_type or "blazer" in t_type
    is_formal_bottom = "formal" in b_style or b_form >= 7 or "trouser" in b_type or "pleated" in b_type
    if is_formal_top and is_formal_bottom and not is_wedding:
        formality_score += 2.0
        style_score += 1.5
        applied_rules.append("✓ RULE 9: Tailored formal top + tailored formal bottom produces strong formality cohesion.")

    # RULE 10: Formal top + highly casual bottom (or vice versa)
    if abs(t_form - b_form) >= 3:
        formality_score -= 2.5
        style_score -= 2.0
        occasion_penalty += 2.0
        issues.append(f"Formality gap: Top formality level ({t_form}) differs significantly from bottom ({b_form}).")
        applied_rules.append("⚠ RULE 10: Significant formality delta penalty applied.")

    # Color Compatibility logic
    neutral_colors = ["black", "white", "grey", "gray", "beige", "navy", "denim", "cream"]
    if t_col in neutral_colors or b_col in neutral_colors:
        color_score += 1.0
        applied_rules.append(f"✓ Color Match: Versatile neutral color pairing ({t_col} & {b_col}).")
    elif t_col == b_col and t_col != "":
        color_score += 1.5
        applied_rules.append(f"✓ Color Match: Intentional monochrome coordination ({t_col}).")

    # Pattern Compatibility logic
    if t_pat != "solid" and b_pat != "solid" and t_pat != b_pat:
        pattern_score -= 2.5
        issues.append(f"Pattern clash: Competing patterns detected ({t_pat} top with {b_pat} bottom).")
        applied_rules.append("⚠ Pattern Rule: Multiple non-matching patterns create visual noise.")

    # Normalize scores between 0.0 and 10.0
    return {
        "silhouette_score": round(max(0.0, min(10.0, silhouette_score)), 1),
        "proportion_score": round(max(0.0, min(10.0, proportion_score)), 1),
        "fit_score": round(max(0.0, min(10.0, fit_score)), 1),
        "length_score": round(max(0.0, min(10.0, length_score)), 1),
        "formality_score": round(max(0.0, min(10.0, formality_score)), 1),
        "style_score": round(max(0.0, min(10.0, style_score)), 1),
        "color_score": round(max(0.0, min(10.0, color_score)), 1),
        "pattern_score": round(max(0.0, min(10.0, pattern_score)), 1),
        "volume_score": round(max(0.0, min(10.0, volume_score)), 1),
        "occasion_penalty": round(occasion_penalty, 1),
        "applied_rules": applied_rules,
        "issues": issues
    }
