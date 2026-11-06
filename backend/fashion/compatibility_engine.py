"""
Fashion Compatibility Engine for AI Smart Wardrobe & Personal Stylist
Evaluates complete candidate outfits across 12 fashion dimensions using configurable weights.
"""

from typing import Dict, Any, List, Optional
from fashion.styling_rules import evaluate_styling_rules

# Default Configurable Dimension Weights (sums to 1.0 / 100%)
DEFAULT_COMPATIBILITY_WEIGHTS = {
    "color": 0.10,
    "style": 0.15,
    "length": 0.10,
    "fit": 0.10,
    "silhouette": 0.15,
    "proportion": 0.15,
    "volume": 0.05,
    "occasion": 0.08,
    "formality": 0.05,
    "pattern": 0.02,
    "trend": 0.05,
    "user_preference": 0.00  # Calculated during hybrid decision phase
}

class CompatibilityEngine:
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or DEFAULT_COMPATIBILITY_WEIGHTS

    def evaluate_candidate_outfit(
        self,
        top_item: Optional[Dict[str, Any]],
        bottom_item: Optional[Dict[str, Any]],
        shoe_item: Optional[Dict[str, Any]] = None,
        outer_item: Optional[Dict[str, Any]] = None,
        occasion_formality: int = 5,
        trend_signals: Optional[List[Dict[str, Any]]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calculates normalized compatibility sub-scores (0-10) for a candidate outfit
        and computes the weighted Rule Compatibility Score.
        """
        if context is None:
            context = {}

        top_attr = dict(top_item or {})
        if top_item and isinstance(top_item.get("attributes"), dict):
            top_attr.update(top_item["attributes"])

        bottom_attr = dict(bottom_item or {})
        if bottom_item and isinstance(bottom_item.get("attributes"), dict):
            bottom_attr.update(bottom_item["attributes"])

        shoe_attr = dict(shoe_item or {})
        if shoe_item and isinstance(shoe_item.get("attributes"), dict):
            shoe_attr.update(shoe_item["attributes"])
        outer_attr = (outer_item.get("attributes") if outer_item else {}) or outer_item or {}

        # 1. Rule Engine evaluation between Top and Bottom
        ctx_with_occ = dict(context)
        ctx_with_occ["occasion"] = ctx_with_occ.get("occasion") or occasion_formality
        rule_eval = evaluate_styling_rules(top_attr, bottom_attr, ctx_with_occ)

        # 2. Occasion & Formality alignment against target occasion formality
        target_formality = occasion_formality
        top_form = top_attr.get("formality", 5)
        bottom_form = bottom_attr.get("formality", 5) if bottom_item else top_form
        avg_formality = (top_form + bottom_form) / 2.0
        formality_diff = abs(avg_formality - target_formality)
        
        # Standalone one-piece dresses/gowns have zero formality penalty for evening dates, parties, & weddings
        from fashion.styling_rules import is_one_piece_garment_dict
        if is_one_piece_garment_dict(top_attr) and target_formality >= 5:
            formality_diff = 0.0

        base_occ_score = max(0.0, 10.0 - (formality_diff * 1.5))
        occ_penalty = rule_eval.get("occasion_penalty", 0.0)
        occasion_score = round(max(0.0, min(10.0, base_occ_score - occ_penalty)), 1)

        # 3. Trend signal resonance
        trend_score = 7.5
        if trend_signals:
            import re
            # Uploaded photos can contain megabytes of base64. Only fashion
            # metadata is relevant to trend matching, never image bytes or URLs.
            trend_fields = (
                'title', 'category', 'subcategory', 'type', 'color', 'secondary_color',
                'pattern', 'style', 'season', 'material', 'fabric', 'fit',
                'silhouette', 'length', 'style_tags',
            )
            parts = []
            for item in (top_item, bottom_item, shoe_item, outer_item):
                if not item:
                    continue
                for metadata in (item, item.get('attributes') or {}):
                    if isinstance(metadata, dict):
                        parts.extend(str(metadata[field]) for field in trend_fields if metadata.get(field))
            blob = ' '.join(parts).lower()
            strengths = [float(ts.get('score', 0)) / 100 for ts in trend_signals
                         if ts.get('current') and re.search(r'(?<!\w)' + re.escape(ts.get('tag') or '__none__') + r's?(?!\w)', blob)]
            trend_score += min(2.5, sum(sorted(strengths, reverse=True)[:3]))
        trend_score = round(min(10.0, trend_score), 1)
        # Extract dimension sub-scores
        scores = {
            "color": rule_eval["color_score"],
            "style": rule_eval["style_score"],
            "length": rule_eval["length_score"],
            "fit": rule_eval["fit_score"],
            "silhouette": rule_eval["silhouette_score"],
            "proportion": rule_eval["proportion_score"],
            "volume": rule_eval["volume_score"],
            "occasion": occasion_score,
            "formality": rule_eval["formality_score"],
            "pattern": rule_eval["pattern_score"],
            "trend": trend_score
        }

        # Calculate weighted composite score
        total_weight = sum(self.weights.get(k, 0.0) for k in scores.keys())
        weighted_sum = sum(scores[k] * self.weights.get(k, 0.0) for k in scores.keys())
        rule_compatibility_score = round(weighted_sum / total_weight, 2) if total_weight > 0 else 7.5

        return {
            "rule_compatibility_score": rule_compatibility_score,
            "sub_scores": scores,
            "applied_rules": rule_eval["applied_rules"],
            "issues": rule_eval["issues"]
        }

# Singleton instance
default_engine = CompatibilityEngine()
