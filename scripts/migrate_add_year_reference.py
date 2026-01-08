"""
Database Migration Script - Add Reference Year
Adds reference_year field to ghg_emission_sources table
Run this ONCE after the previous migration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import mysql.connector
from mysql.connector import Error
from config.settings import config

def migrate_add_reference_year():
    """Add reference_year column for emission factor tracking"""
    
    print("=" * 70)
    print("🔧 Database Migration - Add Reference Year")
    print("=" * 70)
    
    try:
        connection = mysql.connector.connect(**config.database_config)
        cursor = connection.cursor()
        print("✅ Connected to database")
        
        # Check if column already exists
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'ghg_emission_sources' 
            AND COLUMN_NAME = 'reference_year'
        """, (config.database_config['database'],))
        
        existing = cursor.fetchone()
        
        if existing:
            print("⚠️  Warning: reference_year column already exists")
            response = input("Continue anyway? (y/n): ")
            if response.lower() != 'y':
                print("Migration cancelled.")
                return False
        
        print("\n📝 Adding reference_year column to ghg_emission_sources...")
        
        # Add reference_year column
        cursor.execute("""
            ALTER TABLE ghg_emission_sources 
            ADD COLUMN reference_year INT NULL 
            COMMENT 'Year of the emission factor reference/publication'
        """)
        connection.commit()
        print("  ✅ Added column: reference_year")
        
        # Add index for better querying by year
        print("\n📝 Adding index on reference_year...")
        try:
            cursor.execute("""
                CREATE INDEX idx_reference_year 
                ON ghg_emission_sources(reference_year)
            """)
            connection.commit()
            print("  ✅ Added index: idx_reference_year")
        except Error as e:
            if "Duplicate key" in str(e):
                print("  ⏭️  Index already exists")
            else:
                raise
        
        # Set default year for existing system sources (optional)
        print("\n📝 Setting default year for existing sources...")
        cursor.execute("""
            UPDATE ghg_emission_sources 
            SET reference_year = 2024
            WHERE reference_year IS NULL 
            AND source_type = 'system'
        """)
        connection.commit()
        rows_updated = cursor.rowcount
        print(f"  ✅ Updated {rows_updated} existing system sources to year 2024")
        
        # Verify setup
        print("\n🔍 Verifying migration...")
        cursor.execute("""
            SELECT reference_year, COUNT(*) as count 
            FROM ghg_emission_sources 
            GROUP BY reference_year
        """)
        results = cursor.fetchall()
        for year, count in results:
            year_display = year if year else "NULL"
            print(f"  ✅ Year {year_display}: {count} sources")
        
        cursor.close()
        connection.close()
        
        print("\n" + "=" * 70)
        print("🎉 Migration completed successfully!")
        print("=" * 70)
        print("\n✅ reference_year field is now available")
        print("💡 Tip: Update your emission factors with appropriate years")
        print("\n")
        
        return True
        
    except Error as e:
        print(f"\n❌ Migration failed: {e}")
        if connection:
            connection.rollback()
            connection.close()
        return False

if __name__ == "__main__":
    success = migrate_add_reference_year()
    sys.exit(0 if success else 1)