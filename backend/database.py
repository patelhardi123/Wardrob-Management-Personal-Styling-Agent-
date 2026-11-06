import sqlite3
import os
import json
import uuid
import hashlib
import hmac
import secrets
from datetime import date, datetime, timedelta
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "wardrobe.db")
PASSWORD_HASH_ITERATIONS = 310_000

INITIAL_CLOTHES_SEED = [
    {
        "id": "101",
        "category": "tops",
        "title": "Oversized White Linen Shirt",
        "color": "White",
        "pattern": "Solid",
        "style": "smart-casual",
        "season": "summer",
        "usageCount": 4,
        "lastUsed": "2026-08-25",
        "imageUrl": "https://images.unsplash.com/photo-1598033129183-c4f50c736f10?auto=format&fit=crop&w=400&q=80"
    },
    {
        "id": "102",
        "category": "tops",
        "title": "Classic Black Fitted Tee",
        "color": "Black",
        "pattern": "Solid",
        "style": "casual",
        "season": "all-season",
        "usageCount": 12,
        "lastUsed": "2026-08-29",
        "imageUrl": "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=400&q=80"
    },
    {
        "id": "103",
        "category": "bottoms",
        "title": "High-Waisted Straight Blue Jeans",
        "color": "Blue",
        "pattern": "Denim",
        "style": "casual",
        "season": "all-season",
        "usageCount": 18,
        "lastUsed": "2026-08-28",
        "imageUrl": "https://images.unsplash.com/photo-1541099649105-f69ad21f3246?auto=format&fit=crop&w=400&q=80"
    },
    {
        "id": "104",
        "category": "bottoms",
        "title": "Tailored Beige Pleated Trousers",
        "color": "Beige",
        "pattern": "Solid",
        "style": "formal",
        "season": "all-season",
        "usageCount": 3,
        "lastUsed": "2026-08-15",
        "imageUrl": "https://images.unsplash.com/photo-1594633312681-425c7b97ccd1?auto=format&fit=crop&w=400&q=80"
    },
    {
        "id": "105",
        "category": "outerwear",
        "title": "Vintage Dark Leather Jacket",
        "color": "Black",
        "pattern": "Solid",
        "style": "streetwear",
        "season": "winter",
        "usageCount": 6,
        "lastUsed": "2026-08-20",
        "imageUrl": "https://images.unsplash.com/photo-1551028719-00167b16eac5?auto=format&fit=crop&w=400&q=80"
    },
    {
        "id": "106",
        "category": "footwear",
        "title": "Retro White Chunky Sneakers",
        "color": "White",
        "pattern": "Solid",
        "style": "sporty",
        "season": "all-season",
        "usageCount": 15,
        "lastUsed": "2026-08-29",
        "imageUrl": "https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?auto=format&fit=crop&w=400&q=80"
    },
    {
        "id": "107",
        "category": "footwear",
        "title": "Black Leather Loafers",
        "color": "Black",
        "pattern": "Solid",
        "style": "formal",
        "season": "all-season",
        "usageCount": 2,
        "lastUsed": "2026-08-10",
        "imageUrl": "https://images.unsplash.com/photo-1614252235316-8c857d38b5f4?auto=format&fit=crop&w=400&q=80"
    },
    {
        "id": "108",
        "category": "bags",
        "title": "Minimalist Black Crossbody Bag",
        "color": "Black",
        "pattern": "Solid",
        "style": "casual",
        "season": "all-season",
        "usageCount": 9,
        "lastUsed": "2026-08-27",
        "imageUrl": "https://images.unsplash.com/photo-1548036328-c9fa89d128fa?auto=format&fit=crop&w=400&q=80"
    },
    {
        "id": "109",
        "category": "accessories",
        "title": "Gold Minimalist Chain & Analog Watch",
        "color": "Gold",
        "pattern": "Metallic",
        "style": "smart-casual",
        "season": "all-season",
        "usageCount": 22,
        "lastUsed": "2026-08-29",
        "imageUrl": "https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?auto=format&fit=crop&w=400&q=80"
    }
]

def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn

from fashion.attribute_extractor import normalize_garment_attributes


def _requires_preparation(category: str, title: str = "") -> bool:
    description = f"{category or ''} {title or ''}".lower()
    if any(term in description for term in (
        "footwear", "shoe", "sneaker", "loafer", "boot", "sandal", "heel",
        "bag", "purse", "handbag", "tote", "backpack", "accessor",
        "jewell", "jewel", "watch", "chain", "belt"
    )):
        return False
    return any(term in description for term in (
        "top", "shirt", "tee", "t-shirt", "blouse", "sweater", "hoodie",
        "cardigan", "dress", "one_piece", "one-piece", "kurti", "kurta",
        "saree", "lehenga", "gown", "jumpsuit", "bottom", "trouser", "pant",
        "jean", "skirt", "short", "legging", "chino", "outerwear", "jacket",
        "coat", "blazer"
    ))


