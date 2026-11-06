"""
Comprehensive 23-Scenario Test Suite for AI Smart Wardrobe & Personal Stylist
Tests all occasions: Weddings (ethnic & western), Job Interviews, College, Custom Events,
Suitability filtering, Variable outfit counts (0, 1, 2, 3), and Candidate Deduplication.
"""

from fashion.attribute_extractor import normalize_garment_attributes
from fashion.compatibility_engine import default_engine
from fashion.ml_compatibility import ml_model
from agent_graph import (
    AgentGraphState,
    WardrobeItem,
    _apply_weather_context,
    _matches_required_garment_types,
    run_multi_agent_pipeline,
    wardrobe_agent_node,
)


def test_multiple_garment_type_choices_are_alternatives():
    kurta = WardrobeItem(id="kurta", title="Silk Kurta", category="tops", style="ethnic")
    lehenga = WardrobeItem(id="lehenga", title="Flared Lehenga", category="bottoms", style="ethnic")
    shoes = WardrobeItem(id="shoes", title="Embroidered Jutti", category="footwear", style="ethnic")

    assert _matches_required_garment_types(
        kurta, [kurta, lehenga, shoes], ["one_piece", "lehenga"]
    )
    assert not _matches_required_garment_types(
        kurta, [kurta, shoes], ["one_piece"]
    )


def test_preferred_color_ranks_matching_owned_items_higher():
    state = AgentGraphState(
        raw_occasion="college",
        style_preference="casual",
        occasion_formality_score=5,
        preferred_colors=["blue"],
        clothes=[
            WardrobeItem(id="white", title="White Casual Shirt", category="tops", color="White", style="casual"),
            WardrobeItem(id="blue", title="Blue Casual Shirt", category="tops", color="Blue", style="casual"),
        ]
    )

    result = wardrobe_agent_node(state)

    assert [item.id for item in result.filtered_eligible_clothes] == ["blue", "white"]


def test_required_top_color_keeps_other_colors_for_a_complete_outfit(monkeypatch):
    monkeypatch.setattr("agent_graph.visualization_agent_node", lambda state: state)
    response = run_multi_agent_pipeline({
        "occasion": "college",
        "style_preference": "casual",
        "required_top_colors": ["yellow"],
        "clothes": [
            {"id": "yellow-top", "title": "Yellow T-shirt", "category": "tops", "color": "Yellow", "style": "casual"},
            {"id": "black-trousers", "title": "Black Straight-Leg Trousers", "category": "bottoms", "color": "Black", "style": "casual"},
            {"id": "white-sneakers", "title": "White Sneakers", "category": "footwear", "color": "White", "style": "casual"},
        ]
    })

    assert response["status"] == "success"
    assert response["outfits"]
    for outfit in response["outfits"]:
        slots = outfit["slotItems"]
        assert slots["topObj"]["id"] == "yellow-top"
        assert slots["bottomObj"]["id"] == "black-trousers"
        assert slots["shoeObj"]["id"] == "white-sneakers"


def test_weather_context_prioritizes_warm_layers_and_rainproof_footwear(monkeypatch):
    monkeypatch.setattr("agent_graph.fetch_live_weather", lambda city="New York": {
        "city": city,
        "temperature_c": 7,
        "condition": "Raining / Wet",
        "constraints": ["Heavy outerwear required", "Water-resistant footwear recommended"],
        "status": "live",
    })

    state = _apply_weather_context(AgentGraphState(
        raw_occasion="dinner date",
        style_preference="casual",
        context_rules="Dress for a cozy dinner.",
        clothes=[
            WardrobeItem(id="tee", title="Cotton T-shirt", category="tops", style="casual"),
            WardrobeItem(id="knit", title="Long-sleeve Knit Polo", category="tops", style="smart-casual"),
            WardrobeItem(id="rain-coat", title="Waterproof Trench Coat", category="outerwear", style="smart-casual"),
            WardrobeItem(id="canvas-shoes", title="Canvas Sneakers", category="footwear", style="casual"),
            WardrobeItem(id="boots", title="Leather Chelsea Boots", category="footwear", style="smart-casual"),
        ]
    ))

    result = wardrobe_agent_node(state)
    top_ids = [item.id for item in result.filtered_eligible_clothes if item.category == "tops"]
    shoe_ids = [item.id for item in result.filtered_eligible_clothes if item.category == "footwear"]

    assert "knit" in top_ids
    assert "boots" in shoe_ids
    assert "canvas-shoes" not in shoe_ids
    assert "Rainy weather" in (state.context_rules or "")


