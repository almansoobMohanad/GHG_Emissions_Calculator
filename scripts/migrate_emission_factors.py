"""
Database Migration Script
Adds fields for Emission Factor Management
Run this ONCE to add new columns to existing tables
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import mysql.connector
from mysql.connector import Error
from config.settings import config

def migrate_database():
    """Add new columns for emission factor management"""
    
    print("=" * 70)
    print("🔧 Database Migration - Emission Factor Management")
    print("=" * 70)
    
    try:
        connection = mysql.connector.connect(**config.database_config)
        cursor = connection.cursor()
        print("✅ Connected to database")
        
        # Check if columns already exist
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'ghg_emission_sources' 
            AND COLUMN_NAME IN ('source_type', 'company_id', 'is_visible_in_ui', 
                               'data_source_reference', 'version', 'superseded_by')
        """, (config.database_config['database'],))
        
        existing_columns = [row[0] for row in cursor.fetchall()]
        
        if len(existing_columns) > 0:
            print(f"⚠️  Warning: Some columns already exist: {existing_columns}")
            response = input("Continue anyway? (y/n): ")
            if response.lower() != 'y':
                print("Migration cancelled.")
                return False
        
        print("\n📝 Adding new columns to ghg_emission_sources...")
        
        # Add columns one by one to handle existing columns gracefully
        migrations = [
            ("source_type", """
                ALTER TABLE ghg_emission_sources 
                ADD COLUMN source_type ENUM('system', 'custom') DEFAULT 'system'
            """),
            ("company_id", """
                ALTER TABLE ghg_emission_sources 
                ADD COLUMN company_id INT NULL,
                ADD CONSTRAINT fk_source_company 
                FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
            """),
            ("is_visible_in_ui", """
                ALTER TABLE ghg_emission_sources 
                ADD COLUMN is_visible_in_ui BOOLEAN DEFAULT TRUE
            """),
            ("data_source_reference", """
                ALTER TABLE ghg_emission_sources 
                ADD COLUMN data_source_reference VARCHAR(500) NULL
            """),
            ("version", """
                ALTER TABLE ghg_emission_sources 
                ADD COLUMN version INT DEFAULT 1
            """),
            ("superseded_by", """
                ALTER TABLE ghg_emission_sources 
                ADD COLUMN superseded_by INT NULL,
                ADD CONSTRAINT fk_source_superseded 
                FOREIGN KEY (superseded_by) REFERENCES ghg_emission_sources(id) ON DELETE SET NULL
            """),
        ]
        
        for column_name, query in migrations:
            if column_name not in existing_columns:
                try:
                    cursor.execute(query)
                    connection.commit()
                    print(f"  ✅ Added column: {column_name}")
                except Error as e:
                    if "Duplicate column" in str(e):
                        print(f"  ⏭️  Column {column_name} already exists")
                    else:
                        print(f"  ❌ Failed to add {column_name}: {e}")
                        raise
            else:
                print(f"  ⏭️  Column {column_name} already exists")
        
        # Create history table
        print("\n📝 Creating emission source history table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ghg_source_history (
                history_id INT AUTO_INCREMENT PRIMARY KEY,
                source_id INT NOT NULL,
                emission_factor DECIMAL(15,8) NOT NULL,
                changed_by INT NOT NULL,
                changed_at DATETIME NOT NULL,
                change_reason TEXT,
                FOREIGN KEY (source_id) REFERENCES ghg_emission_sources(id) ON DELETE CASCADE,
                FOREIGN KEY (changed_by) REFERENCES users(id) ON DELETE RESTRICT,
                INDEX idx_source (source_id),
                INDEX idx_changed_at (changed_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        connection.commit()
        print("  ✅ History table created")
        
        # Update existing sources to be 'system' type
        print("\n📝 Updating existing sources to 'system' type...")
        cursor.execute("""
            UPDATE ghg_emission_sources 
            SET source_type = 'system', 
                company_id = NULL,
                is_visible_in_ui = TRUE,
                version = 1
            WHERE source_type IS NULL OR source_type = 'system'
        """)
        connection.commit()
        rows_updated = cursor.rowcount
        print(f"  ✅ Updated {rows_updated} existing sources")
        
        # Verify setup
        print("\n🔍 Verifying migration...")
        cursor.execute("SELECT COUNT(*) FROM ghg_emission_sources WHERE source_type = 'system'")
        system_count = cursor.fetchone()[0]
        print(f"  ✅ System sources: {system_count}")
        
        cursor.execute("SELECT COUNT(*) FROM ghg_emission_sources WHERE source_type = 'custom'")
        custom_count = cursor.fetchone()[0]
        print(f"  ✅ Custom sources: {custom_count}")
        
        cursor.close()
        connection.close()
        
        print("\n" + "=" * 70)
        print("🎉 Migration completed successfully!")
        print("=" * 70)
        print("\n✅ Your database is ready for Emission Factor Management")
        print("\n")
        
        return True
        
    except Error as e:
        print(f"\n❌ Migration failed: {e}")
        if connection:
            connection.rollback()
            connection.close()
        return False

if __name__ == "__main__":
    success = migrate_database()
    sys.exit(0 if success else 1)