def ensure_stylist_tables():
    conn = get_connection()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS stylist_conversations (
                conversation_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                state_json TEXT NOT NULL,
                messages_json TEXT NOT NULL DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (conversation_id, user_id)
            );
            CREATE TABLE IF NOT EXISTS saved_stylist_outfits (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                conversation_id TEXT NOT NULL,
                title TEXT NOT NULL,
                outfit_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (id, user_id)
            );
            CREATE TABLE IF NOT EXISTS weekday_outfits (
                schedule_id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                day_id TEXT NOT NULL,
                plan_date TEXT,
                confirmation_status TEXT NOT NULL DEFAULT 'awaiting',
                occasion TEXT NOT NULL DEFAULT 'Outfit',
                outfit_json TEXT NOT NULL,
                source TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_stylist_conversations_user_updated
            ON stylist_conversations (user_id, updated_at);
            CREATE INDEX IF NOT EXISTS idx_saved_stylist_outfits_user_created
            ON saved_stylist_outfits (user_id, created_at);
        """)
        schedule_columns = {
            row["name"] for row in conn.execute("PRAGMA table_info(weekday_outfits)").fetchall()
        }
        if "schedule_id" not in schedule_columns:
            conn.execute("ALTER TABLE weekday_outfits RENAME TO weekday_outfits_legacy")
            conn.executescript("""
                CREATE TABLE weekday_outfits (
                    schedule_id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    day_id TEXT NOT NULL,
                    occasion TEXT NOT NULL DEFAULT 'Outfit',
                    outfit_json TEXT NOT NULL,
                    source TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            legacy_rows = conn.execute(
                "SELECT user_id, day_id, outfit_json, source, updated_at FROM weekday_outfits_legacy"
            ).fetchall()
            conn.executemany(
                """
                INSERT INTO weekday_outfits
                    (schedule_id, user_id, day_id, occasion, outfit_json, source, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        str(uuid.uuid4()), row["user_id"], row["day_id"],
                        "Daily look", row["outfit_json"], row["source"], row["updated_at"]
                    )
                    for row in legacy_rows
                ]
            )
            conn.execute("DROP TABLE weekday_outfits_legacy")
            schedule_columns = {
                row["name"] for row in conn.execute("PRAGMA table_info(weekday_outfits)").fetchall()
            }
        if "plan_date" not in schedule_columns:
            conn.execute("ALTER TABLE weekday_outfits ADD COLUMN plan_date TEXT")
        if "confirmation_status" not in schedule_columns:
            conn.execute(
                "ALTER TABLE weekday_outfits ADD COLUMN confirmation_status TEXT NOT NULL DEFAULT 'awaiting'"
            )
        week_start = date.today() - timedelta(days=date.today().weekday())
        day_offsets = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
        for day_id, offset in day_offsets.items():
            conn.execute(
                "UPDATE weekday_outfits SET plan_date = ? WHERE day_id = ? AND plan_date IS NULL",
                ((week_start + timedelta(days=offset)).isoformat(), day_id)
            )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_weekday_outfits_user_day ON weekday_outfits (user_id, day_id, plan_date)"
        )
        conn.commit()
    finally:
        conn.close()


def init_db():
    conn = get_connection()
    try:
        # Readers (chat/history/plans) can proceed during short background writes.
        conn.execute("PRAGMA journal_mode=WAL")
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL COLLATE NOCASE UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clothes (
                id TEXT PRIMARY KEY,
                title TEXT,
                category TEXT,
                color TEXT,
                pattern TEXT,
                style TEXT,
                season TEXT,
                usageCount INTEGER DEFAULT 0,
                lastUsed TEXT DEFAULT 'Never',
                imageUrl TEXT,
                attributes_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Check if attributes_json column exists in older database tables
        cursor.execute("PRAGMA table_info(clothes)")
        columns = [row[1] for row in cursor.fetchall()]
        if "attributes_json" not in columns:
            cursor.execute("ALTER TABLE clothes ADD COLUMN attributes_json TEXT")

        # Add availability and ironing status columns for Voice Stylist Agent
        if "availability_status" not in columns:
            cursor.execute("ALTER TABLE clothes ADD COLUMN availability_status TEXT")
            cursor.execute("UPDATE clothes SET availability_status = 'available'")
        if "ironing_status" not in columns:
            cursor.execute("ALTER TABLE clothes ADD COLUMN ironing_status TEXT")
            cursor.execute("UPDATE clothes SET ironing_status = 'ready'")
        if "expected_available_at" not in columns:
            cursor.execute("ALTER TABLE clothes ADD COLUMN expected_available_at TEXT")
        if "last_status_updated" not in columns:
            cursor.execute("ALTER TABLE clothes ADD COLUMN last_status_updated TEXT")
            cursor.execute("UPDATE clothes SET last_status_updated = datetime('now')")
        if "user_id" not in columns:
            cursor.execute("ALTER TABLE clothes ADD COLUMN user_id INTEGER NOT NULL DEFAULT 1")
        if "status_note" not in columns:
            cursor.execute("ALTER TABLE clothes ADD COLUMN status_note TEXT")
        if "notify_when_ready" not in columns:
            cursor.execute("ALTER TABLE clothes ADD COLUMN notify_when_ready INTEGER NOT NULL DEFAULT 0")
        if "wear_cooldown_until" not in columns:
            cursor.execute("ALTER TABLE clothes ADD COLUMN wear_cooldown_until TEXT")
        cursor.execute(
            "UPDATE clothes SET availability_status = 'ready' "
            "WHERE availability_status IS NULL OR TRIM(availability_status) = '' "
            "OR availability_status = 'available'"
        )
        cursor.execute(
            "UPDATE clothes SET ironing_status = 'ready' "
            "WHERE ironing_status IS NULL OR TRIM(ironing_status) = ''"
        )
        cursor.execute("UPDATE clothes SET wear_cooldown_until = NULL WHERE wear_cooldown_until IS NOT NULL")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_clothes_user_id ON clothes (user_id)")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_profile (
                id INTEGER PRIMARY KEY DEFAULT 1,
                profile_json TEXT
            )
        """)
        conn.commit()
        ensure_stylist_tables()
        ensure_availability_tables()

        # Check if empty, then seed
        cursor.execute("SELECT COUNT(*) FROM clothes")
        count = cursor.fetchone()[0]
        if count == 0:
            print("Seeding SQLite database with default wardrobe items...")
            for item in INITIAL_CLOTHES_SEED:
                norm_attr = normalize_garment_attributes({
                    "category": item.get("category"),
                    "title": item.get("title"),
                    "color": item.get("color"),
                    "pattern": item.get("pattern"),
                    "style": item.get("style")
                })
                attr_json_str = json.dumps(norm_attr)

                cursor.execute("""
                    INSERT INTO clothes (id, title, category, color, pattern, style, season, usageCount, lastUsed, imageUrl, attributes_json, availability_status, ironing_status, user_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ready', 'ready', 1)
                """, (
                    str(item["id"]),
                    item["title"],
                    item["category"],
                    item["color"],
                    item["pattern"],
                    item["style"],
                    item["season"],
                    item["usageCount"],
                    item["lastUsed"],
                    item["imageUrl"],
                    attr_json_str
                ))
            conn.commit()
    finally:
        conn.close()


def create_user(name: str, email: str, password: str):
    salt = secrets.token_bytes(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_HASH_ITERATIONS
    )
    stored_hash = f"{PASSWORD_HASH_ITERATIONS}${salt.hex()}${password_hash.hex()}"
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name.strip(), email.strip().lower(), stored_hash)
        )
        conn.commit()
        return {
            "id": cursor.lastrowid,
            "name": name.strip(),
            "email": email.strip().lower()
        }
    finally:
        conn.close()


