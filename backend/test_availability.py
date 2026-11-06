import os
import sys
from datetime import date, datetime, timedelta

import pytest

sys.path.insert(0, os.path.dirname(__file__))

import database as db
from agent_graph import run_multi_agent_pipeline
from voice_agent_graph import (
    VoiceAgentState,
    intent_understanding_node,
    status_update_node,
)
import voice_agent_graph as voice
from voice_agent_graph import run_voice_agent_pipeline
from fastapi import HTTPException
import main as api


def setup_test_database(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "availability.db"))
    db.init_db()


def test_empty_legacy_statuses_migrate_to_ready(tmp_path, monkeypatch):
    setup_test_database(tmp_path, monkeypatch)
    conn = db.get_connection()
    conn.execute(
        "UPDATE clothes SET availability_status = '', ironing_status = '' WHERE id = '101'"
    )
    conn.commit()
    conn.close()

    db.init_db()

    item = db.get_clothing_item("101")
    assert item["availability_status"] == "ready"
    assert item["ironing_status"] == "ready"
    assert next(item for item in db.get_all_clothes(1) if item["id"] == "101")["ironing_status"] == "ready"


@pytest.mark.parametrize(
    ("message", "availability", "ironing"),
    [
        ("My blue shirt is in the washing machine", "in_wash", None),
        ("My black trousers are drying", "drying", None),
        ("My white shirt is ready to wear", "ready", "ready"),
        ("My black shoes are missing", "missing", None),
        ("My jacket needs ironing", None, "needs_ironing"),
        ("My shirt should be ready by 7 PM", None, None),
        ("Don't use clothes that need ironing tomorrow", None, None),
    ],
)
def test_clothing_status_intents(message, availability, ironing):
    state = intent_understanding_node(VoiceAgentState(user_message=message))

    if "don't use" in message.lower():
        assert state.intent == "modification"
        assert state.status_change is None
    else:
        assert state.intent == "status_update"
        assert state.status_change is not None
        assert state.status_change.get("availability_status") == availability
        assert state.status_change.get("ironing_status") == ironing
        if "7 PM" in message:
            assert state.status_change["expected_available_at"].endswith("19:00:00")


def test_status_update_resolves_ambiguity_without_mutating_items(monkeypatch):
    clothes = [
        {"id": "shoe-a", "title": "Black Leather Sneakers", "category": "footwear", "color": "Black"},
        {"id": "shoe-b", "title": "Black Leather Loafers", "category": "footwear", "color": "Black"},
    ]
    monkeypatch.setattr(db, "get_all_clothes", lambda user_id=1: clothes)
    state = VoiceAgentState(
        user_message="My black shoes are missing",
        intent="status_update",
        status_change={"garment_description": "black shoes", "availability_status": "missing"},
    )

    state = status_update_node(state)

    assert state.response_type == "error"
    assert state.status_update_result["reason"] == "ambiguous"
    assert "Which one" in state.agent_response


def test_availability_changes_persist_and_are_owner_scoped(tmp_path, monkeypatch):
    setup_test_database(tmp_path, monkeypatch)
    created = db.add_clothing_item({
        "id": "private-item",
        "title": "Blue Linen Shirt",
        "category": "tops",
        "color": "Blue",
    }, user_id=2)

    updated = db.update_clothing_availability(
        created["id"], 2, "in_wash", expected_available_at="2030-01-01T19:00:00"
    )

    assert updated["availability_status"] == "in_wash"
    assert db.get_clothing_item(created["id"], 1) is None
    assert created["id"] not in {item["id"] for item in db.get_all_clothes(1)}
    assert db.get_clothing_item(created["id"], 2)["expected_available_at"] == "2030-01-01T19:00:00"