def test_pink_top_request_matches_light_pink_wardrobe_item(monkeypatch):
    monkeypatch.setattr("agent_graph.visualization_agent_node", lambda state: state)
    response = run_multi_agent_pipeline({
        "occasion": "college",
        "style_preference": "casual",
        "required_top_colors": ["pink"],
        "clothes": [
            {"id": "light-pink-top", "title": "Short Top", "category": "tops", "color": "Light Pink", "style": "smart-casual"},
            {"id": "black-trousers", "title": "Black Straight-Leg Trousers", "category": "bottoms", "color": "Black", "style": "casual"},
            {"id": "white-sneakers", "title": "White Sneakers", "category": "footwear", "color": "White", "style": "casual"},
        ]
    })

    assert response["status"] == "success"
    assert response["outfits"]
    for outfit in response["outfits"]:
        slots = outfit["slotItems"]
        assert slots["topObj"]["id"] == "light-pink-top"
        assert slots["bottomObj"]["id"] == "black-trousers"
        assert slots["shoeObj"]["id"] == "white-sneakers"


def test_scenario_1_wedding_with_ethnic():
    print("\n--- TEST SCENARIO 1: Wedding Event with Ethnic/Festive Wardrobe ---")
    clothes = [
        {"id": 101, "title": "Silk Kurta Set", "category": "tops", "style": "ethnic", "attributes": {"type": "kurta", "style": "ethnic", "formality": 8, "fit": "regular"}},
        {"id": 102, "title": "Churidar Pyjama", "category": "bottoms", "style": "ethnic", "attributes": {"type": "pyjama", "style": "ethnic", "leg_shape": "straight", "formality": 8, "fit": "regular"}},
        {"id": 103, "title": "Traditional Mojari", "category": "footwear", "style": "ethnic", "attributes": {"type": "mojari", "style": "ethnic", "formality": 8}}
    ]
    res = run_multi_agent_pipeline({"occasion": "wedding", "clothes": clothes})
    print(f"Status: {res['status']}, Outfits Count: {res['count']}")
    assert res['count'] >= 1, "Should generate at least 1 suitable wedding outfit for ethnic items"
    print("[OK] Scenario 1 Passed!")

def test_scenario_2_wedding_with_only_office():
    print("\n--- TEST SCENARIO 2: Wedding Event with ONLY Office/Casual Wardrobe (0 Match) ---")
    clothes = [
        {"id": 201, "title": "Formal Blue Office Shirt", "category": "tops", "style": "formal", "attributes": {"type": "shirt", "style": "formal", "formality": 8, "fit": "fitted"}},
        {"id": 202, "title": "Office Trousers", "category": "bottoms", "style": "formal", "attributes": {"type": "trouser", "style": "formal", "leg_shape": "straight", "formality": 8}},
        {"id": 203, "title": "Casual Graphic Tee", "category": "tops", "style": "casual", "attributes": {"type": "t-shirt", "style": "casual", "formality": 3}},
        {"id": 204, "title": "Blue Jeans", "category": "bottoms", "style": "casual", "attributes": {"type": "jeans", "style": "casual", "formality": 4}}
    ]
    res = run_multi_agent_pipeline({"occasion": "wedding", "clothes": clothes})
    print(f"Status: {res['status']}, Message: '{res['message']}', Outfits Count: {res['count']}")
    assert res['status'] == "no_match" and res['count'] == 0, "Should return 0 outfits and no_match status for unsuitable wedding wardrobe"
    print("[OK] Scenario 2 Passed!")

def test_no_match_message_does_not_blame_unavailable_items_when_ready_clothes_are_unsuitable(monkeypatch):
    monkeypatch.setattr("agent_graph.visualization_agent_node", lambda state: state)
    clothes = [
        {"id": "ready-top", "title": "Casual Graphic Tee", "category": "tops", "style": "casual"},
        {"id": "ready-bottom", "title": "Blue Jeans", "category": "bottoms", "style": "casual"},
        {"id": "ready-shoes", "title": "Canvas Sneakers", "category": "footwear", "style": "casual"},
        {"id": "unavailable-item", "title": "Party Dress", "category": "one_piece", "availability_status": "to_wash"},
    ]

    response = run_multi_agent_pipeline({"occasion": "wedding", "clothes": clothes})

    assert response["status"] == "no_match"
    assert "No suitable outfit matched this occasion" in response["message"]
    assert "laundry or ironing status" not in response["message"]