def authenticate_user(email: str, password: str):
    conn = get_connection()
    try:
        user = conn.execute(
            "SELECT id, name, email, password_hash FROM users WHERE email = ?",
            (email.strip().lower(),)
        ).fetchone()
    finally:
        conn.close()

    if not user:
        return None

    try:
        iterations, salt_hex, hash_hex = user["password_hash"].split("$")
        calculated_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterations)
        )
        if not hmac.compare_digest(calculated_hash.hex(), hash_hex):
            return None
    except (ValueError, TypeError):
        return None

    return {"id": user["id"], "name": user["name"], "email": user["email"]}


def get_user_profile():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT profile_json FROM user_profile WHERE id = 1")
        row = cursor.fetchone()
        if row and row["profile_json"]:
            try:
                profile = json.loads(row["profile_json"])
                if profile.get("name") == "Alex Morgan":
                    profile["name"] = "My Profile"
                if profile.get("defaultRoutine") in ["college", "College Student"]:
                    profile["defaultRoutine"] = "Daily Look"
                return profile
            except Exception:
                pass
        return None
    finally:
        conn.close()

def save_user_profile(profile_dict: dict):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        profile_json = json.dumps(profile_dict)
        cursor.execute("""
            INSERT INTO user_profile (id, profile_json) VALUES (1, ?)
            ON CONFLICT(id) DO UPDATE SET profile_json = excluded.profile_json
        """, (profile_json,))
        conn.commit()
        return profile_dict
    finally:
        conn.close()

def ensure_availability_tables():
    conn = get_connection()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS outfit_wear_events (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                outfit_id TEXT NOT NULL,
                outfit_title TEXT NOT NULL,
                planned_day TEXT,
                wear_date TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (user_id, outfit_id, wear_date)
            );
            CREATE TABLE IF NOT EXISTS outfit_wear_garments (
                event_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                item_id TEXT NOT NULL,
                actually_worn INTEGER,
                laundry_response INTEGER,
                PRIMARY KEY (event_id, item_id),
                FOREIGN KEY (event_id) REFERENCES outfit_wear_events(id)
            );
            CREATE INDEX IF NOT EXISTS idx_wear_events_user_status
            ON outfit_wear_events (user_id, status, wear_date);
        """)
        conn.commit()
    finally:
        conn.close()


def get_all_clothes(user_id: int = 1):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM clothes WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        )
        rows = cursor.fetchall()

        result = []
        for r in rows:
            attr_data = {}
            if r["attributes_json"]:
                try:
                    attr_data = json.loads(r["attributes_json"])
                except Exception:
                    pass

            if not attr_data:
                attr_data = normalize_garment_attributes({
                    "category": r["category"],
                    "title": r["title"],
                    "color": r["color"],
                    "pattern": r["pattern"],
                    "style": r["style"]
                })

            # Convert row to dict for safe access
            row_dict = dict(r)

            result.append({
                "id": r["id"],
                "title": r["title"],
                "category": r["category"],
                "color": r["color"],
                "pattern": r["pattern"],
                "style": r["style"],
                "season": r["season"],
                "usageCount": r["usageCount"],
                "lastUsed": r["lastUsed"],
                "imageUrl": r["imageUrl"],
                "attributes": attr_data,
                "availability_status": row_dict.get("availability_status") or "ready",
                "ironing_status": row_dict.get("ironing_status") or "ready",
                "expected_available_at": row_dict.get("expected_available_at"),
                "last_status_updated": row_dict.get("last_status_updated"),
                "status_note": row_dict.get("status_note"),
                "notify_when_ready": bool(row_dict.get("notify_when_ready", 0)),
                "wear_cooldown_until": row_dict.get("wear_cooldown_until"),
                "user_id": row_dict.get("user_id", 1)
            })
        return result
    finally:
        conn.close()

def add_clothing_item(item: dict, user_id: int = 1):
    conn = get_connection()
    try:
        cursor = conn.cursor()

        item_id = str(item.get("id") or int(os.urandom(4).hex(), 16))
        title = item.get("title", "Untitled Garment")
        category = item.get("category", "tops")
        color = item.get("color", "Black")
        pattern = item.get("pattern", "Solid")
        style = item.get("style", "casual")
        season = item.get("season", "all-season")
        usage_count = item.get("usageCount", 0)
        last_used = item.get("lastUsed", "Never")
        image_url = item.get("imageUrl", "")
        availability_status = item.get("availability_status", "ready")
        ironing_status = item.get("ironing_status", "ready")
        expected_available_at = item.get("expected_available_at")

        raw_attr = item.get("attributes") or item.get("analysis") or {
            "category": category, "title": title, "color": color, "pattern": pattern, "style": style
        }
        norm_attr = normalize_garment_attributes(raw_attr)
        attr_json_str = json.dumps(norm_attr)

        cursor.execute("""
            INSERT INTO clothes (id, title, category, color, pattern, style, season, usageCount, lastUsed, imageUrl, attributes_json, availability_status, ironing_status, expected_available_at, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (item_id, title, category, color, pattern, style, season, usage_count, last_used, image_url, attr_json_str, availability_status, ironing_status, expected_available_at, user_id))

        conn.commit()

        return {
            "id": item_id,
            "title": title,
            "category": category,
            "color": color,
            "pattern": pattern,
            "style": style,
            "season": season,
            "usageCount": usage_count,
            "lastUsed": last_used,
            "imageUrl": image_url,
            "attributes": norm_attr,
            "availability_status": availability_status,
            "ironing_status": ironing_status,
            "expected_available_at": expected_available_at,
            "last_status_updated": None,
            "status_note": item.get("status_note"),
            "notify_when_ready": bool(item.get("notify_when_ready", False)),
            "wear_cooldown_until": item.get("wear_cooldown_until"),
            "user_id": user_id
        }
    finally:
        conn.close()

