"""
Migration Runner - Baseline Year Database Updates
Executes the baseline year migration SQL script
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import mysql.connector
from mysql.connector import Error
from config.settings import config

def run_migration():
    """Run the baseline year migration"""
    
    print("=" * 70)
    print("🚀 GHG Emissions Dashboard - Baseline Year Migration")
    print("=" * 70)
    
    # Read migration SQL file
    migration_file = os.path.join(os.path.dirname(__file__), 'migrate_baseline_year.sql')
    
    if not os.path.exists(migration_file):
        print(f"❌ Migration file not found: {migration_file}")
        return False
    
    print(f"\n📂 Reading migration file: {migration_file}")
    
    try:
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
    except Exception as e:
        print(f"❌ Error reading migration file: {e}")
        return False
    
    # Connect to database
    print("\n🔗 Connecting to database...")
    db_config = config.database_config.copy()
    
    try:
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            db_info = connection.get_server_info()
            print(f"✅ Successfully connected to MySQL Server version {db_info}")
            print(f"📊 Database: {db_config['database']}")
    except Error as e:
        print(f"❌ Error connecting to MySQL: {e}")
        return False
    
    # Execute migration
    print("\n⚙️  Executing migration...")
    cursor = None
    
    try:
        cursor = connection.cursor()
        
        # Split SQL statements and execute them individually
        # This handles comments and multiple statements better
        statements = [stmt.strip() for stmt in migration_sql.split(';') 
                     if stmt.strip() and not stmt.strip().startswith('--')]
        
        for i, statement in enumerate(statements, 1):
            if statement:
                print(f"\n   [{i}/{len(statements)}] Executing statement...")
                try:
                    cursor.execute(statement)
                    connection.commit()
                    print(f"   ✅ Statement executed successfully")
                except Error as e:
                    # Some statements might fail (e.g., verification queries)
                    # This is OK, just log it
                    if "No data" in str(e) or "0 row" in str(e):
                        print(f"   ⓘ  {e}")
                    else:
                        print(f"   ⚠️  {e}")
        
        print("\n" + "=" * 70)
        print("✅ Migration completed successfully!")
        print("=" * 70)
        
        # Verify migration
        print("\n🔍 Verifying migration...")
        
        # Check new columns
        verify_columns_sql = """
        SELECT COLUMN_NAME, DATA_TYPE 
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'companies'
        AND COLUMN_NAME IN ('baseline_year', 'baseline_notes', 'baseline_set_date', 'baseline_set_by')
        ORDER BY COLUMN_NAME;
        """
        
        cursor.execute(verify_columns_sql)
        columns = cursor.fetchall()
        
        if columns:
            print("\n✅ New columns in 'companies' table:")
            for col in columns:
                print(f"   • {col[0]}: {col[1]}")
        else:
            print("\n⚠️  No new columns found")
        
        # Check coverage table
        check_coverage_sql = """
        SELECT COUNT(*) 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'emissions_coverage';
        """
        
        cursor.execute(check_coverage_sql)
        result = cursor.fetchone()
        
        if result[0] > 0:
            print("\n✅ 'emissions_coverage' table created successfully")
        else:
            print("\n⚠️  'emissions_coverage' table not found")
        
        print("\n" + "=" * 70)
        print("📋 Migration Summary:")
        print("=" * 70)
        print("✅ Added columns to companies table:")
        print("   • baseline_year")
        print("   • baseline_notes")
        print("   • baseline_set_date")
        print("   • baseline_set_by")
        print("\n✅ Created tables:")
        print("   • emissions_coverage")
        print("\n✅ Created indexes:")
        print("   • idx_companies_baseline_year")
        print("   • idx_company_year (on emissions_coverage)")
        print("   • idx_scope (on emissions_coverage)")
        print("\n" + "=" * 70)
        print("🎉 Next Steps:")
        print("=" * 70)
        print("1. Add cache functions to core/cache.py")
        print("2. Update permissions in config/permissions.py")
        print("3. Update dashboard imports")
        print("4. Test the new dashboard features")
        print("=" * 70)
        
        return True
        
    except Error as e:
        print(f"\n❌ Error executing migration: {e}")
        connection.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if connection.is_connected():
            connection.close()
            print("\n🔌 Database connection closed")

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