def test_scenario_3_wedding_western_preference():
    print("\n--- TEST SCENARIO 3: Wedding with Explicit Western Formal Preference ---")
    clothes = [
        {"id": 301, "title": "Black Tuxedo Suit Jacket", "category": "tops", "style": "formal", "attributes": {"type": "blazer", "style": "formal", "formality": 9, "fit": "tailored"}},
        {"id": 302, "title": "Tailored Tuxedo Pants", "category": "bottoms", "style": "formal", "attributes": {"type": "trouser", "style": "formal", "leg_shape": "straight", "formality": 9}},
        {"id": 303, "title": "Oxford Leather Shoes", "category": "footwear", "style": "formal", "attributes": {"type": "loafer", "style": "formal", "formality": 9}}
    ]
    res = run_multi_agent_pipeline({"occasion": "wedding", "style_preference": "western formal", "clothes": clothes})
    print(f"Status: {res['status']}, Outfits Count: {res['count']}")
    assert res['count'] >= 1, "Should accept western formal suit for wedding when explicitly requested"
    print("[OK] Scenario 3 Passed!")

def test_scenario_4_job_interview_formal():
    print("\n--- TEST SCENARIO 4: Job Interview with Formal Attire ---")
    clothes = [
        {"id": 401, "title": "White Crisp Oxford Shirt", "category": "tops", "style": "formal", "attributes": {"type": "fitted_shirt", "style": "formal", "formality": 9}},
        {"id": 402, "title": "Navy Pleated Trousers", "category": "bottoms", "style": "formal", "attributes": {"type": "trouser", "style": "formal", "leg_shape": "straight", "formality": 9}},
        {"id": 403, "title": "Black Leather Formal Shoes", "category": "footwear", "style": "formal", "attributes": {"type": "loafer", "style": "formal", "formality": 9}}
    ]
    res = run_multi_agent_pipeline({"occasion": "job interview", "clothes": clothes})
    print(f"Status: {res['status']}, Outfits Count: {res['count']}")
    assert res['count'] >= 1, "Should recommend formal outfit for job interview"
    print("[OK] Scenario 4 Passed!")


def test_formal_one_piece_is_eligible_for_interview_and_presentation(monkeypatch):
    monkeypatch.setattr("agent_graph.visualization_agent_node", lambda state: state)
    clothes = [
        {
            "id": "formal-dress",
            "title": "Formal Interview Dress",
            "category": "one_piece",
            "style": "formal",
            "attributes": {"type": "dress", "style": "formal", "formality": 9},
        },
        {
            "id": "formal-heels",
            "title": "Formal Heels",
            "category": "footwear",
            "style": "formal",
            "attributes": {"type": "heels", "style": "formal", "formality": 9},
        },
    ]

    for occasion in ("job interview", "presentation"):
        response = run_multi_agent_pipeline({"occasion": occasion, "clothes": clothes})
        assert response["status"] == "success"
        assert response["outfits"]
        assert response["outfits"][0]["slotItems"]["topObj"]["id"] == "formal-dress"


def test_formal_wedding_one_piece_is_eligible_at_formality_seven(monkeypatch):
    monkeypatch.setattr("agent_graph.visualization_agent_node", lambda state: state)
    response = run_multi_agent_pipeline({
        "occasion": "wedding",
        "clothes": [
            {
                "id": "wedding-dress",
                "title": "Formal Wedding Guest Dress",
                "category": "one_piece",
                "style": "formal",
                "attributes": {"type": "dress", "style": "formal", "formality": 7},
            },
            {
                "id": "wedding-shoes",
                "title": "Formal Heels",
                "category": "footwear",
                "style": "formal",
            },
        ],
    })

    assert response["status"] == "success"
    assert response["outfits"]


def test_scenario_5_job_interview_casual_rejection():
    print("\n--- TEST SCENARIO 5: Job Interview with Casual Wear (0 Match) ---")
    clothes = [
        {"id": 501, "title": "Hoodie", "category": "tops", "style": "streetwear", "attributes": {"type": "hoodie", "style": "streetwear", "formality": 2}},
        {"id": 502, "title": "Cargo Shorts", "category": "bottoms", "style": "casual", "attributes": {"type": "short", "style": "casual", "formality": 2}},
        {"id": 503, "title": "Chunky Sneakers", "category": "footwear", "style": "casual", "attributes": {"type": "sneaker", "style": "casual", "formality": 2}}
    ]
    res = run_multi_agent_pipeline({"occasion": "job interview", "clothes": clothes})
    print(f"Status: {res['status']}, Outfits Count: {res['count']}")
    assert res['status'] == "no_match" and res['count'] == 0, "Should reject casual hoodie & shorts for job interview"
    print("[OK] Scenario 5 Passed!")

