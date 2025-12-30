"""
Database Migration Script for Reduction Tracker
Save as: scripts/create_reduction_tables.py

Run this script once to create the necessary tables in your database
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.cache import get_database

def create_reduction_tables():
    """
    Create the tables needed for the Reduction Tracker feature
    """
    db = get_database()
    
    if not db.connect():
        print("❌ Failed to connect to database")
        return False
    
    print("🔄 Creating Reduction Tracker tables...")
    
    # Table 1: Reduction Goals
    create_goals_table = """
    CREATE TABLE IF NOT EXISTS reduction_goals (
        id INT AUTO_INCREMENT PRIMARY KEY,
        company_id INT NOT NULL,
        baseline_year INT NOT NULL,
        baseline_emissions DECIMAL(15,2) NOT NULL COMMENT 'Baseline emissions in tonnes CO2e',
        target_year INT NOT NULL,
        target_reduction_percentage DECIMAL(5,2) NOT NULL COMMENT 'Target reduction percentage',
        framework VARCHAR(100) COMMENT 'e.g., SBTi, Net Zero, Paris Agreement',
        description TEXT COMMENT 'Additional details about the goal',
        status ENUM('active', 'inactive', 'achieved') DEFAULT 'active',
        created_by INT COMMENT 'User ID who created this goal',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        
        FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
        FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
        
        INDEX idx_company_status (company_id, status),
        INDEX idx_target_year (target_year)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Company emission reduction goals';
    """
    
    # Table 2: Reduction Initiatives
    create_initiatives_table = """
    CREATE TABLE IF NOT EXISTS reduction_initiatives (
        id INT AUTO_INCREMENT PRIMARY KEY,
        company_id INT NOT NULL,
        initiative_name VARCHAR(255) NOT NULL,
        description TEXT COMMENT 'Detailed description and implementation plan',
        target_scopes VARCHAR(100) COMMENT 'Comma-separated scopes (e.g., Scope 1,Scope 2)',
        expected_reduction DECIMAL(15,2) NOT NULL COMMENT 'Expected annual CO2e reduction in tonnes',
        actual_reduction DECIMAL(15,2) COMMENT 'Actual achieved reduction in tonnes',
        estimated_cost DECIMAL(15,2) COMMENT 'Estimated implementation cost',
        actual_cost DECIMAL(15,2) COMMENT 'Actual cost incurred',
        status ENUM('Planned', 'In Progress', 'Completed', 'On Hold', 'Cancelled') DEFAULT 'Planned',
        start_date DATE COMMENT 'Initiative start date',
        target_completion_date DATE COMMENT 'Target completion date',
        actual_completion_date DATE COMMENT 'Actual completion date',
        responsible_person VARCHAR(255) COMMENT 'Person or department responsible',
        created_by INT COMMENT 'User ID who created this initiative',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        
        FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
        FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
        
        INDEX idx_company_status (company_id, status),
        INDEX idx_dates (start_date, target_completion_date)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Emission reduction initiatives and action plans';
    """
    
    # Table 3: Initiative Progress Updates (Optional - for future use)
    create_progress_table = """
    CREATE TABLE IF NOT EXISTS initiative_progress (
        id INT AUTO_INCREMENT PRIMARY KEY,
        initiative_id INT NOT NULL,
        progress_date DATE NOT NULL,
        progress_percentage INT COMMENT 'Completion percentage (0-100)',
        notes TEXT COMMENT 'Progress update notes',
        actual_reduction_to_date DECIMAL(15,2) COMMENT 'Cumulative reduction achieved',
        cost_to_date DECIMAL(15,2) COMMENT 'Cumulative cost incurred',
        created_by INT COMMENT 'User ID who logged this update',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        FOREIGN KEY (initiative_id) REFERENCES reduction_initiatives(id) ON DELETE CASCADE,
        FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
        
        INDEX idx_initiative_date (initiative_id, progress_date)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Progress tracking for reduction initiatives';
    """
    
    # Table 4: Initiative Documents (Optional - for future use)
    create_documents_table = """
    CREATE TABLE IF NOT EXISTS initiative_documents (
        id INT AUTO_INCREMENT PRIMARY KEY,
        initiative_id INT NOT NULL,
        document_name VARCHAR(255) NOT NULL,
        document_type VARCHAR(50) COMMENT 'e.g., Invoice, Certificate, Report',
        file_path VARCHAR(500) COMMENT 'Path to stored file',
        file_url VARCHAR(500) COMMENT 'URL if stored externally',
        description TEXT,
        uploaded_by INT,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        FOREIGN KEY (initiative_id) REFERENCES reduction_initiatives(id) ON DELETE CASCADE,
        FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE SET NULL,
        
        INDEX idx_initiative (initiative_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Supporting documents for initiatives';
    """
    
    try:
        # Create tables
        print("  📋 Creating reduction_goals table...")
        if db.execute_query(create_goals_table):
            print("     ✅ reduction_goals table created successfully")
        else:
            print("     ⚠️  reduction_goals table already exists or failed to create")
        
        print("  💡 Creating reduction_initiatives table...")
        if db.execute_query(create_initiatives_table):
            print("     ✅ reduction_initiatives table created successfully")
        else:
            print("     ⚠️  reduction_initiatives table already exists or failed to create")
        
        print("  📈 Creating initiative_progress table...")
        if db.execute_query(create_progress_table):
            print("     ✅ initiative_progress table created successfully")
        else:
            print("     ⚠️  initiative_progress table already exists or failed to create")
        
        print("  📎 Creating initiative_documents table...")
        if db.execute_query(create_documents_table):
            print("     ✅ initiative_documents table created successfully")
        else:
            print("     ⚠️  initiative_documents table already exists or failed to create")
        
        print("\n✅ All tables created successfully!")
        print("\n📊 Next steps:")
        print("   1. Go to your Streamlit app")
        print("   2. Navigate to the '🎯 Reduction Tracker' page")
        print("   3. Start setting goals and creating initiatives!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error creating tables: {str(e)}")
        return False
    
    finally:
        db.disconnect()


def drop_reduction_tables():
    """
    Drop all reduction tracker tables (use with caution!)
    """
    db = get_database()
    
    if not db.connect():
        print("❌ Failed to connect to database")
        return False
    
    print("\n⚠️  WARNING: This will delete all reduction tracker data!")
    confirmation = input("Type 'DELETE' to confirm: ")
    
    if confirmation != 'DELETE':
        print("❌ Cancelled")
        return False
    
    try:
        print("🗑️  Dropping tables...")
        
        # Drop in reverse order due to foreign keys
        db.execute_query("DROP TABLE IF EXISTS initiative_documents")
        print("  ✅ Dropped initiative_documents")
        
        db.execute_query("DROP TABLE IF EXISTS initiative_progress")
        print("  ✅ Dropped initiative_progress")
        
        db.execute_query("DROP TABLE IF EXISTS reduction_initiatives")
        print("  ✅ Dropped reduction_initiatives")
        
        db.execute_query("DROP TABLE IF EXISTS reduction_goals")
        print("  ✅ Dropped reduction_goals")
        
        print("\n✅ All tables dropped successfully")
        return True
        
    except Exception as e:
        print(f"\n❌ Error dropping tables: {str(e)}")
        return False
    
    finally:
        db.disconnect()


def check_tables_exist():
    """
    Check if reduction tracker tables exist
    """
    db = get_database()
    
    if not db.connect():
        print("❌ Failed to connect to database")
        return False
    
    try:
        tables = ['reduction_goals', 'reduction_initiatives', 'initiative_progress', 'initiative_documents']
        
        print("🔍 Checking for reduction tracker tables...\n")
        
        for table in tables:
            query = f"SHOW TABLES LIKE '{table}'"
            result = db.fetch_one(query)
            
            if result:
                # Get row count
                count_query = f"SELECT COUNT(*) as count FROM {table}"
                count_result = db.fetch_one(count_query)
                count = count_result['count'] if count_result else 0
                
                print(f"  ✅ {table} - EXISTS ({count} rows)")
            else:
                print(f"  ❌ {table} - NOT FOUND")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error checking tables: {str(e)}")
        return False
    
    finally:
        db.disconnect()


if __name__ == "__main__":
    print("=" * 60)
    print("  GHG Calculator - Reduction Tracker Database Setup")
    print("=" * 60)
    print("\nOptions:")
    print("  1. Create tables")
    print("  2. Check if tables exist")
    print("  3. Drop all tables (DANGER!)")
    print("  4. Exit")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == "1":
        create_reduction_tables()
    elif choice == "2":
        check_tables_exist()
    elif choice == "3":
        drop_reduction_tables()
    elif choice == "4":
        print("👋 Goodbye!")
    else:
        print("❌ Invalid choice")