def update_clothing_item(item_id: str, item: dict, user_id: int = 1):
    conn = get_connection()
    try:
        cursor = conn.cursor()

        title = item.get("title")
        category = item.get("category")
        color = item.get("color")
        pattern = item.get("pattern")
        style = item.get("style")
        season = item.get("season")
        usage_count = item.get("usageCount")
        last_used = item.get("lastUsed")
        image_url = item.get("imageUrl")
        availability_status = item.get("availability_status")
        ironing_status = item.get("ironing_status")
        expected_available_at = item.get("expected_available_at")
        status_note = item.get("status_note")
        notify_when_ready = item.get("notify_when_ready")
        wear_cooldown_until = item.get("wear_cooldown_until")

        attr_json_str = None
        if "attributes" in item and item["attributes"]:
            norm_attr = normalize_garment_attributes(item["attributes"])
            attr_json_str = json.dumps(norm_attr)

        # Build dynamic update query
        update_fields = []
        update_values = []

        if title is not None:
            update_fields.append("title = ?")
            update_values.append(title)
        if category is not None:
            update_fields.append("category = ?")
            update_values.append(category)
        if color is not None:
            update_fields.append("color = ?")
            update_values.append(color)
        if pattern is not None:
            update_fields.append("pattern = ?")
            update_values.append(pattern)
        if style is not None:
            update_fields.append("style = ?")
            update_values.append(style)
        if season is not None:
            update_fields.append("season = ?")
            update_values.append(season)
        if usage_count is not None:
            update_fields.append("usageCount = ?")
            update_values.append(usage_count)
        if last_used is not None:
            update_fields.append("lastUsed = ?")
            update_values.append(last_used)
        if image_url is not None:
            update_fields.append("imageUrl = ?")
            update_values.append(image_url)
        if attr_json_str is not None:
            update_fields.append("attributes_json = ?")
            update_values.append(attr_json_str)
        if availability_status is not None:
            update_fields.append("availability_status = ?")
            update_values.append(availability_status)
            update_fields.append("last_status_updated = CURRENT_TIMESTAMP")
        if ironing_status is not None:
            update_fields.append("ironing_status = ?")
            update_values.append(ironing_status)
            update_fields.append("last_status_updated = CURRENT_TIMESTAMP")
        if "expected_available_at" in item:
            update_fields.append("expected_available_at = ?")
            update_values.append(expected_available_at)
        if "status_note" in item:
            update_fields.append("status_note = ?")
            update_values.append(status_note)
        if notify_when_ready is not None:
            update_fields.append("notify_when_ready = ?")
            update_values.append(int(bool(notify_when_ready)))
        if wear_cooldown_until is not None:
            update_fields.append("wear_cooldown_until = ?")
            update_values.append(wear_cooldown_until)

        if update_fields:
            update_values.append(str(item_id))
            update_values.append(user_id)
            cursor.execute(f"""
                UPDATE clothes
                SET {', '.join(update_fields)}
                WHERE id = ? AND user_id = ?
            """, update_values)

        conn.commit()
        return get_clothing_item(item_id, user_id)
    finally:
        conn.close()

def get_clothing_item(item_id: str, user_id: int = 1):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM clothes WHERE id = ? AND user_id = ?",
            (str(item_id), user_id)
        )
        r = cursor.fetchone()
        if r:
            attr_data = {}
            if r["attributes_json"]:
                try:
                    attr_data = json.loads(r["attributes_json"])
                except Exception:
                    pass

            if not attr_data:
                attr_data = normalize_garment_attributes({
                    "category": r["category"],
                    "title": r["title"],
                    "color": r["color"],
                    "pattern": r["pattern"],
                    "style": r["style"]
                })

            # Convert row to dict for safe access
            row_dict = dict(r)

            return {
                "id": r["id"],
                "title": r["title"],
                "category": r["category"],
                "color": r["color"],
                "pattern": r["pattern"],
                "style": r["style"],
                "season": r["season"],
                "usageCount": r["usageCount"],
                "lastUsed": r["lastUsed"],
                "imageUrl": r["imageUrl"],
                "attributes": attr_data,
                "availability_status": row_dict.get("availability_status") or "ready",
                "ironing_status": row_dict.get("ironing_status") or "ready",
                "expected_available_at": row_dict.get("expected_available_at"),
                "last_status_updated": row_dict.get("last_status_updated"),
                "status_note": row_dict.get("status_note"),
                "notify_when_ready": bool(row_dict.get("notify_when_ready", 0)),
                "wear_cooldown_until": row_dict.get("wear_cooldown_until"),
                "user_id": row_dict.get("user_id", 1)
            }
        return None
    finally:
        conn.close()

