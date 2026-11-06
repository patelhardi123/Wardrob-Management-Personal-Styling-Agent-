import sqlite3

import pytest

import database as db


@pytest.fixture
def auth_database(tmp_path, monkeypatch):
    database_path = tmp_path / "auth.db"
    monkeypatch.setattr(db, "DB_PATH", str(database_path))
    with sqlite3.connect(database_path) as connection:
        connection.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL COLLATE NOCASE UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    return database_path


def test_create_and_authenticate_user(auth_database):
    user = db.create_user("  Wardrobe Tester  ", "TEST@example.com", "correct horse battery staple")

    assert user["name"] == "Wardrobe Tester"
    assert user["email"] == "test@example.com"
    authenticated = db.authenticate_user("test@EXAMPLE.com", "correct horse battery staple")
    assert authenticated == user
    assert db.authenticate_user("test@example.com", "incorrect password") is None

    with sqlite3.connect(auth_database) as connection:
        stored_hash = connection.execute("SELECT password_hash FROM users").fetchone()[0]
    assert "correct horse battery staple" not in stored_hash


def test_email_is_unique_without_case_sensitivity(auth_database):
    db.create_user("First User", "user@example.com", "first secure password")

    with pytest.raises(sqlite3.IntegrityError):
        db.create_user("Second User", "USER@example.com", "second secure password")