def test_laundry_reminder_preference_persists_with_garment(tmp_path, monkeypatch):
    setup_test_database(tmp_path, monkeypatch)
    db.add_clothing_item({
        "id": "laundry-alert-shirt",
        "title": "Laundry Alert Shirt",
        "category": "tops",
        "color": "Blue",
    })

    updated = db.update_clothing_availability(
        "laundry-alert-shirt",
        1,
        "drying",
        expected_available_at="2026-10-20T08:00:00",
        notify_when_ready=True,
    )

    assert updated["notify_when_ready"] is True
    persisted = next(item for item in db.get_all_clothes(1) if item["id"] == "laundry-alert-shirt")
    assert persisted["notify_when_ready"] is True


def test_availability_api_validates_status_and_ownership(tmp_path, monkeypatch):
    setup_test_database(tmp_path, monkeypatch)

    updated = api.update_clothing_availability(
        "101",
        api.AvailabilityUpdateRequest(
            availability_status="in_wash",
            expected_available_at="2030-01-01T19:00:00",
            user_id=1,
        ),
    )
    assert updated["item"]["availability_status"] == "in_wash"
    assert db.get_clothing_item("101")["expected_available_at"] == "2030-01-01T19:00:00"

    with pytest.raises(HTTPException) as invalid_status:
        api.update_clothing_availability(
            "101",
            api.AvailabilityUpdateRequest(availability_status="clean", user_id=1),
        )
    assert invalid_status.value.status_code == 422

    with pytest.raises(HTTPException) as wrong_user:
        api.update_clothing_availability(
            "101",
            api.AvailabilityUpdateRequest(availability_status="ready", user_id=2),
        )
    assert wrong_user.value.status_code == 403


def test_typed_voice_pipeline_persists_a_status_update(tmp_path, monkeypatch):
    setup_test_database(tmp_path, monkeypatch)
    db.add_clothing_item({
        "id": "blue-cotton-shirt",
        "title": "Blue Cotton Shirt",
        "category": "tops",
        "color": "Blue",
    })
    monkeypatch.setattr(
        voice,
        "_understand_stylist_message",
        lambda message, saved_state: voice._local_structured_intent(message, saved_state),
    )

    response = run_voice_agent_pipeline(
        "My blue shirt is in the washing machine",
        conversation_id="status-through-chat",
    )

    assert response["response_type"] == "status_update"
    assert db.get_clothing_item("blue-cotton-shirt")["availability_status"] == "in_wash"
    assert "Blue Cotton Shirt" in response["agent_response"]


def test_chat_wear_confirmation_creates_the_in_app_laundry_check(tmp_path, monkeypatch):
    setup_test_database(tmp_path, monkeypatch)
    monkeypatch.setattr(
        voice,
        "_understand_stylist_message",
        lambda message, saved_state: voice._local_structured_intent(message, saved_state),
    )
    outfit = {
        "id": "confirmed-look",
        "title": "Planned campus look",
        "slotItems": {
            "topObj": {"id": "101"},
            "bottomObj": {"id": "104"},
            "shoeObj": {"id": "106"},
        },
    }

    response = run_voice_agent_pipeline(
        "I wore this outfit today",
        conversation_id="wore-outfit-chat",
        context_outfit=outfit,
    )

    assert response["response_type"] == "wear_reminder"
    assert {garment["id"] for garment in db.get_pending_wear_events(1)[0]["garments"]} == {"101", "104"}
    assert db.get_clothing_item("101")["availability_status"] == "ready"


def test_chat_not_worn_confirmation_does_not_start_laundry_work(tmp_path, monkeypatch):
    setup_test_database(tmp_path, monkeypatch)
    monkeypatch.setattr(
        voice,
        "_understand_stylist_message",
        lambda message, saved_state: voice._local_structured_intent(message, saved_state),
    )
    outfit = {"id": "not-worn-look", "title": "Planned look", "slotItems": {"topObj": {"id": "101"}}}

    response = run_voice_agent_pipeline(
        "I didn't wear the outfit we planned",
        conversation_id="not-worn-chat",
        context_outfit=outfit,
    )

    assert response["response_type"] == "text"
    assert db.get_pending_wear_events(1) == []
    assert db.get_clothing_item("101")["availability_status"] == "ready"