def delete_clothing_item(item_id: str, user_id: int = 1):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM clothes WHERE id = ? AND user_id = ?",
            (str(item_id), user_id)
        )
        conn.commit()
        deleted = cursor.rowcount > 0
        return deleted
    finally:
        conn.close()


def update_clothing_availability(
    item_id: str,
    user_id: int,
    availability_status: str,
    ironing_status: Optional[str] = None,
    expected_available_at: Optional[str] = None,
    status_note: Optional[str] = None,
    notify_when_ready: Optional[bool] = None
):
    conn = get_connection()
    try:
        fields = ["availability_status = ?", "last_status_updated = CURRENT_TIMESTAMP"]
        values = [availability_status]
        if ironing_status is not None:
            fields.append("ironing_status = ?")
            values.append(ironing_status)
        fields.extend(["expected_available_at = ?", "status_note = ?"])
        values.extend([expected_available_at, status_note])
        if notify_when_ready is not None:
            fields.append("notify_when_ready = ?")
            values.append(int(notify_when_ready))
        values.extend([str(item_id), user_id])
        conn.execute(
            f"UPDATE clothes SET {', '.join(fields)} WHERE id = ? AND user_id = ?",
            values
        )
        if conn.total_changes == 0:
            return None
        conn.commit()
    finally:
        conn.close()
    return get_clothing_item(item_id, user_id)


def create_outfit_wear_event(
    user_id: int,
    outfit: dict,
    item_ids: list,
    wear_date: str,
    planned_day: Optional[str] = None,
    worn: bool = True
):
    ensure_availability_tables()
    event_id = str(uuid.uuid4())
    outfit_id = str(outfit.get("id") or "")
    if not outfit_id:
        raise ValueError("Outfit ID is required to record a wear event.")
    valid_items = []
    conn = get_connection()
    try:
        conn.row_factory = sqlite3.Row
        item_records = {}
        for item_id in dict.fromkeys(str(value) for value in item_ids):
            item = conn.execute(
                "SELECT id, category, title FROM clothes WHERE id = ? AND user_id = ?",
                (item_id, user_id)
            ).fetchone()
            if not item:
                raise ValueError("The outfit contains an item that is not in this user's wardrobe.")
            valid_items.append(item_id)
            item_records[item_id] = dict(item)
        confirmation_items = [
            item_id for item_id in valid_items
            if _requires_preparation(item_records[item_id]["category"], item_records[item_id]["title"])
        ]
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO outfit_wear_events
                (id, user_id, outfit_id, outfit_title, planned_day, wear_date, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id, user_id, outfit_id, outfit.get("title", "Planned outfit"),
                planned_day, wear_date,
                "pending" if worn and confirmation_items else "submitted" if worn else "not_worn"
            )
        )
        if cursor.rowcount == 0:
            row = conn.execute(
                """
                SELECT id, status FROM outfit_wear_events
                WHERE user_id = ? AND outfit_id = ? AND wear_date = ?
                """,
                (user_id, outfit_id, wear_date)
            ).fetchone()
            if worn and row["status"] == "not_worn":
                conn.execute(
                    "UPDATE outfit_wear_events SET status = 'pending' WHERE id = ? AND user_id = ?",
                    (row["id"], user_id)
                )
                conn.executemany(
                    """
                    INSERT OR IGNORE INTO outfit_wear_garments (event_id, user_id, item_id)
                    VALUES (?, ?, ?)
                    """,
                    [(row["id"], user_id, item_id) for item_id in confirmation_items]
                )
                conn.executemany(
                    """
                    UPDATE clothes
                    SET usageCount = COALESCE(usageCount, 0) + 1, lastUsed = ?
                    WHERE id = ? AND user_id = ?
                    """,
                    [(wear_date, item_id, user_id) for item_id in valid_items]
                )
                conn.commit()
                return {
                    "id": row["id"],
                    "status": "pending" if confirmation_items else "submitted",
                    "duplicate": False
                }
            return {"id": row["id"], "status": row["status"], "duplicate": True}
        if worn:
            conn.executemany(
                """
                UPDATE clothes
                SET usageCount = COALESCE(usageCount, 0) + 1, lastUsed = ?
                WHERE id = ? AND user_id = ?
                """,
                [(wear_date, item_id, user_id) for item_id in valid_items]
            )
        if worn and confirmation_items:
            conn.executemany(
                """
                INSERT INTO outfit_wear_garments (event_id, user_id, item_id)
                VALUES (?, ?, ?)
                """,
                [(event_id, user_id, item_id) for item_id in confirmation_items]
            )
        conn.commit()
    finally:
        conn.close()
    return {
        "id": event_id,
        "status": "pending" if worn and confirmation_items else "submitted" if worn else "not_worn",
        "duplicate": False
    }


