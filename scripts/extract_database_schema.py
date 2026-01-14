"""
Extract Database Schema - Generate complete CREATE TABLE statements from existing database
This will help create an updated setup_db.py based on your current database structure
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import mysql.connector
from config.settings import Config

def get_connection():
    """Get a direct database connection"""
    return mysql.connector.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        port=Config.DB_PORT
    )

def extract_all_tables():
    """Get list of all tables in the database"""
    db = get_connection()
    cursor = db.cursor()
    
    cursor.execute(f"SHOW TABLES FROM {Config.DB_NAME}")
    tables = [table[0] for table in cursor.fetchall()]
    
    cursor.close()
    db.close()
    
    return tables

def extract_create_statement(table_name):
    """Get the CREATE TABLE statement for a specific table"""
    db = get_connection()
    cursor = db.cursor()
    
    cursor.execute(f"SHOW CREATE TABLE {table_name}")
    result = cursor.fetchone()
    create_statement = result[1] if result else None
    
    cursor.close()
    db.close()
    
    return create_statement

def extract_table_info(table_name):
    """Get detailed information about a table's columns"""
    db = get_connection()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute(f"""
        SELECT 
            COLUMN_NAME,
            COLUMN_TYPE,
            IS_NULLABLE,
            COLUMN_KEY,
            COLUMN_DEFAULT,
            EXTRA,
            COLUMN_COMMENT
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
        ORDER BY ORDINAL_POSITION
    """, (Config.DB_NAME, table_name))
    
    columns = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return columns

def extract_indexes(table_name):
    """Get all indexes for a table"""
    db = get_connection()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute(f"""
        SELECT 
            INDEX_NAME,
            COLUMN_NAME,
            NON_UNIQUE,
            INDEX_TYPE,
            SEQ_IN_INDEX
        FROM INFORMATION_SCHEMA.STATISTICS
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
        ORDER BY INDEX_NAME, SEQ_IN_INDEX
    """, (Config.DB_NAME, table_name))
    
    indexes = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return indexes

def extract_foreign_keys(table_name):
    """Get all foreign key constraints for a table"""
    db = get_connection()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute(f"""
        SELECT 
            CONSTRAINT_NAME,
            COLUMN_NAME,
            REFERENCED_TABLE_NAME,
            REFERENCED_COLUMN_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = %s 
            AND REFERENCED_TABLE_NAME IS NOT NULL
        ORDER BY CONSTRAINT_NAME, ORDINAL_POSITION
    """, (Config.DB_NAME, table_name))
    
    foreign_keys = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return foreign_keys

def main():
    print("=" * 80)
    print("DATABASE SCHEMA EXTRACTION")
    print("=" * 80)
    print(f"Database: {Config.DB_NAME}")
    print(f"Host: {Config.DB_HOST}")
    print("=" * 80)
    print()
    
    # Get all tables
    tables = extract_all_tables()
    print(f"Found {len(tables)} tables:")
    for i, table in enumerate(tables, 1):
        print(f"  {i}. {table}")
    print()
    print("=" * 80)
    print()
    
    # Extract complete schema for each table
    for table in tables:
        print(f"\n{'=' * 80}")
        print(f"TABLE: {table}")
        print('=' * 80)
        
        # Get CREATE TABLE statement (most complete)
        create_stmt = extract_create_statement(table)
        if create_stmt:
            print("\nCREATE TABLE Statement:")
            print("-" * 80)
            print(create_stmt)
            print()
        
        # Get column details
        print("\nColumn Details:")
        print("-" * 80)
        columns = extract_table_info(table)
        for col in columns:
            nullable = "NULL" if col['IS_NULLABLE'] == 'YES' else "NOT NULL"
            default = f"DEFAULT {col['COLUMN_DEFAULT']}" if col['COLUMN_DEFAULT'] else ""
            key = f"[{col['COLUMN_KEY']}]" if col['COLUMN_KEY'] else ""
            extra = col['EXTRA'] if col['EXTRA'] else ""
            comment = f"-- {col['COLUMN_COMMENT']}" if col['COLUMN_COMMENT'] else ""
            
            print(f"  {col['COLUMN_NAME']:<30} {col['COLUMN_TYPE']:<20} {nullable:<10} {key:<10} {extra:<20} {default:<20} {comment}")
        
        # Get indexes
        indexes = extract_indexes(table)
        if indexes:
            print("\nIndexes:")
            print("-" * 80)
            current_index = None
            for idx in indexes:
                if idx['INDEX_NAME'] != current_index:
                    unique = "" if idx['NON_UNIQUE'] else "UNIQUE"
                    print(f"  {unique} {idx['INDEX_NAME']} ({idx['INDEX_TYPE']})")
                    current_index = idx['INDEX_NAME']
                print(f"    - {idx['COLUMN_NAME']}")
        
        # Get foreign keys
        foreign_keys = extract_foreign_keys(table)
        if foreign_keys:
            print("\nForeign Keys:")
            print("-" * 80)
            for fk in foreign_keys:
                print(f"  {fk['CONSTRAINT_NAME']}")
                print(f"    {fk['COLUMN_NAME']} -> {fk['REFERENCED_TABLE_NAME']}.{fk['REFERENCED_COLUMN_NAME']}")
        
        print()
    
    print("\n" + "=" * 80)
    print("EXTRACTION COMPLETE")
    print("=" * 80)
    print("\nYou can now use this information to create an updated setup_db.py file.")
    print("Copy the CREATE TABLE statements and organize them in dependency order.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