def test_scenario_6_college_campus():
    print("\n--- TEST SCENARIO 6: Daily College Campus Outing ---")
    clothes = [
        {"id": 601, "title": "Graphic Tee", "category": "tops", "style": "casual", "attributes": {"type": "t-shirt", "fit": "regular", "formality": 4, "style": "casual"}},
        {"id": 602, "title": "Relaxed Blue Denim Jeans", "category": "bottoms", "style": "casual", "attributes": {"type": "jeans", "fit": "relaxed", "leg_shape": "straight", "formality": 4, "style": "casual"}},
        {"id": 603, "title": "White Canvas Sneakers", "category": "footwear", "style": "casual", "attributes": {"type": "sneaker", "formality": 4, "style": "casual"}}
    ]
    res = run_multi_agent_pipeline({"occasion": "college", "clothes": clothes})
    print(f"Status: {res['status']}, Outfits Count: {res['count']}")
    assert res['count'] >= 1, "Should generate casual outfit for college"
    print("[OK] Scenario 6 Passed!")

def test_scenario_7_custom_event():
    print("\n--- TEST SCENARIO 7: Custom Event (Art Gallery Opening) ---")
    clothes = [
        {"id": 701, "title": "Black Turtleneck Sweater", "category": "tops", "style": "smart-casual", "attributes": {"type": "sweater", "fit": "fitted", "formality": 6}},
        {"id": 702, "title": "Beige Wide-Leg Trousers", "category": "bottoms", "style": "smart-casual", "attributes": {"type": "wide_leg", "leg_shape": "wide_leg", "rise": "high", "formality": 6}},
        {"id": 703, "title": "Minimalist Loafers", "category": "footwear", "style": "smart-casual", "attributes": {"type": "loafer", "formality": 6}}
    ]
    res = run_multi_agent_pipeline({"occasion": "art gallery opening", "clothes": clothes})
    print(f"Status: {res['status']}, Outfits Count: {res['count']}")
    assert res['count'] >= 1, "Should generate smart casual look for custom event"
    print("[OK] Scenario 7 Passed!")

def test_scenario_8_one_outfit_match():
    print("\n--- TEST SCENARIO 8: Inventory Yielding Exactly 1 Match ---")
    clothes = [
        {"id": 801, "title": "Beige Linen Shirt", "category": "tops", "style": "casual", "attributes": {"type": "shirt", "fit": "regular", "formality": 5}},
        {"id": 802, "title": "Chino Pants", "category": "bottoms", "style": "casual", "attributes": {"type": "trouser", "leg_shape": "straight", "formality": 5}},
        {"id": 803, "title": "Silk Kurta", "category": "tops", "style": "ethnic", "attributes": {"type": "kurta", "formality": 8}},
        {"id": 804, "title": "Cargo Shorts", "category": "bottoms", "style": "casual", "attributes": {"type": "cargo", "formality": 2}}
    ]
    res = run_multi_agent_pipeline({"occasion": "college", "clothes": clothes})
    print(f"Status: {res['status']}, Outfits Count: {res['count']}")
    assert res['count'] == 1, "Should yield exactly 1 match for suitable items"
    print("[OK] Scenario 8 Passed!")

def test_scenario_9_two_outfit_matches():
    print("\n--- TEST SCENARIO 9: Inventory Yielding Exactly 2 Matches ---")
    clothes = [
        {"id": 901, "title": "White Tee", "category": "tops", "style": "casual", "attributes": {"type": "t-shirt", "formality": 4}},
        {"id": 902, "title": "Black Tee", "category": "tops", "style": "casual", "attributes": {"type": "t-shirt", "formality": 4}},
        {"id": 903, "title": "Blue Jeans", "category": "bottoms", "style": "casual", "attributes": {"type": "jeans", "formality": 4}}
    ]
    res = run_multi_agent_pipeline({"occasion": "college", "clothes": clothes})
    print(f"Status: {res['status']}, Outfits Count: {res['count']}")
    assert res['count'] == 2, "Should yield exactly 2 matches for 2 unique tops with 1 bottom"
    print("[OK] Scenario 9 Passed!")

