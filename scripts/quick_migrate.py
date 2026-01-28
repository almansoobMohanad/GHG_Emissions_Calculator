"""Quick migration runner for baseline year columns"""
import mysql.connector
from mysql.connector import Error
import os
import sys

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to load from config, fallback to environment variables
try:
    from config.settings import config
    db_config = config.database_config
except:
    # Fallback to environment variables or defaults
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', 'root'),
        'database': os.getenv('DB_NAME', 'ghg_emissions'),
        'port': int(os.getenv('DB_PORT', 3306))
    }

print(f"🔗 Connecting to {db_config.get('host')}:{db_config.get('port')}/{db_config.get('database')}...")
print(f"📝 Using credentials: user={db_config.get('user')}")

# If no host is configured, use AWS RDS
if not db_config.get('host') or db_config.get('host') == 'localhost':
    print("⚠️  No host configured, trying AWS RDS...")
    db_config['host'] = 'ghg-1.c9260sqmwpz9.ap-southeast-1.rds.amazonaws.com'
    db_config['database'] = 'ghg_emissions_calculator_db'

try:
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    
    print("=" * 70)
    print("🚀 Adding baseline year columns to companies table...")
    print("=" * 70)
    
    # Read and execute the migration SQL
    with open('migrate_baseline_year.sql', 'r') as f:
        sql_content = f.read()
    
    # Split by semicolon and execute each statement
    statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip() and not stmt.strip().startswith('--')]
    
    for i, statement in enumerate(statements, 1):
        # Skip comments and empty lines
        if statement.startswith('/*') or not statement:
            continue
            
        print(f"\n[{i}/{len(statements)}] Executing...")
        print(f"Statement preview: {statement[:80]}...")
        
        try:
            cursor.execute(statement)
            connection.commit()
            print(f"✅ Success!")
        except Error as e:
            # Check if it's just a "column already exists" error, which is OK
            if "already exists" in str(e) or "Duplicate" in str(e):
                print(f"⚠️  Column/index already exists (OK): {e}")
            else:
                print(f"❌ Error: {e}")
                connection.rollback()
    
    print("\n" + "=" * 70)
    print("✅ Migration completed!")
    print("=" * 70)
    
    # Verify the columns exist
    print("\n📋 Verifying columns...")
    verify_query = """
    SELECT COLUMN_NAME, DATA_TYPE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = %s
    AND TABLE_NAME = 'companies'
    AND COLUMN_NAME IN ('baseline_year', 'baseline_notes', 'baseline_set_date', 'baseline_set_by')
    """
    
    cursor.execute(verify_query, (db_config['database'],))
    results = cursor.fetchall()
    
    if results:
        print("✅ Columns verified:")
        for col_name, col_type in results:
            print(f"   - {col_name}: {col_type}")
    else:
        print("⚠️  Columns not found - migration may have failed")
    
    cursor.close()
    connection.close()
    
except Error as e:
    print(f"❌ Database error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