def get_pending_wear_events(user_id: int = 1):
    ensure_availability_tables()
    conn = get_connection()
    try:
        conn.row_factory = sqlite3.Row
        events = conn.execute(
            """
            SELECT * FROM outfit_wear_events
            WHERE user_id = ? AND status = 'pending'
            ORDER BY wear_date DESC, created_at DESC
            """,
            (user_id,)
        ).fetchall()
        results = []
        for event in events:
            garments = conn.execute(
                """
                SELECT c.id, c.title, c.category, c.color, c.imageUrl,
                       g.actually_worn, g.laundry_response
                FROM outfit_wear_garments g
                JOIN clothes c ON c.id = g.item_id AND c.user_id = g.user_id
                WHERE g.event_id = ? AND g.user_id = ?
                ORDER BY c.category, c.title
                """,
                (event["id"], user_id)
            ).fetchall()
            results.append({
                "id": event["id"],
                "outfit_id": event["outfit_id"],
                "outfit_title": event["outfit_title"],
                "planned_day": event["planned_day"],
                "wear_date": event["wear_date"],
                "garments": [dict(garment) for garment in garments]
            })
        return results
    finally:
        conn.close()


def submit_wear_event_answers(user_id: int, event_id: str, answers: list):
    ensure_availability_tables()
    conn = get_connection()
    try:
        conn.row_factory = sqlite3.Row
        event = conn.execute(
            "SELECT id FROM outfit_wear_events WHERE id = ? AND user_id = ? AND status = 'pending'",
            (event_id, user_id)
        ).fetchone()
        if not event:
            return None
        for answer in answers:
            item_id = str(answer["item_id"])
            actually_worn = answer.get("actually_worn")
            laundry_response = answer.get("in_laundry")
            row = conn.execute(
                """
                SELECT item_id FROM outfit_wear_garments
                WHERE event_id = ? AND user_id = ? AND item_id = ?
                """,
                (event_id, user_id, item_id)
            ).fetchone()
            if not row:
                raise ValueError("The response includes a garment outside this wear event.")
            if actually_worn is None:
                continue

            # Get item category to check if it's clothing (not accessories/footwear)
            item_row = conn.execute(
                "SELECT category FROM clothes WHERE id = ? AND user_id = ?",
                (item_id, user_id)
            ).fetchone()
            category = item_row["category"].lower() if item_row else ""

            # Non-clothing categories that don't need washing
            non_clothing_categories = ['footwear', 'bags', 'accessories', 'jewelry', 'jewellery']
            is_clothing = not any(nc in category for nc in non_clothing_categories)

            conn.execute(
                """
                UPDATE outfit_wear_garments
                SET actually_worn = ?, laundry_response = ?
                WHERE event_id = ? AND user_id = ? AND item_id = ?
                """,
                (
                    int(bool(actually_worn)),
                    int(bool(laundry_response)) if actually_worn and laundry_response is not None else None,
                    event_id, user_id, item_id
                )
            )

            # Update item status based on answers
            if actually_worn:
                if is_clothing:
                    if laundry_response is True:
                        conn.execute(
                            """
                            UPDATE clothes
                            SET availability_status = 'to_wash',
                                expected_available_at = datetime('now', '+2 days'),
                                last_status_updated = CURRENT_TIMESTAMP
                            WHERE id = ? AND user_id = ?
                            """,
                            (item_id, user_id)
                        )
                    elif laundry_response is False:
                        conn.execute(
                            """
                            UPDATE clothes
                            SET availability_status = 'ready',
                                expected_available_at = NULL,
                                last_status_updated = CURRENT_TIMESTAMP
                            WHERE id = ? AND user_id = ?
                              AND availability_status IN ('ready', 'available', 'in_wash', 'to_wash')
                            """,
                            (item_id, user_id)
                        )
                # For non-clothing items: don't change availability (they're always available unless missing)

        conn.execute(
            "UPDATE outfit_wear_events SET status = 'submitted' WHERE id = ? AND user_id = ?",
            (event_id, user_id)
        )
        conn.commit()
    finally:
        conn.close()
    return True


