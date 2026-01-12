"""
Migration: Add progress tracking fields to reduction_initiatives
Run once: python scripts/migrate_initiatives_progress.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.cache import get_database


def column_exists(db, table_name: str, column_name: str) -> bool:
    query = """
        SELECT COUNT(*)
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
          AND COLUMN_NAME = %s
    """
    result = db.fetch_one(query, (table_name, column_name))
    return bool(result and result[0])


def migrate():
    db = get_database()
    if not db.connect():
        print("❌ Failed to connect to database")
        return False

    try:
        # 1) Add progress_type
        if not column_exists(db, "reduction_initiatives", "progress_type"):
            add_progress_type = """
                ALTER TABLE reduction_initiatives
                ADD COLUMN progress_type VARCHAR(50) DEFAULT 'percentage'
                COMMENT 'Type of progress tracking: percentage, checklist, or numeric'
            """
            if db.execute_query(add_progress_type):
                print("✅ Added column progress_type (VARCHAR(50), DEFAULT 'percentage')")
            else:
                print("⚠️ Could not add progress_type")
        else:
            print("ℹ️ progress_type already exists; skipping")

        # 2) Add target_value
        if not column_exists(db, "reduction_initiatives", "target_value"):
            add_target_value = """
                ALTER TABLE reduction_initiatives
                ADD COLUMN target_value DECIMAL(10,2) NULL
                COMMENT 'Target value for numeric or checklist progress (e.g., 100 for percentage, 10 for checklist items)'
            """
            if db.execute_query(add_target_value):
                print("✅ Added column target_value (DECIMAL(10,2), NULL)")
            else:
                print("⚠️ Could not add target_value")
        else:
            print("ℹ️ target_value already exists; skipping")

        # 3) Add current_progress
        if not column_exists(db, "reduction_initiatives", "current_progress"):
            add_current_progress = """
                ALTER TABLE reduction_initiatives
                ADD COLUMN current_progress DECIMAL(10,2) DEFAULT 0
                COMMENT 'Current progress value (percentage, items completed, or custom metric)'
            """
            if db.execute_query(add_current_progress):
                print("✅ Added column current_progress (DECIMAL(10,2), DEFAULT 0)")
            else:
                print("⚠️ Could not add current_progress")
        else:
            print("ℹ️ current_progress already exists; skipping")

        # 4) Add progress_notes
        if not column_exists(db, "reduction_initiatives", "progress_notes"):
            add_progress_notes = """
                ALTER TABLE reduction_initiatives
                ADD COLUMN progress_notes TEXT NULL
                COMMENT 'Notes about recent progress updates'
            """
            if db.execute_query(add_progress_notes):
                print("✅ Added column progress_notes (TEXT, NULL)")
            else:
                print("⚠️ Could not add progress_notes")
        else:
            print("ℹ️ progress_notes already exists; skipping")

        # 5) Add last_progress_update
        if not column_exists(db, "reduction_initiatives", "last_progress_update"):
            add_last_update = """
                ALTER TABLE reduction_initiatives
                ADD COLUMN last_progress_update TIMESTAMP NULL
                COMMENT 'Timestamp of last progress update'
            """
            if db.execute_query(add_last_update):
                print("✅ Added column last_progress_update (TIMESTAMP, NULL)")
            else:
                print("⚠️ Could not add last_progress_update")
        else:
            print("ℹ️ last_progress_update already exists; skipping")

        print("\n🎯 Migration complete - Progress tracking fields added to reduction_initiatives!")
        print("\nNew fields:")
        print("  - progress_type: Type of progress tracking")
        print("  - target_value: Target/goal value")
        print("  - current_progress: Current progress value")
        print("  - progress_notes: Notes about progress")
        print("  - last_progress_update: Last update timestamp")
        
        return True
    finally:
        db.disconnect()


if __name__ == "__main__":
    migrate()