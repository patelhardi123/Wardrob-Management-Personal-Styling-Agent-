import pytest
from fastapi import HTTPException
from datetime import date, timedelta

import database as db
import main as api


@pytest.mark.parametrize("day_id", ["mon", "tue", "wed", "thu", "fri", "sat", "sun"])
def test_weekday_schedule_allows_multiple_occasion_looks_per_day_and_removes_one(tmp_path, monkeypatch, day_id):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "wardrobe.db"))
    db.ensure_stylist_tables()

    outfit = {"id": f"{day_id}-college", "title": f"{day_id} College Look"}
    scheduled = db.schedule_weekday_outfit(day_id, 1, outfit, "voice", "College")

    assert scheduled["outfit"] == outfit
    assert scheduled["source"] == "voice"
    assert scheduled["occasion"] == "College"
    assert db.get_weekday_outfits(1)[day_id][0]["outfit"] == outfit

    evening_outfit = {"id": f"{day_id}-dinner", "title": f"{day_id} Dinner Look"}
    evening = db.schedule_weekday_outfit(day_id, 1, evening_outfit, "occasion", "Dinner date")
    entries = db.get_weekday_outfits(1)[day_id]
    assert len(entries) == 2
    assert {entry["occasion"] for entry in entries} == {"College", "Dinner date"}

    assert db.remove_weekday_outfit(scheduled["schedule_id"], 1)
    assert len(db.get_weekday_outfits(1)[day_id]) == 1
    assert db.get_weekday_outfits(1)[day_id][0]["schedule_id"] == evening["schedule_id"]
    assert db.remove_weekday_outfit(evening["schedule_id"], 1)
    assert db.get_weekday_outfits(1) == {}


def test_weekday_schedule_replacement_requires_the_expected_current_outfit(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "wardrobe.db"))
    db.ensure_stylist_tables()
    original = {"id": "thursday-old", "title": "Look with bag"}
    updated = {"id": "thursday-new", "title": "Updated look without bag"}
    scheduled = db.schedule_weekday_outfit("thu", 1, original, "voice", "Dinner date")

    assert db.replace_weekday_outfit(scheduled["schedule_id"], 1, "wrong-id", updated, "voice") is None
    assert db.get_weekday_outfits(1)["thu"][0]["outfit"] == original

    replaced = db.replace_weekday_outfit(scheduled["schedule_id"], 1, "thursday-old", updated, "voice")
    assert replaced["outfit"] == updated
    assert replaced["occasion"] == "Dinner date"
    assert db.get_weekday_outfits(1)["thu"][0]["outfit"] == updated


def test_weekday_schedule_persists_iso_date_and_confirmation_status(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "wardrobe.db"))
    db.ensure_stylist_tables()
    plan_date = date.today() + timedelta(days=7)
    day_id = plan_date.strftime("%a").lower()[:3]

    scheduled = db.schedule_weekday_outfit(
        day_id, 1, {"id": "dated-look"}, "voice", "College", plan_date=plan_date.isoformat()
    )

    assert scheduled["plan_date"] == plan_date.isoformat()
    assert scheduled["confirmation_status"] == "awaiting"
    assert db.get_weekday_outfits(1)[day_id][0]["confirmation_status"] == "awaiting"
    assert db.confirm_weekday_outfit(scheduled["schedule_id"], 1, False)
    assert db.get_weekday_outfit(scheduled["schedule_id"], 1)["confirmation_status"] == "not_worn"


def test_future_outfit_cannot_be_confirmed_as_worn(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "wardrobe.db"))
    db.ensure_stylist_tables()
    plan_date = date.today() + timedelta(days=1)
    day_id = plan_date.strftime("%a").lower()[:3]
    outfit = {"id": "future-look"}
    scheduled = db.schedule_weekday_outfit(
        day_id, 1, outfit, "daily", "College", plan_date=plan_date.isoformat()
    )
    request = api.OutfitWearEventRequest(
        outfit=outfit,
        item_ids=[],
        wear_date=plan_date.isoformat(),
        planned_day=day_id,
        schedule_id=scheduled["schedule_id"],
        worn=True,
    )

    with pytest.raises(HTTPException) as error:
        api.create_outfit_wear_event(request)

    assert error.value.status_code == 422
    assert db.get_weekday_outfit(scheduled["schedule_id"], 1)["confirmation_status"] == "awaiting"


def test_weekday_schedule_migrates_existing_single_look_records(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "wardrobe.db"))
    connection = db.get_connection()
    connection.execute("""
        CREATE TABLE weekday_outfits (
            user_id INTEGER NOT NULL,
            day_id TEXT NOT NULL,
            outfit_json TEXT NOT NULL,
            source TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, day_id)
        )
    """)
    connection.execute(
        "INSERT INTO weekday_outfits (user_id, day_id, outfit_json, source) VALUES (?, ?, ?, ?)",
        (1, "sat", '{"id":"old-saturday","title":"Saturday look"}', "voice")
    )
    connection.commit()
    connection.close()

    db.ensure_stylist_tables()

    migrated = db.get_weekday_outfits(1)["sat"]
    assert len(migrated) == 1
    assert migrated[0]["occasion"] == "Daily look"
    assert migrated[0]["outfit"]["id"] == "old-saturday"
    assert migrated[0]["plan_date"]
    assert migrated[0]["confirmation_status"] == "awaiting"