def test_scenario_10_three_outfit_matches():
    print("\n--- TEST SCENARIO 10: Inventory Yielding Exactly 3 Matches ---")
    clothes = [
        {"id": 1001, "title": "White Tee", "category": "tops", "style": "casual", "attributes": {"type": "t-shirt", "formality": 4}},
        {"id": 1002, "title": "Black Tee", "category": "tops", "style": "casual", "attributes": {"type": "t-shirt", "formality": 4}},
        {"id": 1003, "title": "Grey Tee", "category": "tops", "style": "casual", "attributes": {"type": "t-shirt", "formality": 4}},
        {"id": 1004, "title": "Blue Jeans", "category": "bottoms", "style": "casual", "attributes": {"type": "jeans", "formality": 4}}
    ]
    res = run_multi_agent_pipeline({"occasion": "college", "clothes": clothes})
    print(f"Status: {res['status']}, Outfits Count: {res['count']}")
    assert res['count'] == 3, "Should yield max 3 matches"
    print("[OK] Scenario 10 Passed!")

def test_scenario_11_candidate_deduplication():
    print("\n--- TEST SCENARIO 11: Candidate Outfit Deduplication (Same Top & Bottom) ---")
    clothes = [
        {"id": 1101, "title": "White Tee", "category": "tops", "style": "casual", "attributes": {"type": "t-shirt", "formality": 4}},
        {"id": 1102, "title": "Blue Jeans", "category": "bottoms", "style": "casual", "attributes": {"type": "jeans", "formality": 4}},
        {"id": 1103, "title": "Sneakers A", "category": "footwear", "style": "casual", "attributes": {"type": "sneaker", "formality": 4}},
        {"id": 1104, "title": "Sneakers B", "category": "footwear", "style": "casual", "attributes": {"type": "sneaker", "formality": 4}}
    ]
    res = run_multi_agent_pipeline({"occasion": "college", "clothes": clothes})
    print(f"Status: {res['status']}, Outfits Count: {res['count']}")
    assert res['count'] == 1, "Duplicate candidates sharing same Top & Bottom should be deduplicated to 1"
    print("[OK] Scenario 11 Passed!")

def test_scenario_12_empty_wardrobe():
    print("\n--- TEST SCENARIO 12: Empty Wardrobe Inventory Check ---")
    res = run_multi_agent_pipeline({"occasion": "college", "clothes": []})
    print(f"Status: {res['status']}, Outfits Count: {res['count']}")
    assert res['status'] == "no_match" and res['count'] == 0, "Empty wardrobe must return 0 outfits"
    print("[OK] Scenario 12 Passed!")

def test_scenario_13_presentation_formal_and_interview_check():
    print("\n--- TEST SCENARIO 13: Presentation & Job Interview with Formal Shirts/Pants/Heels vs Casual Tees ---")
    clothes = [
        {"id": 1301, "title": "Shirt Formal", "category": "tops", "style": "formal"},
        {"id": 1302, "title": "Shirt Formal Black", "category": "tops", "style": "formal"},
        {"id": 1303, "title": "T-shirt Grey", "category": "tops", "style": "casual"},
        {"id": 1304, "title": "Formal Pant Black", "category": "bottoms", "style": "formal"},
        {"id": 1305, "title": "Danim Pant Oversized", "category": "bottoms", "style": "casual"},
        {"id": 1306, "title": "Formal Heels", "category": "footwear", "style": "formal"}
    ]
    # Test Job Interview
    res_interview = run_multi_agent_pipeline({"occasion": "Job Interview", "clothes": clothes})
    print(f"Interview Status: {res_interview['status']}, Count: {res_interview['count']}")
    assert res_interview['count'] >= 1, "Job interview must recommend formal outfits when formal shirts/pants/heels exist"
    for o in res_interview['outfits']:
        assert "t-shirt" not in o['slots']['top'].lower(), "Job interview must NOT recommend casual t-shirts when formal options exist"

    # Test Presentation
    res_pres = run_multi_agent_pipeline({"occasion": "Presentation", "clothes": clothes})
    print(f"Presentation Status: {res_pres['status']}, Count: {res_pres['count']}")
    assert res_pres['count'] >= 1, "Presentation must recommend formal outfits"
    for o in res_pres['outfits']:
        assert "t-shirt" not in o['slots']['top'].lower(), "Presentation must NOT recommend casual t-shirts when formal options exist"
        assert "danim" not in o['slots']['bottom'].lower(), "Presentation must NOT recommend casual denim when formal options exist"
    print("[OK] Scenario 13 Passed!")

