"""
Migrate existing hexadecimal session_string values to Telethon StringSession format.

Usage:
    python -m backend.scripts.migrate_sessions
"""

import os
import shutil
import sys
import tempfile

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from telethon.sessions import SQLiteSession, StringSession

from config import settings
from models.account import Account


def get_db_url() -> str:
    return settings.database_url


def migrate_hex_to_string_session():
    """Convert all hex-encoded sessions to StringSession format."""
    engine = create_engine(get_db_url())
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Get all accounts with session_string
        accounts = db.query(Account).filter(
            Account.session_string.isnot(None),
            Account.session_string != ""
        ).all()

        print(f"Found {len(accounts)} accounts with sessions")

        migrated = 0
        skipped = 0
        failed = 0

        for account in accounts:
            session_str = account.session_string

            # Skip if already in StringSession format (Base64-like, starts with '1')
            if session_str and (session_str.startswith('1') or '+' in session_str or '/' in session_str):
                print(f"⏭️  {account.phone}: Already in StringSession format")
                skipped += 1
                continue

            # Try to convert hex to StringSession
            try:
                # Decode hex to bytes
                session_bytes = bytes.fromhex(session_str)

                # Write to temp file
                temp_dir = tempfile.mkdtemp()
                try:
                    safe_phone = os.path.basename(account.phone)
                    temp_path = os.path.join(temp_dir, safe_phone)
                    with open(temp_path + ".session", "wb") as f:
                        f.write(session_bytes)

                    # Load as SQLiteSession and convert
                    sqlite_session = SQLiteSession(temp_path)
                    sqlite_session.save()
                    string_session = StringSession.save(sqlite_session)

                    if not string_session:
                        raise ValueError("StringSession.save() returned empty string")

                    # Update database
                    account.session_string = string_session
                    db.commit()

                    print(f"✅ {account.phone}: Migrated successfully")
                    migrated += 1

                finally:
                    shutil.rmtree(temp_dir, ignore_errors=True)

            except Exception as e:
                print(f"❌ {account.phone}: Migration failed - {str(e)}")
                failed += 1
                db.rollback()

        print("\n" + "=" * 60)
        print("Migration Summary:")
        print(f"  ✅ Migrated: {migrated}")
        print(f"  ⏭️  Skipped:  {skipped}")
        print(f"  ❌ Failed:   {failed}")
        print("=" * 60)

    finally:
        db.close()


if __name__ == "__main__":
    print("Starting session migration...\n")
    migrate_hex_to_string_session()
    print("\nMigration complete!")