def test_wear_confirmation_selects_the_matching_occasion_from_multiple_daily_plans(tmp_path, monkeypatch):
    setup_test_database(tmp_path, monkeypatch)
    monkeypatch.setattr(
        voice,
        "_understand_stylist_message",
        lambda message, saved_state: voice._local_structured_intent(message, saved_state),
    )
    day_id = datetime.now().strftime("%a").lower()[:3]
    db.schedule_weekday_outfit(
        day_id,
        1,
        {"id": "college-look", "title": "College look", "slotItems": {"topObj": {"id": "101"}}},
        "daily",
        "College",
    )
    db.schedule_weekday_outfit(
        day_id,
        1,
        {"id": "dinner-look", "title": "Dinner look", "slotItems": {"topObj": {"id": "102"}}},
        "occasion",
        "Dinner date",
        ["102"],
    )

    response = run_voice_agent_pipeline(
        "I wore the planned dinner date look today",
        conversation_id="wear-multiple-occasion-plans",
    )

    assert response["response_type"] == "wear_reminder"
    pending = db.get_pending_wear_events(1)
    assert len(pending) == 1
    assert pending[0]["outfit_title"] == "Dinner look"


def test_readiness_estimate_prompts_once_and_never_auto_marks_ready(tmp_path, monkeypatch):
    setup_test_database(tmp_path, monkeypatch)
    db.update_clothing_availability("101", 1, "in_wash", expected_available_at="2000-01-01T00:00:00")
    monkeypatch.setattr(
        voice,
        "_understand_stylist_message",
        lambda message, saved_state: voice._local_structured_intent(message, saved_state),
    )

    def pipeline(request):
        top = next((item for item in request["clothes"] if str(item.get("id")) == "101"), None)
        if (
            top
            and top["availability_status"] == "ready"
            and "white" in request.get("required_top_colors", [])
            and "101" not in request.get("excluded_item_ids", [])
        ):
            return {"outfits": [{
                "id": "white-shirt-look",
                "title": "White Shirt Look",
                "slotItems": {"topObj": {"id": "101"}},
            }]}
        return {"outfits": []}

    monkeypatch.setattr(voice, "run_multi_agent_pipeline", pipeline)
    first = run_voice_agent_pipeline(
        "I want a white top for college",
        conversation_id="readiness-confirmation",
    )

    assert first["response_type"] == "readiness_confirmation"
    assert first["outfits"] == []
    assert first["readiness_confirmation"]["item_id"] == "101"
    assert db.get_clothing_item("101")["availability_status"] == "in_wash"

    confirmed = run_voice_agent_pipeline(
        "yes",
        conversation_id="readiness-confirmation",
    )
    assert confirmed["response_type"] == "outfit"
    assert db.get_clothing_item("101")["availability_status"] == "ready"


def test_readiness_denial_keeps_item_blocked_and_does_not_repeat_prompt(tmp_path, monkeypatch):
    setup_test_database(tmp_path, monkeypatch)
    db.update_clothing_availability("101", 1, "drying", expected_available_at="2000-01-01T00:00:00")
    monkeypatch.setattr(
        voice,
        "_understand_stylist_message",
        lambda message, saved_state: voice._local_structured_intent(message, saved_state),
    )
    def pipeline(request):
        top = next((item for item in request["clothes"] if str(item.get("id")) == "101"), None)
        if (
            top
            and top["availability_status"] == "ready"
            and "white" in request.get("required_top_colors", [])
            and "101" not in request.get("excluded_item_ids", [])
        ):
            return {"outfits": [{
                "id": "white-shirt-look",
                "title": "White Shirt Look",
                "slotItems": {"topObj": {"id": "101"}},
            }]}
        return {"outfits": []}

    monkeypatch.setattr(voice, "run_multi_agent_pipeline", pipeline)

    first = run_voice_agent_pipeline(
        "I want a white top for college",
        conversation_id="readiness-denial",
    )
    assert first["response_type"] == "readiness_confirmation"
    denied = run_voice_agent_pipeline("no", conversation_id="readiness-denial")

    assert denied["response_type"] == "no_match"
    assert denied["readiness_confirmation"] is None
    assert db.get_clothing_item("101")["availability_status"] == "drying"