def test_scenario_14_romantic_dinner_date():
    print("\n--- TEST SCENARIO 14: Romantic Dinner Date (Dress/Gown Priority & Chic Tops with Bell-Bottoms) ---")
    clothes = [
        {"id": 1401, "title": "Elegant Black Bodycon Maxi Dress", "category": "tops", "style": "formal"},
        {"id": 1402, "title": "Shirt Stylish", "category": "tops", "style": "smart-casual"},
        {"id": 1403, "title": "Shirt Formal Black", "category": "tops", "style": "formal"},
        {"id": 1404, "title": "Bell Bottom Pant", "category": "bottoms", "style": "smart-casual"},
        {"id": 1405, "title": "Formal Pant Black", "category": "bottoms", "style": "formal"}
    ]
    res = run_multi_agent_pipeline({"occasion": "Romantic Dinner Date", "clothes": clothes})
    print(f"Dinner Date Status: {res['status']}, Count: {res['count']}")
    assert res['count'] >= 1, "Must recommend outfits for romantic dinner date"
    top_look = res['outfits'][0]
    assert "dress" in top_look['slots']['top'].lower() or "bodycon" in top_look['slots']['top'].lower(), "One-piece dress/gown must be top pick for romantic dinner date when available"
    print("[OK] Scenario 14 Passed!")

def test_scenario_15_wedding_prefers_ethnic_over_stylish_separates():
    print("\n--- TEST SCENARIO 15: Wedding must pick lehenga/one-piece, not stylish top + pants ---")
    clothes = [
        {"id": 1501, "title": "Red Embroidered Lehenga One Piece", "category": "one_piece", "style": "ethnic"},
        {"id": 1502, "title": "Shirt Stylish", "category": "tops", "style": "smart-casual"},
        {"id": 1503, "title": "Stylish Top", "category": "tops", "style": "smart-casual"},
        {"id": 1504, "title": "Trouser Pant", "category": "bottoms", "style": "casual"},
        {"id": 1505, "title": "Formal Pant Black", "category": "bottoms", "style": "formal"},
        {"id": 1506, "title": "Gold Ethnic Juttis", "category": "footwear", "style": "ethnic"}
    ]
    res = run_multi_agent_pipeline({"occasion": "wedding", "clothes": clothes})
    print(f"Wedding mixed Status: {res['status']}, Count: {res['count']}")
    assert res['count'] >= 1, "Wedding wardrobe with lehenga must return ethnic outfits"
    for o in res['outfits']:
        top = o['slots']['top'].lower()
        assert "lehenga" in top or "one piece" in top or "ethnic" in top, f"Wedding look should be ethnic/one-piece, got {o['slots']}"
        assert "stylish" not in top
    print("[OK] Scenario 15 Passed!")

def test_scenario_16_interview_prefers_formal_shirt_pants_heels():
    print("\n--- TEST SCENARIO 16: Job interview must pick formal shirt + pants + heels ---")
    clothes = [
        {"id": 1601, "title": "Shirt Stylish", "category": "tops", "style": "smart-casual"},
        {"id": 1602, "title": "White Formal Shirt", "category": "tops", "style": "formal"},
        {"id": 1603, "title": "Stylish Top", "category": "tops", "style": "smart-casual"},
        {"id": 1604, "title": "Formal Pant Black", "category": "bottoms", "style": "formal"},
        {"id": 1605, "title": "Trouser Pant", "category": "bottoms", "style": "casual"},
        {"id": 1606, "title": "Formal Heels", "category": "footwear", "style": "formal"},
        {"id": 1607, "title": "Chunky Sneakers", "category": "footwear", "style": "sporty"}
    ]
    res = run_multi_agent_pipeline({"occasion": "job interview", "clothes": clothes})
    print(f"Interview mixed Status: {res['status']}, Count: {res['count']}")
    assert res['count'] >= 1, "Interview wardrobe with formal shirt/pants/heels must recommend them"
    for o in res['outfits']:
        top = o['slots']['top'].lower()
        bottom = o['slots']['bottom'].lower()
        shoes = o['slots']['footwear'].lower()
        assert "formal shirt" in top or ("formal" in top and "shirt" in top), f"Interview top should be formal shirt, got {top}"
        assert "stylish" not in top
        assert "formal pant" in bottom or ("formal" in bottom and "pant" in bottom)
        assert "heel" in shoes or "formal" in shoes
        assert "sneaker" not in shoes
    print("[OK] Scenario 16 Passed!")