def dismiss_wear_event(user_id: int, event_id: str):
    ensure_availability_tables()
    conn = get_connection()
    try:
        cursor = conn.execute(
            "UPDATE outfit_wear_events SET status = 'dismissed' WHERE id = ? AND user_id = ? AND status = 'pending'",
            (event_id, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def get_items_needing_ready_confirmation(user_id: int = 1):
    """Get clothing items that have been in wash/drying for 2+ days and need user confirmation."""
    conn = get_connection()
    try:
        conn.row_factory = sqlite3.Row
        # Non-clothing categories that don't need washing
        non_clothing_categories = ['footwear', 'bags', 'accessories', 'jewelry', 'jewellery']

        query = """
            SELECT id, title, category, color, imageUrl, availability_status,
                   last_status_updated, expected_available_at
            FROM clothes
            WHERE user_id = ?
              AND availability_status IN ('in_wash', 'drying', 'to_wash')
              AND (
                  last_status_updated < datetime('now', '-2 days')
                  OR expected_available_at < datetime('now')
              )
        """
        rows = conn.execute(query, (user_id,)).fetchall()

        results = []
        for row in rows:
            category = row["category"].lower()
            # Filter out non-clothing items
            is_clothing = not any(nc in category for nc in non_clothing_categories)

            if is_clothing:
                results.append({
                    "id": row["id"],
                    "title": row["title"],
                    "category": row["category"],
                    "color": row["color"],
                    "imageUrl": row["imageUrl"],
                    "availability_status": row["availability_status"],
                    "last_status_updated": row["last_status_updated"],
                    "expected_available_at": row["expected_available_at"]
                })

        return results
    finally:
        conn.close()


def get_stylist_conversation(conversation_id: str, user_id: int = 1):
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT state_json, messages_json, created_at, updated_at
            FROM stylist_conversations
            WHERE conversation_id = ? AND user_id = ?
            """,
            (conversation_id, user_id)
        ).fetchone()
        if not row:
            return None
        return {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "state": json.loads(row["state_json"]),
            "messages": json.loads(row["messages_json"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        }
    finally:
        conn.close()


def save_stylist_conversation(
    conversation_id: str,
    user_id: int,
    state: dict,
    messages: list
):
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO stylist_conversations
                (conversation_id, user_id, state_json, messages_json, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(conversation_id, user_id) DO UPDATE SET
                state_json = excluded.state_json,
                messages_json = excluded.messages_json,
                updated_at = CURRENT_TIMESTAMP
            """,
            (conversation_id, user_id, json.dumps(state), json.dumps(messages))
        )
        conn.commit()
    finally:
        conn.close()


def save_stylist_outfit(
    outfit_id: str,
    user_id: int,
    conversation_id: str,
    outfit: dict
):
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO saved_stylist_outfits
                (id, user_id, conversation_id, title, outfit_json)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO NOTHING
            """,
            (outfit_id, user_id, conversation_id, outfit.get("title", "Saved outfit"), json.dumps(outfit))
        )
        row = conn.execute(
            "SELECT id, title, outfit_json, created_at FROM saved_stylist_outfits WHERE id = ? AND user_id = ?",
            (outfit_id, user_id)
        ).fetchone()
        if not row:
            raise ValueError("The selected outfit could not be saved for this user.")
        conn.commit()
        return {
            "id": row["id"],
            "title": row["title"],
            "outfit": json.loads(row["outfit_json"]),
            "created_at": row["created_at"]
        }
    finally:
        conn.close()


def get_saved_stylist_outfits(user_id: int = 1):
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT id, title, outfit_json, created_at
            FROM saved_stylist_outfits
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,)
        ).fetchall()
        return [
            {
                "id": row["id"],
                "title": row["title"],
                "outfit": json.loads(row["outfit_json"]),
                "created_at": row["created_at"]
            }
            for row in rows
        ]
    finally:
        conn.close()


def get_weekday_outfits(user_id: int = 1):
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT schedule_id, day_id, plan_date, confirmation_status, occasion, outfit_json, source, updated_at
            FROM weekday_outfits
            WHERE user_id = ?
            ORDER BY day_id, updated_at, schedule_id
            """,
            (user_id,)
        ).fetchall()
        schedule = {}
        for row in rows:
            schedule.setdefault(row["day_id"], []).append({
                "schedule_id": row["schedule_id"],
                "day_id": row["day_id"],
                "plan_date": row["plan_date"],
                "confirmation_status": row["confirmation_status"],
                "occasion": row["occasion"],
                "outfit": json.loads(row["outfit_json"]),
                "source": row["source"],
                "updated_at": row["updated_at"]
            })
        return schedule
    finally:
        conn.close()


def get_weekday_outfit(schedule_id: str, user_id: int = 1):
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT schedule_id, day_id, plan_date, confirmation_status, occasion,
                   outfit_json, source, updated_at
            FROM weekday_outfits WHERE user_id = ? AND schedule_id = ?
            """,
            (user_id, schedule_id)
        ).fetchone()
        if not row:
            return None
        return {
            "schedule_id": row["schedule_id"],
            "day_id": row["day_id"],
            "plan_date": row["plan_date"],
            "confirmation_status": row["confirmation_status"],
            "occasion": row["occasion"],
            "outfit": json.loads(row["outfit_json"]),
            "source": row["source"],
            "updated_at": row["updated_at"]
        }
    finally:
        conn.close()


def _validate_scheduled_outfit(conn, user_id, outfit, source, ready_confirmed_item_ids=None):
    slots = outfit.get("slotItems") or {}
    outfit_item_ids = list(dict.fromkeys(
        str(item["id"])
        for item in slots.values()
        if isinstance(item, dict) and item.get("id") is not None
    ))
    confirmed_ids = {str(item_id) for item_id in (ready_confirmed_item_ids or [])}
    preparation_item_ids = []

    for item_id in outfit_item_ids:
        item = conn.execute(
            """
            SELECT category, title, availability_status, ironing_status
            FROM clothes WHERE id = ? AND user_id = ?
            """,
            (item_id, user_id)
        ).fetchone()
        if not item:
            raise ValueError("This outfit includes a garment outside your wardrobe.")
        if item["availability_status"] not in {"ready", "available"}:
            raise ValueError(f"{item['title']} is not currently available to wear.")

        requires_preparation = _requires_preparation(item["category"], item["title"])
        if not requires_preparation:
            continue
        preparation_item_ids.append(item_id)
        if item["ironing_status"] != "ready":
            raise ValueError(f"{item['title']} needs ironing before it can be scheduled.")
        if source == "occasion" and item_id not in confirmed_ids:
            raise ValueError("Confirm that every clothing garment is clean, available, and ironed before scheduling.")
    return outfit_item_ids, preparation_item_ids


def schedule_weekday_outfit(
    day_id: str,
    user_id: int,
    outfit: dict,
    source: str,
    occasion: str = "Outfit",
    ready_confirmed_item_ids: Optional[list] = None,
    plan_date: Optional[str] = None
):
    if day_id not in {"mon", "tue", "wed", "thu", "fri", "sat", "sun"}:
        raise ValueError("Choose a day from Monday to Sunday.")
    week_start = date.today() - timedelta(days=date.today().weekday())
    day_offsets = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
    planned_date = date.fromisoformat(plan_date) if plan_date else week_start + timedelta(days=day_offsets[day_id])
    if planned_date.weekday() != day_offsets[day_id]:
        raise ValueError("The planned date must match the selected weekday.")
    conn = get_connection()
    try:
        outfit_item_ids, preparation_item_ids = _validate_scheduled_outfit(
            conn, user_id, outfit, source, ready_confirmed_item_ids
        )
        for item_id in preparation_item_ids:
            conn.execute(
                """
                UPDATE clothes
                SET wear_cooldown_until = NULL,
                    availability_status = 'ready',
                    ironing_status = 'ready',
                    expected_available_at = NULL,
                    last_status_updated = CURRENT_TIMESTAMP
                WHERE id = ? AND user_id = ?
                """,
                (item_id, user_id)
            )
        schedule_id = str(uuid.uuid4())
        cursor = conn.execute(
            """
            INSERT INTO weekday_outfits
                (schedule_id, user_id, day_id, plan_date, occasion, outfit_json, source)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(schedule_id) DO NOTHING
            """,
            (schedule_id, user_id, day_id, planned_date.isoformat(), occasion, json.dumps(outfit), source)
        )
        conn.commit()
        if cursor.rowcount == 0:
            return None
        return {
            "schedule_id": schedule_id,
            "day_id": day_id,
            "plan_date": planned_date.isoformat(),
            "confirmation_status": "awaiting",
            "occasion": occasion,
            "outfit": outfit,
            "source": source
        }
    finally:
        conn.close()


def replace_weekday_outfit(
    schedule_id: str,
    user_id: int,
    expected_outfit_id: str,
    outfit: dict,
    source: str,
    ready_confirmed_item_ids: Optional[list] = None
):
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT outfit_json, occasion, source, day_id, plan_date, confirmation_status
            FROM weekday_outfits
            WHERE user_id = ? AND schedule_id = ?
            """,
            (user_id, schedule_id)
        ).fetchone()
        if not row or json.loads(row["outfit_json"]).get("id") != expected_outfit_id:
            return None
        if row["confirmation_status"] != "awaiting":
            return None

        _, preparation_item_ids = _validate_scheduled_outfit(
            conn, user_id, outfit, source, ready_confirmed_item_ids
        )
        cursor = conn.execute(
            """
            UPDATE weekday_outfits
            SET outfit_json = ?, source = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND schedule_id = ? AND outfit_json = ?
              AND confirmation_status = 'awaiting'
            """,
            (json.dumps(outfit), source, user_id, schedule_id, row["outfit_json"])
        )
        if cursor.rowcount == 0:
            return None
        for item_id in preparation_item_ids:
            conn.execute(
                """
                UPDATE clothes
                SET wear_cooldown_until = NULL,
                    availability_status = 'ready',
                    ironing_status = 'ready',
                    expected_available_at = NULL,
                    last_status_updated = CURRENT_TIMESTAMP
                WHERE id = ? AND user_id = ?
                """,
                (item_id, user_id)
            )
        conn.commit()
        return {
            "schedule_id": schedule_id,
            "day_id": row["day_id"],
            "plan_date": row["plan_date"],
            "confirmation_status": "awaiting",
            "occasion": row["occasion"],
            "outfit": outfit,
            "source": source
        }
    finally:
        conn.close()


