"""Failed writes must never block subsequent assistant or planner requests."""
import sqlite3
from concurrent.futures import ThreadPoolExecutor

import pytest
import database as db


def test_failed_garment_insert_releases_write_lock(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "wardrobe.db"))
    db.init_db()
    garment = {"id": "duplicate", "title": "Test shirt"}
    db.add_clothing_item(garment)
    with pytest.raises(sqlite3.IntegrityError) as failure:
        db.add_clothing_item(garment)
    # Keep the traceback alive: cleanup must not depend on garbage collection.
    assert failure.value is not None
    with ThreadPoolExecutor(max_workers=2) as executor:
        executor.submit(db.ensure_stylist_tables).result(timeout=3)
        executor.submit(db.save_stylist_conversation, "test", 1, {}, []).result(timeout=3)
    assert db.get_stylist_conversation("test", 1) is not None


def test_plan_reads_continue_while_another_connection_writes(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "wardrobe.db"))
    db.init_db()
    writer = db.get_connection()
    try:
        writer.execute("BEGIN IMMEDIATE")
        writer.execute("UPDATE clothes SET title = title WHERE id = '101'")
        with ThreadPoolExecutor(max_workers=1) as executor:
            assert executor.submit(db.get_weekday_outfits).result(timeout=3) == {}
    finally:
        writer.rollback()
        writer.close()