def test_scenario_17_wedding_rejects_ethnic_top_with_western_trousers():
    print("\n--- TEST SCENARIO 17: Wedding rejects ethnic top paired with western trousers ---")
    clothes = [
        {"id": 1701, "title": "Embroidered Ethnic Kurti", "category": "tops", "style": "ethnic"},
        {"id": 1702, "title": "Tailored Formal Trousers", "category": "bottoms", "style": "formal"},
        {"id": 1703, "title": "Gold Ethnic Juttis", "category": "footwear", "style": "ethnic"}
    ]
    res = run_multi_agent_pipeline({"occasion": "wedding", "clothes": clothes})
    assert res["status"] == "no_match" and res["count"] == 0, (
        "An ethnic top alone must not make a western-trouser outfit wedding-appropriate"
    )
    print("[OK] Scenario 17 Passed!")

def test_scenario_18_interview_rejects_generic_formal_top():
    print("\n--- TEST SCENARIO 18: Interview rejects a generic formal top ---")
    clothes = [
        {"id": 1801, "title": "Stylish Formal Top", "category": "tops", "style": "formal"},
        {"id": 1802, "title": "Formal Pant Black", "category": "bottoms", "style": "formal"},
        {"id": 1803, "title": "Formal Heels", "category": "footwear", "style": "formal"}
    ]
    res = run_multi_agent_pipeline({"occasion": "job interview", "clothes": clothes})
    assert res["status"] == "no_match" and res["count"] == 0, (
        "Interview tops must have a shirt or blouse shape, not merely be labeled formal"
    )
    print("[OK] Scenario 18 Passed!")

def test_scenario_19_interview_requires_formal_footwear():
    print("\n--- TEST SCENARIO 19: Interview rejects missing or casual footwear ---")
    clothes = [
        {"id": 1901, "title": "White Formal Shirt", "category": "tops", "style": "formal"},
        {"id": 1902, "title": "Formal Pant Black", "category": "bottoms", "style": "formal"},
        {"id": 1903, "title": "Casual Sandals", "category": "footwear", "style": "casual"}
    ]
    res = run_multi_agent_pipeline({"occasion": "job interview", "clothes": clothes})
    assert res["status"] == "no_match" and res["count"] == 0, (
        "Interview outfits must not be returned without formal footwear"
    )
    without_shoes = [item for item in clothes if item["category"] != "footwear"]
    res = run_multi_agent_pipeline({"occasion": "job interview", "clothes": without_shoes})
    assert res["status"] == "no_match" and res["count"] == 0, (
        "Interview outfits must not be returned without footwear"
    )
    print("[OK] Scenario 19 Passed!")

def test_scenario_20_wedding_occasion_search_does_not_skip_ethnic_dress():
    import random
    random.seed(42)
    clothes = [
        {"id": 2001, "title": "Embroidered Wedding Lehenga", "category": "one_piece", "style": "ethnic"},
        *[
            {"id": 2010 + i, "title": f"Casual Tee {i}", "category": "tops", "style": "casual"}
            for i in range(25)
        ],
        *[
            {"id": 2040 + i, "title": f"Casual Pant {i}", "category": "bottoms", "style": "casual"}
            for i in range(25)
        ],
        {"id": 2070, "title": "Ethnic Heels", "category": "footwear", "style": "ethnic"}
    ]
    res = run_multi_agent_pipeline({"occasion": "wedding", "clothes": clothes})
    assert res["count"] >= 1
    assert all("lehenga" in outfit["slots"]["top"].lower() for outfit in res["outfits"])
    print("[OK] Scenario 20 Passed!")

