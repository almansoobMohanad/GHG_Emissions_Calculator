"""
GHG Protocol Alignment Migration Script

Purpose:
- Align existing database records to the updated category/source model in
  scripts/setup_ghg_factors.py without clearing operational emissions data.

What it does:
1) Ensures scopes and categories exist using the latest setup script logic.
2) Remaps legacy category usage (e.g., S3-HOTEL, S3-MATERIALS) to protocol-aligned categories.
3) Applies source-code-based safety remaps for known groups.
4) Inserts any missing sources from the latest setup list.
5) Optionally deletes empty legacy categories.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import mysql.connector
from mysql.connector import Error
from config.settings import config
from scripts.setup_ghg_factors import GHGFactorsSetup


class GHGProtocolMigration:
    def __init__(self):
        self.connection = None
        self.db_config = config.database_config.copy()

    def connect(self):
        try:
            self.connection = mysql.connector.connect(**self.db_config)
            print("✅ Connected to database")
            return True
        except Error as e:
            print(f"❌ Connection failed: {e}")
            return False

    def disconnect(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("✅ Disconnected from database")

    def fetch_category_map(self):
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute("SELECT id, category_code FROM ghg_categories")
        rows = cursor.fetchall()
        cursor.close()
        return {row["category_code"]: row["id"] for row in rows}

    def run_update(self, query, params=None):
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        affected = cursor.rowcount
        cursor.close()
        return affected

    def remap_legacy_categories(self):
        print("\n🔄 Remapping legacy categories...")

        categories = self.fetch_category_map()
        legacy_to_standard = {
            # Legacy Scope 1/2 categories
            "S1-01": "S1-FUEL",
            "S1-02": "S1-FUGITIVE",
            "S1-03": "S1-PROCESS",
            "S1-04": "S1-PROCESS",
            "S2-01": "S2-ELECTRICITY",
            "S2-02": "S2-HEAT-STEAM",

            # Legacy Scope 3 shorthand categories
            "S3-01": "S3-01-GOODS",
            "S3-02": "S3-02-CAPITAL",
            "S3-03": "S3-03-FUEL-ENERGY",
            "S3-04": "S3-04-UPSTREAM-TRANSPORT",
            "S3-05": "S3-05-WASTE",
            "S3-06": "S3-06-BUSINESS-TRAVEL",
            "S3-07": "S3-07-COMMUTING",
            "S3-08": "S3-08-UPSTREAM-ASSETS",
            "S3-09": "S3-09-DOWNSTREAM-TRANSPORT",
            "S3-10": "S3-10-PROCESSING",
            "S3-11": "S3-11-USE-PRODUCTS",
            "S3-12": "S3-12-END-LIFE",
            "S3-13": "S3-13-DOWNSTREAM-ASSETS",
            "S3-14": "S3-14-FRANCHISES",
            "S3-15": "S3-15-INVESTMENTS",

            # Previously custom categories
            "S3-HOTEL": "S3-06-BUSINESS-TRAVEL",
            "S3-MATERIALS": "S3-01-GOODS",
        }

        moved_total = 0

        for legacy_code, target_code in legacy_to_standard.items():
            legacy_id = categories.get(legacy_code)
            target_id = categories.get(target_code)

            if not legacy_id:
                continue
            if not target_id:
                print(f"  ⚠️ Target category missing: {target_code}")
                continue

            moved = self.run_update(
                """
                UPDATE ghg_emission_sources
                SET category_id = %s
                WHERE category_id = %s
                """,
                (target_id, legacy_id),
            )
            moved_total += moved
            print(f"  ✅ {legacy_code} -> {target_code}: {moved} sources moved")

        return moved_total

    def remap_by_source_code_patterns(self):
        print("\n🧭 Applying source-code pattern remaps...")

        categories = self.fetch_category_map()
        rules = [
            ("S3-06-BUSINESS-TRAVEL", "S3-H-%"),
            ("S3-01-GOODS", "S3-M-%"),
            ("S3-01-GOODS", "S3-WT-%"),
            ("S3-04-UPSTREAM-TRANSPORT", "S3-FT-%"),
            ("S3-09-DOWNSTREAM-TRANSPORT", "S3-DT-%"),
        ]

        moved_total = 0

        for target_code, pattern in rules:
            target_id = categories.get(target_code)
            if not target_id:
                print(f"  ⚠️ Skipping {pattern}; missing target category {target_code}")
                continue

            moved = self.run_update(
                """
                UPDATE ghg_emission_sources
                SET category_id = %s
                WHERE source_code LIKE %s
                """,
                (target_id, pattern),
            )
            moved_total += moved
            print(f"  ✅ Pattern {pattern} -> {target_code}: {moved} sources aligned")

        return moved_total

    def remove_legacy_categories_if_empty(self):
        print("\n🧹 Cleaning legacy categories (if empty)...")

        legacy_codes = [
            "S1-01", "S1-02", "S1-03", "S1-04",
            "S2-01", "S2-02",
            "S3-01", "S3-02", "S3-03", "S3-04", "S3-05", "S3-06", "S3-07", "S3-08", "S3-09", "S3-10", "S3-11", "S3-12", "S3-13", "S3-14", "S3-15",
            "S3-HOTEL", "S3-MATERIALS",
        ]
        deleted = 0

        for code in legacy_codes:
            rows_deleted = self.run_update(
                """
                DELETE c
                FROM ghg_categories c
                LEFT JOIN ghg_emission_sources s ON s.category_id = c.id
                WHERE c.category_code = %s
                  AND s.id IS NULL
                """,
                (code,),
            )
            deleted += rows_deleted
            if rows_deleted > 0:
                print(f"  ✅ Deleted empty legacy category: {code}")
            else:
                print(f"  ⏭️ Kept {code} (not present or still referenced)")

        return deleted

    def show_summary(self):
        print("\n📊 Post-migration summary")
        cursor = self.connection.cursor(dictionary=True)

        cursor.execute("SELECT COUNT(*) AS count FROM ghg_categories")
        categories_count = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) AS count FROM ghg_emission_sources")
        sources_count = cursor.fetchone()["count"]

        cursor.execute(
            """
            SELECT c.category_code, COUNT(s.id) AS sources
            FROM ghg_categories c
            LEFT JOIN ghg_emission_sources s ON s.category_id = c.id
            GROUP BY c.category_code
            ORDER BY c.category_code
            """
        )
        by_category = cursor.fetchall()

        cursor.close()

        print(f"  ✅ Categories: {categories_count}")
        print(f"  ✅ Emission Sources: {sources_count}")
        print("\n  Scope/category source distribution:")
        for row in by_category:
            print(f"    - {row['category_code']}: {row['sources']}")

    def migrate(self, delete_legacy=False):
        print("=" * 70)
        print("🔧 GHG Protocol Schema Alignment Migration")
        print("=" * 70)

        if not self.connect():
            return False

        try:
            self.connection.start_transaction()

            setup = GHGFactorsSetup()
            setup.connection = self.connection

            def execute_without_commit(query, params=None):
                try:
                    if query and "INSERT INTO ghg_emission_sources" in query and params is not None:
                        cursor = self.connection.cursor()
                        cursor.execute(
                            """
                            INSERT INTO ghg_emission_sources
                            (category_id, source_code, source_name, emission_factor, unit, description, region, source_type, is_active)
                            VALUES (%s, %s, %s, %s, %s, %s, 'UK', 'system', 1)
                            ON DUPLICATE KEY UPDATE
                                category_id = IF(source_type = 'custom', category_id, VALUES(category_id)),
                                source_name = IF(source_type = 'custom', source_name, VALUES(source_name)),
                                emission_factor = IF(source_type = 'custom', emission_factor, VALUES(emission_factor)),
                                unit = IF(source_type = 'custom', unit, VALUES(unit)),
                                description = IF(source_type = 'custom', description, VALUES(description)),
                                region = IF(source_type = 'custom', region, 'UK'),
                                is_active = IF(source_type = 'custom', is_active, 1)
                            """,
                            params,
                        )
                        cursor.close()
                        return True

                    cursor = self.connection.cursor()
                    cursor.execute(query, params)
                    cursor.close()
                    return True
                except Error as e:
                    print(f"❌ Query failed: {e}")
                    return False

            setup.execute_query = execute_without_commit

            print("\n🧱 Ensuring scopes and categories from latest setup...")
            if not setup.setup_scopes():
                raise RuntimeError("Failed to ensure scopes")
            if not setup.setup_categories():
                raise RuntimeError("Failed to ensure categories")

            moved_legacy = self.remap_legacy_categories()
            moved_pattern = self.remap_by_source_code_patterns()

            print("\n➕ Syncing emission sources to latest definitions (insert/update)...")
            if not setup.setup_emission_sources():
                raise RuntimeError("Failed while syncing emission sources")

            deleted = 0
            if delete_legacy:
                deleted = self.remove_legacy_categories_if_empty()

            self.connection.commit()

            print("\n" + "=" * 70)
            print("✅ Migration completed successfully")
            print("=" * 70)
            print(f"  • Legacy category-based moves: {moved_legacy}")
            print(f"  • Source-code pattern alignments: {moved_pattern}")
            print("  • System source rows: upsert-synced by source_code")
            if delete_legacy:
                print(f"  • Empty legacy categories deleted: {deleted}")

            self.show_summary()
            return True

        except Exception as e:
            self.connection.rollback()
            print(f"\n❌ Migration failed: {e}")
            print("↩️  Rolled back all changes")
            return False

        finally:
            self.disconnect()


def main():
    delete_legacy = "--delete-legacy" in sys.argv

    if delete_legacy:
        print("⚠️  Legacy category deletion is enabled (--delete-legacy)")

    migration = GHGProtocolMigration()
    success = migration.migrate(delete_legacy=delete_legacy)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