def remove_weekday_outfit(schedule_id: str, user_id: int = 1):
    conn = get_connection()
    try:
        cursor = conn.execute(
            "DELETE FROM weekday_outfits WHERE user_id = ? AND schedule_id = ?",
            (user_id, schedule_id)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def remove_future_outfits_using_item(item_id: str, user_id: int = 1, from_date: Optional[str] = None):
    earliest_date = from_date or date.today().isoformat()
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT schedule_id, outfit_json FROM weekday_outfits
            WHERE user_id = ? AND plan_date >= ? AND confirmation_status = 'awaiting'
            """,
            (user_id, earliest_date)
        ).fetchall()
        affected_ids = [
            row["schedule_id"]
            for row in rows
            if any(
                isinstance(item, dict) and str(item.get("id")) == str(item_id)
                for item in (json.loads(row["outfit_json"]).get("slotItems") or {}).values()
            )
        ]
        conn.executemany(
            "DELETE FROM weekday_outfits WHERE user_id = ? AND schedule_id = ?",
            [(user_id, schedule_id) for schedule_id in affected_ids]
        )
        conn.commit()
        return affected_ids
    finally:
        conn.close()


def remove_unavailable_future_outfits(user_id: int = 1, from_date: Optional[str] = None):
    earliest_date = from_date or date.today().isoformat()
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT schedule_id, outfit_json FROM weekday_outfits
            WHERE user_id = ? AND plan_date >= ? AND confirmation_status = 'awaiting'
            """,
            (user_id, earliest_date)
        ).fetchall()
        affected_ids = []
        for row in rows:
            item_ids = list(dict.fromkeys(
                str(item["id"])
                for item in (json.loads(row["outfit_json"]).get("slotItems") or {}).values()
                if isinstance(item, dict) and item.get("id") is not None
            ))
            for item_id in item_ids:
                item = conn.execute(
                    """
                    SELECT availability_status, ironing_status
                    FROM clothes WHERE id = ? AND user_id = ?
                    """,
                    (item_id, user_id)
                ).fetchone()
                if (
                    not item
                    or item["availability_status"] not in {"ready", "available"}
                    or item["ironing_status"] != "ready"
                ):
                    affected_ids.append(row["schedule_id"])
                    break
        conn.executemany(
            "DELETE FROM weekday_outfits WHERE user_id = ? AND schedule_id = ?",
            [(user_id, schedule_id) for schedule_id in affected_ids]
        )
        conn.commit()
        return affected_ids
    finally:
        conn.close()


def confirm_weekday_outfit(schedule_id: str, user_id: int, worn: bool):
    status = "worn" if worn else "not_worn"
    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            UPDATE weekday_outfits
            SET confirmation_status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND schedule_id = ? AND confirmation_status = 'awaiting'
            """,
            (status, user_id, schedule_id)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()
