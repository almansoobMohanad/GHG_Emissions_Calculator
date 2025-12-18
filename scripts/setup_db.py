"""
Database Setup Script
Creates all tables for GHG Calculator
Run this ONCE to initialize your database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import mysql.connector
from mysql.connector import Error
from config.settings import config

class DatabaseSetup:
    def __init__(self):
        self.connection = None
        self.db_config = config.database_config.copy()
        # Remove database from config for initial connection
        self.db_name = self.db_config.pop('database')
    
    def connect(self):
        """Connect to MySQL server (without database)"""
        try:
            self.connection = mysql.connector.connect(**self.db_config)
            print("✅ Connected to MySQL server")
            return True
        except Error as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("✅ Disconnected from MySQL server")
    
    def execute_query(self, query, params=None):
        """Execute a query"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"❌ Query failed: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def create_database(self):
        """Create database if not exists"""
        print(f"\n📁 Creating database: {self.db_name}")
        query = f"CREATE DATABASE IF NOT EXISTS {self.db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        if self.execute_query(query):
            print(f"✅ Database '{self.db_name}' ready")
            # Switch to the database
            self.execute_query(f"USE {self.db_name}")
            return True
        return False
    
    def create_tables(self):
        """Create all tables"""
        print("\n📋 Creating tables...")
        
        tables = {
            'users': """
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    role ENUM('admin', 'manager', 'normal_user') DEFAULT 'normal_user',
                    company_id INT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    last_login DATETIME NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_users_company (company_id),
                    INDEX idx_users_email (email)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,
            
            'companies': """
                CREATE TABLE IF NOT EXISTS companies (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    company_name VARCHAR(255) UNIQUE NOT NULL,
                    company_code VARCHAR(50) UNIQUE NOT NULL,
                    industry_sector VARCHAR(100) NULL,
                    address TEXT NULL,
                    contact_email VARCHAR(255) NULL,
                    contact_phone VARCHAR(50) NULL,
                    verification_status ENUM('pending', 'verified', 'rejected') DEFAULT 'pending',
                    verification_date DATETIME NULL,
                    verified_by INT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_companies_status (verification_status),
                    INDEX idx_companies_code (company_code)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,
            
            'ghg_scopes': """
                CREATE TABLE IF NOT EXISTS ghg_scopes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    scope_number INT UNIQUE NOT NULL,
                    scope_name VARCHAR(100) NOT NULL,
                    description TEXT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,
            
            'ghg_categories': """
                CREATE TABLE IF NOT EXISTS ghg_categories (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    scope_id INT NOT NULL,
                    category_code VARCHAR(50) UNIQUE NOT NULL,
                    category_name VARCHAR(200) NOT NULL,
                    description TEXT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (scope_id) REFERENCES ghg_scopes(id) ON DELETE RESTRICT,
                    INDEX idx_categories_scope (scope_id),
                    INDEX idx_categories_code (category_code)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,
            
            'ghg_emission_sources': """
                CREATE TABLE IF NOT EXISTS ghg_emission_sources (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    category_id INT NOT NULL,
                    source_code VARCHAR(50) UNIQUE NOT NULL,
                    source_name VARCHAR(200) NOT NULL,
                    emission_factor DECIMAL(15,8) NOT NULL,
                    unit VARCHAR(50) NOT NULL,
                    description TEXT NULL,
                    region VARCHAR(50) DEFAULT 'UK',
                    source_reference VARCHAR(255) NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (category_id) REFERENCES ghg_categories(id) ON DELETE RESTRICT,
                    INDEX idx_sources_category (category_id),
                    INDEX idx_sources_code (source_code),
                    INDEX idx_sources_active (is_active)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,
            
            'emissions_data': """
                CREATE TABLE IF NOT EXISTS emissions_data (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    company_id INT NOT NULL,
                    user_id INT NOT NULL,
                    emission_source_id INT NOT NULL,
                    reporting_period VARCHAR(20) NOT NULL,
                    activity_data DECIMAL(15,4) NOT NULL,
                    emission_factor DECIMAL(15,8) NOT NULL,
                    co2_equivalent DECIMAL(15,4) NOT NULL,
                    data_source VARCHAR(255) NULL,
                    calculation_method VARCHAR(100) NULL,
                    verification_status ENUM('unverified', 'verified', 'rejected') DEFAULT 'unverified',
                    verified_by INT NULL,
                    verified_at DATETIME NULL,
                    notes TEXT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT,
                    FOREIGN KEY (emission_source_id) REFERENCES ghg_emission_sources(id) ON DELETE RESTRICT,
                    FOREIGN KEY (verified_by) REFERENCES users(id) ON DELETE SET NULL,
                    INDEX idx_emissions_company (company_id),
                    INDEX idx_emissions_period (reporting_period),
                    INDEX idx_emissions_source (emission_source_id),
                    INDEX idx_emissions_status (verification_status)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,
            
            'cosiri_documents': """
                CREATE TABLE IF NOT EXISTS cosiri_documents (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    company_id INT NOT NULL,
                    uploaded_by INT NOT NULL,
                    document_type ENUM('report', 'certificate') NOT NULL,
                    file_name VARCHAR(255) NOT NULL,
                    file_path VARCHAR(500) NOT NULL,
                    file_size INT NULL,
                    mime_type VARCHAR(100) NULL,
                    reporting_period VARCHAR(20) NULL,
                    notes TEXT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
                    FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE RESTRICT,
                    INDEX idx_cosiri_company (company_id),
                    INDEX idx_cosiri_type (document_type),
                    INDEX idx_cosiri_active (is_active)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
        }
        
        # Create tables in order
        for table_name, table_query in tables.items():
            print(f"  Creating table: {table_name}...", end=" ")
            if self.execute_query(table_query):
                print("✅")
            else:
                print("❌")
                return False
        
        # Add foreign key for users.company_id (after companies table exists)
        print("  Adding foreign key constraints...", end=" ")
        
        # Check if constraint already exists
        check_fk_query = """
            SELECT COUNT(*) as cnt FROM information_schema.TABLE_CONSTRAINTS 
            WHERE CONSTRAINT_SCHEMA = %s 
            AND TABLE_NAME = 'users' 
            AND CONSTRAINT_NAME = 'fk_users_company'
        """
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(check_fk_query, (self.db_name,))
        result = cursor.fetchone()
        cursor.close()
        
        if result['cnt'] == 0:
            # Constraint doesn't exist, add it
            fk_query = """
                ALTER TABLE users 
                ADD CONSTRAINT fk_users_company 
                FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE SET NULL
            """
            if self.execute_query(fk_query):
                print("✅")
            else:
                print("❌")
                return False
        else:
            print("⏭️  (already exists)")
        
        return True
    
    def seed_initial_data(self):
        """Insert initial reference data"""
        print("\n🌱 Seeding initial data...")
        
        # Insert GHG Scopes
        print("  Inserting GHG scopes...", end=" ")
        scopes_query = """
            INSERT IGNORE INTO ghg_scopes (scope_number, scope_name, description) VALUES
            (1, 'Scope 1: Direct Emissions', 'Direct GHG emissions from sources owned or controlled by the company'),
            (2, 'Scope 2: Indirect Emissions (Energy)', 'Indirect GHG emissions from purchased electricity, heat, or steam'),
            (3, 'Scope 3: Other Indirect Emissions', 'All other indirect emissions in the value chain')
        """
        if self.execute_query(scopes_query):
            print("✅")
        else:
            print("❌")
            return False
        
        # Insert sample categories for each scope
        print("  Inserting GHG categories...", end=" ")
        categories_query = """
            INSERT IGNORE INTO ghg_categories (scope_id, category_code, category_name, description) VALUES
            -- Scope 1 categories
            (1, 'S1-01', 'Stationary Combustion', 'Emissions from stationary fuel combustion sources'),
            (1, 'S1-02', 'Mobile Combustion', 'Emissions from mobile fuel combustion sources'),
            (1, 'S1-03', 'Process Emissions', 'Emissions from industrial processes'),
            (1, 'S1-04', 'Fugitive Emissions', 'Intentional and unintentional releases'),
            -- Scope 2 categories
            (2, 'S2-01', 'Purchased Electricity', 'Electricity purchased from the grid'),
            (2, 'S2-02', 'Purchased Heat/Steam/Cooling', 'Purchased thermal energy'),
            -- Scope 3 categories (examples)
            (3, 'S3-01', 'Purchased Goods and Services', 'Upstream emissions from purchased goods'),
            (3, 'S3-06', 'Business Travel', 'Employee business travel'),
            (3, 'S3-07', 'Employee Commuting', 'Employee commuting to work')
        """
        if self.execute_query(categories_query):
            print("✅")
        else:
            print("❌")
            return False
        
        # Insert sample emission sources
        print("  Inserting emission sources...", end=" ")
        sources_query = """
            INSERT IGNORE INTO ghg_emission_sources 
            (category_id, source_code, source_name, emission_factor, unit, description, region) VALUES
            -- Stationary Combustion (S1-01)
            ((SELECT id FROM ghg_categories WHERE category_code = 'S1-01'), 'S1-01-01', 'Natural Gas', 0.18385000, 'kg CO2e/kWh', 'Natural gas combustion in boilers and furnaces', 'UK'),
            ((SELECT id FROM ghg_categories WHERE category_code = 'S1-01'), 'S1-01-02', 'Coal', 0.34224000, 'kg CO2e/kWh', 'Coal combustion in power generation', 'UK'),
            ((SELECT id FROM ghg_categories WHERE category_code = 'S1-01'), 'S1-01-03', 'LPG', 0.21449000, 'kg CO2e/litre', 'LPG combustion', 'UK'),
            -- Mobile Combustion (S1-02)
            ((SELECT id FROM ghg_categories WHERE category_code = 'S1-02'), 'S1-02-01', 'Petrol Cars', 0.16743000, 'kg CO2e/litre', 'Petrol vehicles', 'UK'),
            ((SELECT id FROM ghg_categories WHERE category_code = 'S1-02'), 'S1-02-02', 'Diesel Cars', 0.16901000, 'kg CO2e/litre', 'Diesel vehicles', 'UK'),
            -- Purchased Electricity (S2-01)
            ((SELECT id FROM ghg_categories WHERE category_code = 'S2-01'), 'S2-01-01', 'Grid Electricity (UK)', 0.19338000, 'kg CO2e/kWh', 'UK national grid electricity', 'UK'),
            ((SELECT id FROM ghg_categories WHERE category_code = 'S2-01'), 'S2-01-02', 'Renewable Electricity', 0.00000000, 'kg CO2e/kWh', 'Certified renewable electricity', 'UK')
        """
        if self.execute_query(sources_query):
            print("✅")
        else:
            print("❌")
            return False
        
        # Create default admin user (password: admin123)
        print("  Creating default admin user...", end=" ")
        import hashlib
        password = "admin123"
        # Simple hash - in production use bcrypt or similar
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        admin_query = """
            INSERT IGNORE INTO users (username, email, password_hash, role, is_active) VALUES
            ('admin', 'admin@ghgcalc.com', %s, 'admin', TRUE)
        """
        if self.execute_query(admin_query, (password_hash,)):
            print("✅")
            print("      Username: admin")
            print("      Password: admin123")
        else:
            print("⏭️  (already exists)")
        
        # Create sample company
        print("  Creating sample company...", end=" ")
        company_query = """
            INSERT IGNORE INTO companies 
            (company_name, company_code, industry_sector, address, contact_email, verification_status) VALUES
            ('Demo Manufacturing Ltd', 'DEMO001', 'Manufacturing', '123 Industrial Park, London, UK', 'contact@demomfg.com', 'verified')
        """
        if self.execute_query(company_query):
            print("✅")
            print("      Company: Demo Manufacturing Ltd")
            print("      Code: DEMO001")
        else:
            print("⏭️  (already exists)")
        
        # Create sample user associated with the company
        print("  Creating sample company user...", end=" ")
        sample_password_hash = hashlib.sha256("demo123".encode()).hexdigest()
        
        sample_user_query = """
            INSERT IGNORE INTO users (username, email, password_hash, role, company_id, is_active) VALUES
            ('demouser', 'user@demomfg.com', %s, 'manager', 
             (SELECT id FROM companies WHERE company_code = 'DEMO001'), TRUE)
        """
        if self.execute_query(sample_user_query, (sample_password_hash,)):
            print("✅")
            print("      Username: demouser")
            print("      Password: demo123")
            print("      Role: manager")
        else:
            print("⏭️  (already exists)")
        
        return True
    
    def run_setup(self):
        """Run complete database setup"""
        print("=" * 60)
        print("🚀 GHG Calculator - Database Setup")
        print("=" * 60)
        print(f"Database: {self.db_name}")
        print(f"Host: {self.db_config['host']}")
        print("=" * 60)
        
        if not self.connect():
            return False
        
        try:
            # Create database
            if not self.create_database():
                return False
            
            # Create tables
            if not self.create_tables():
                return False
            
            # Seed initial data
            if not self.seed_initial_data():
                return False
            
            print("\n" + "=" * 60)
            print("🎉 Database setup completed successfully!")
            print("=" * 60)
            print("\n📝 Next steps:")
            print("  1. Run: streamlit run app/main.py")
            print("  2. Login with: admin / admin123")
            print("  3. Change admin password immediately!")
            print("\n")
            
            return True
            
        finally:
            self.disconnect()

def main():
    """Main function"""
    setup = DatabaseSetup()
    success = setup.run_setup()
    
    if success:
        print("✅ Setup completed successfully")
        return 0
    else:
        print("❌ Setup failed")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())