def test_scenario_21_interview_occasion_search_and_outerwear():
    import random
    random.seed(42)
    clothes = [
        {"id": 2101, "title": "White Formal Shirt", "category": "tops", "style": "formal"},
        *[
            {"id": 2110 + i, "title": f"Stylish Top {i}", "category": "tops", "style": "smart-casual"}
            for i in range(25)
        ],
        {"id": 2140, "title": "Formal Pant Black", "category": "bottoms", "style": "formal"},
        *[
            {"id": 2150 + i, "title": f"Casual Pant {i}", "category": "bottoms", "style": "casual"}
            for i in range(25)
        ],
        {"id": 2180, "title": "Formal Heels", "category": "footwear", "style": "formal"},
        {"id": 2181, "title": "Denim Jacket Black", "category": "outerwear", "style": "casual"},
        {"id": 2182, "title": "Formal Blazer", "category": "outerwear", "style": "formal"}
    ]
    res = run_multi_agent_pipeline({"occasion": "job interview", "clothes": clothes})
    assert res["count"] >= 1
    for outfit in res["outfits"]:
        assert "formal shirt" in outfit["slots"]["top"].lower()
        assert "formal pant" in outfit["slots"]["bottom"].lower()
        assert "heel" in outfit["slots"]["footwear"].lower()
        assert "denim" not in outfit["slots"]["outerwear"].lower()
    print("[OK] Scenario 21 Passed!")

def test_scenario_22_dinner_date_prioritizes_one_piece_over_separates():
    import random
    random.seed(42)
    clothes = [
        {"id": 2201, "title": "Elegant Dinner Date Dress", "category": "one_piece", "style": "smart-casual"},
        *[
            {"id": 2210 + i, "title": f"Casual Top {i}", "category": "tops", "style": "casual"}
            for i in range(25)
        ],
        *[
            {"id": 2240 + i, "title": f"Casual Pant {i}", "category": "bottoms", "style": "casual"}
            for i in range(25)
        ]
    ]
    res = run_multi_agent_pipeline({"occasion": "dinner date", "clothes": clothes})
    assert res["count"] >= 1
    assert all("dinner date dress" in outfit["slots"]["top"].lower() for outfit in res["outfits"])
    print("[OK] Scenario 22 Passed!")

def test_scenario_23_generic_one_piece_is_not_ethnic_wedding_wear():
    from fashion.styling_rules import is_ethnic_garment, is_wedding_appropriate_look
    party_dress = {
        "title": "Party Dress",
        "category": "one_piece",
        "style": "smart-casual",
        "formality": 7
    }
    assert not is_ethnic_garment(party_dress)
    assert not is_wedding_appropriate_look(party_dress)
    clothes = [
        {"id": 2301, "title": "Embroidered Wedding Dress", "category": "one_piece", "style": "ethnic"},
        {"id": 2302, "title": "Party Dress", "category": "one_piece", "style": "smart-casual", "attributes": {"formality": 7}},
        {"id": 2303, "title": "Traditional Heels", "category": "footwear", "style": "ethnic"}
    ]
    res = run_multi_agent_pipeline({"occasion": "wedding", "clothes": clothes})
    assert res["count"] == 1
    assert "wedding dress" in res["outfits"][0]["slots"]["top"].lower()
    print("[OK] Scenario 23 Passed!")

def run_all_scenarios():
    print("=" * 80)
    print("RUNNING COMPREHENSIVE FASHION COMPATIBILITY TEST SUITE")
    print("=" * 80)
    test_scenario_1_wedding_with_ethnic()
    test_scenario_2_wedding_with_only_office()
    test_scenario_3_wedding_western_preference()
    test_scenario_4_job_interview_formal()
    test_scenario_5_job_interview_casual_rejection()
    test_scenario_6_college_campus()
    test_scenario_7_custom_event()
    test_scenario_8_one_outfit_match()
    test_scenario_9_two_outfit_matches()
    test_scenario_10_three_outfit_matches()
    test_scenario_11_candidate_deduplication()
    test_scenario_12_empty_wardrobe()
    test_scenario_13_presentation_formal_and_interview_check()
    test_scenario_14_romantic_dinner_date()
    test_scenario_15_wedding_prefers_ethnic_over_stylish_separates()
    test_scenario_16_interview_prefers_formal_shirt_pants_heels()
    test_scenario_17_wedding_rejects_ethnic_top_with_western_trousers()
    test_scenario_18_interview_rejects_generic_formal_top()
    test_scenario_19_interview_requires_formal_footwear()
    test_scenario_20_wedding_occasion_search_does_not_skip_ethnic_dress()
    test_scenario_21_interview_occasion_search_and_outerwear()
    test_scenario_22_dinner_date_prioritizes_one_piece_over_separates()
    test_scenario_23_generic_one_piece_is_not_ethnic_wedding_wear()
    print("\n" + "=" * 80)
    print("ALL TEST SCENARIOS PASSED!")
    print("=" * 80)

if __name__ == "__main__":
    run_all_scenarios()
