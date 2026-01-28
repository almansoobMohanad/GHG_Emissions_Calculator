"""
Baseline Year Migration Checker
Automatically checks if baseline year columns exist in the database.
If they don't exist, runs the migration automatically.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import mysql.connector
from mysql.connector import Error
from config.settings import config

def check_baseline_year_exists():
    """Check if baseline_year column exists in companies table"""
    try:
        connection = mysql.connector.connect(**config.database_config)
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'companies' 
            AND COLUMN_NAME = 'baseline_year'
        """, (config.database_config['database'],))
        
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        
        return result is not None
        
    except Error as e:
        print(f"❌ Error checking database: {e}")
        return False

def migrate_baseline_year():
    """Migrate baseline year columns to companies table"""
    try:
        connection = mysql.connector.connect(**config.database_config)
        cursor = connection.cursor()
        
        print("📝 Adding baseline year columns...")
        
        # Add baseline_year columns
        cursor.execute("""
            ALTER TABLE companies 
            ADD COLUMN baseline_year INT DEFAULT NULL COMMENT 'The year designated as the reference point for emissions comparisons',
            ADD COLUMN baseline_notes TEXT DEFAULT NULL COMMENT 'Notes about why this baseline year was chosen',
            ADD COLUMN baseline_set_date DATE DEFAULT NULL COMMENT 'When the baseline year was designated',
            ADD COLUMN baseline_set_by INT DEFAULT NULL COMMENT 'User ID who set the baseline year'
        """)
        connection.commit()
        print("  ✅ Added baseline year columns")
        
        # Add index for better performance
        print("📝 Adding index on baseline_year...")
        try:
            cursor.execute("""
                CREATE INDEX idx_companies_baseline_year 
                ON companies(baseline_year)
            """)
            connection.commit()
            print("  ✅ Added index: idx_companies_baseline_year")
        except Error as e:
            if "Duplicate" in str(e):
                print("  ⏭️  Index already exists")
            else:
                raise
        
        # Add foreign key constraint for baseline_set_by
        print("📝 Adding foreign key constraint...")
        try:
            cursor.execute("""
                ALTER TABLE companies 
                ADD CONSTRAINT fk_baseline_set_by 
                FOREIGN KEY (baseline_set_by) REFERENCES users(id) ON DELETE SET NULL
            """)
            connection.commit()
            print("  ✅ Added foreign key constraint")
        except Error as e:
            if "already exists" in str(e) or "Duplicate" in str(e):
                print("  ⏭️  Constraint already exists")
            else:
                raise
        
        # Create emissions_coverage table
        print("📝 Creating emissions_coverage table...")
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS emissions_coverage (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    company_id INT NOT NULL,
                    year INT NOT NULL,
                    scope_number INT NOT NULL CHECK (scope_number IN (1, 2, 3)),
                    coverage_percentage DECIMAL(5,2) DEFAULT NULL COMMENT 'Estimated percentage of emissions covered (0-100)',
                    total_expected_sources INT DEFAULT NULL COMMENT 'Total number of emission sources expected',
                    tracked_sources INT DEFAULT NULL COMMENT 'Number of sources actually tracked',
                    notes TEXT COMMENT 'Additional context about coverage for this scope/year',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
                    UNIQUE KEY unique_company_year_scope (company_id, year, scope_number),
                    INDEX idx_company_year (company_id, year),
                    INDEX idx_scope (scope_number)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Tracks data coverage evolution over time'
            """)
            connection.commit()
            print("  ✅ Created emissions_coverage table")
        except Error as e:
            if "already exists" in str(e):
                print("  ⏭️  Table already exists")
            else:
                raise
        
        # Verify
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = %s
            AND TABLE_NAME = 'companies'
            AND COLUMN_NAME IN ('baseline_year', 'baseline_notes', 'baseline_set_date', 'baseline_set_by')
            ORDER BY COLUMN_NAME
        """, (config.database_config['database'],))
        
        results = cursor.fetchall()
        if results:
            print("\n✅ Verified columns:")
            for col_name, col_type in results:
                print(f"   - {col_name}: {col_type}")
        
        cursor.close()
        connection.close()
        
        print("\n🎉 Migration completed successfully!")
        return True
        
    except Error as e:
        print(f"❌ Migration failed: {e}")
        return False

def main():
    """Main function - check and migrate if needed"""
    print("=" * 70)
    print("🔍 Baseline Year Migration Checker")
    print("=" * 70)
    
    print(f"\n🔗 Checking database: {config.database_config['database']}")
    print(f"   Host: {config.database_config['host']}")
    
    if check_baseline_year_exists():
        print("\n✅ Baseline year columns already exist in the database!")
        print("   No migration needed.")
        return True
    else:
        print("\n⚠️  Baseline year columns NOT found in database")
        print("🚀 Running migration...\n")
        
        success = migrate_baseline_year()
        
        if success:
            print("\n" + "=" * 70)
            print("✅ BASELINE YEAR MIGRATION COMPLETE")
            print("=" * 70)
            return True
        else:
            print("\n" + "=" * 70)
            print("❌ MIGRATION FAILED")
            print("=" * 70)
            return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
