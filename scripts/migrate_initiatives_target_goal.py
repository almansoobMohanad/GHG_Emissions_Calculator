"""
Migration: add target_goal to reduction_initiatives and relax expected_reduction nullability
Run once: python scripts/migrate_initiatives_target_goal.py
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
        # 1) Add target_goal if missing
        if not column_exists(db, "reduction_initiatives", "target_goal"):
            add_goal = """
                ALTER TABLE reduction_initiatives
                ADD COLUMN target_goal TEXT NULL AFTER description
            """
            if db.execute_query(add_goal):
                print("✅ Added column target_goal (TEXT, NULL)")
            else:
                print("⚠️ Could not add target_goal (maybe already exists)")
        else:
            print("ℹ️ target_goal already exists; skipping")

        # 2) Relax expected_reduction to allow NULL (optional field now)
        relax_expected = """
            ALTER TABLE reduction_initiatives
            MODIFY expected_reduction DECIMAL(15,2) NULL COMMENT 'Expected annual CO2e reduction in tonnes'
        """
        if db.execute_query(relax_expected):
            print("✅ expected_reduction is now NULLable")
        else:
            print("⚠️ Could not alter expected_reduction (already NULLable or error)")

        print("\n🎯 Migration complete.")
        return True
    finally:
        db.disconnect()


if __name__ == "__main__":
    migrate()