def test_unworn_outfit_does_not_create_laundry_work_and_duplicate_wear_is_prevented(tmp_path, monkeypatch):
    setup_test_database(tmp_path, monkeypatch)
    outfit = {"id": "daily-look", "title": "Campus look"}

    not_worn = db.create_outfit_wear_event(1, outfit, ["101", "102"], "2026-10-18", "sun", False)
    assert not_worn["status"] == "not_worn"
    assert db.get_pending_wear_events(1) == []
    assert db.get_clothing_item("101")["availability_status"] == "ready"

    worn = db.create_outfit_wear_event(1, outfit, ["101", "102"], "2026-10-18", "sun", True)
    repeated = db.create_outfit_wear_event(1, outfit, ["101", "102"], "2026-10-18", "sun", True)
    assert worn["id"] == not_worn["id"]
    assert worn["status"] == "pending"
    assert worn["duplicate"] is False
    assert repeated["duplicate"] is True


def test_worn_clothing_remains_recommendable_until_marked_unavailable(tmp_path, monkeypatch):
    setup_test_database(tmp_path, monkeypatch)
    wear_date = datetime.now().date()
    outfit = {"id": "cooldown-look", "title": "Campus look"}

    event = db.create_outfit_wear_event(
        1, outfit, ["101", "106", "108", "109"], wear_date.isoformat(), "mon"
    )

    assert event["status"] == "pending"
    assert {garment["id"] for garment in db.get_pending_wear_events(1)[0]["garments"]} == {"101"}
    assert db.get_clothing_item("101")["wear_cooldown_until"] is None
    for item_id in ("106", "108", "109"):
        assert db.get_clothing_item(item_id)["wear_cooldown_until"] is None

    planned = {
        "id": "cooldown-look",
        "slotItems": {"topObj": {"id": "101"}, "shoeObj": {"id": "106"}},
    }
    scheduled = db.schedule_weekday_outfit("thu", 1, planned, "occasion", "College", ["101"])
    assert scheduled["outfit"] == planned
    assert db.get_clothing_item("101")["wear_cooldown_until"] is None


def test_ready_garment_is_recommendable_even_with_legacy_cooldown(tmp_path, monkeypatch):
    setup_test_database(tmp_path, monkeypatch)
    cooldown_until = (datetime.now().date() + timedelta(days=2)).isoformat()
    connection = db.get_connection()
    connection.execute(
        "UPDATE clothes SET wear_cooldown_until = ? WHERE id = ? AND user_id = ?",
        (cooldown_until, "101", 1),
    )
    connection.commit()
    connection.close()

    response = run_multi_agent_pipeline({
        "user_id": 1,
        "occasion": "college",
        "clothes": db.get_all_clothes(1),
        "required_top_colors": ["white"],
    })

    assert response["count"] > 0
    assert any(
        outfit["slotItems"]["topObj"]["id"] == "101"
        for outfit in response["outfits"]
    )


def test_occasion_schedule_requires_readiness_and_rejects_unavailable_accessories(tmp_path, monkeypatch):
    setup_test_database(tmp_path, monkeypatch)
    outfit = {
        "id": "verified-look",
        "slotItems": {"topObj": {"id": "101"}, "shoeObj": {"id": "106"}},
    }

    with pytest.raises(ValueError, match="Confirm that every clothing garment"):
        db.schedule_weekday_outfit("mon", 1, outfit, "occasion", "College")

    db.update_clothing_availability("106", 1, "missing")
    with pytest.raises(ValueError, match="not currently available"):
        db.schedule_weekday_outfit("mon", 1, outfit, "occasion", "College", ["101"])


def test_laundry_answers_apply_independently_and_unanswered_items_stay_unchanged(tmp_path, monkeypatch):
    setup_test_database(tmp_path, monkeypatch)
    db.update_clothing_availability("102", 1, "damaged")
    outfit = {"id": "evening-look", "title": "Dinner look"}
    event = db.create_outfit_wear_event(1, outfit, ["101", "102", "103"], "2026-10-18")

    saved = db.submit_wear_event_answers(1, event["id"], [
        {"item_id": "101", "actually_worn": True, "in_laundry": True},
        {"item_id": "102", "actually_worn": True, "in_laundry": False},
        {"item_id": "103", "actually_worn": True, "in_laundry": None},
    ])

    assert saved is True
    assert db.get_clothing_item("101")["availability_status"] == "to_wash"
    assert db.get_clothing_item("102")["availability_status"] == "damaged"
    assert db.get_clothing_item("103")["availability_status"] == "ready"
    assert db.get_clothing_item("101")["usageCount"] == 5
    assert db.get_clothing_item("102")["usageCount"] == 13
    assert db.get_pending_wear_events(1) == []


def test_marking_one_item_unavailable_removes_only_its_future_plans(tmp_path, monkeypatch):
    setup_test_database(tmp_path, monkeypatch)
    plan_date = date.today() + timedelta(days=7)
    day_id = plan_date.strftime("%a").lower()[:3]
    affected = db.schedule_weekday_outfit(
        day_id, 1,
        {"id": "affected", "slotItems": {"topObj": {"id": "101"}}},
        "daily", "College", plan_date=plan_date.isoformat()
    )
    unaffected = db.schedule_weekday_outfit(
        day_id, 1,
        {"id": "unaffected", "slotItems": {"topObj": {"id": "102"}}},
        "daily", "Dinner date", plan_date=plan_date.isoformat()
    )

    removed = db.remove_future_outfits_using_item("101", 1)

    assert removed == [affected["schedule_id"]]
    assert db.get_weekday_outfit(affected["schedule_id"], 1) is None
    assert db.get_weekday_outfit(unaffected["schedule_id"], 1)["outfit"]["id"] == "unaffected"


@pytest.mark.parametrize("blocked_status", ["to_wash", "in_wash", "drying", "missing", "damaged", "borrowed", "unavailable"])
def test_blocked_top_is_never_recommended_even_after_estimated_ready_time(tmp_path, monkeypatch, blocked_status):
    setup_test_database(tmp_path, monkeypatch)
    db.update_clothing_availability(
        "101", 1, blocked_status, expected_available_at="2000-01-01T00:00:00"
    )

    response = run_multi_agent_pipeline({
        "user_id": 1,
        "occasion": "college",
        "clothes": db.get_all_clothes(1),
        "required_top_colors": ["white"],
    })

    assert response["count"] == 0
    assert response["outfits"] == []


def test_recommendations_preserve_required_top_color_and_ready_constraint(tmp_path, monkeypatch):
    setup_test_database(tmp_path, monkeypatch)
    clothes = db.get_all_clothes(1)
    blue_top = db.add_clothing_item({
        "id": "ready-blue-top",
        "title": "Blue Cotton Shirt",
        "category": "tops",
        "color": "Blue",
        "availability_status": "ready",
        "ironing_status": "ready",
    })
    clothes.insert(0, blue_top)
    db.update_clothing_availability("102", 1, "to_wash")

    response = run_multi_agent_pipeline({
        "user_id": 1,
        "occasion": "college",
        "clothes": clothes,
        "required_top_colors": ["blue"],
    })

    assert response["count"] > 0
    for outfit in response["outfits"]:
        top = outfit["slotItems"]["topObj"]
        assert top["color"].lower() == "blue"
        assert top["availability_status"] == "ready"
