"""
Setup Test Users Script
Creates test users for each role (admin, manager, normal_user)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import hashlib
import mysql.connector
from mysql.connector import Error
from config.settings import config


def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


def create_test_users():
    """Create test company and users"""
    print("=" * 60)
    print("🧪 GHG Calculator - Test Users Setup")
    print("=" * 60)
    
    try:
        # Connect to database
        conn = mysql.connector.connect(**config.database_config)
        cursor = conn.cursor()
        print("✅ Connected to database\n")
        
        # Create test company
        print("📋 Creating test company...")
        company_query = """
            INSERT INTO companies 
            (company_name, company_code, industry_sector, address, contact_email, verification_status)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE id=LAST_INSERT_ID(id)
        """
        cursor.execute(company_query, (
            'Test Company Ltd',
            'TEST001',
            'Technology',
            '456 Test Street, London, UK',
            'contact@testcompany.com',
            'verified'
        ))
        company_id = cursor.lastrowid
        conn.commit()
        print(f"✅ Test Company created (ID: {company_id})\n")
        
        # Create test users
        test_users = [
            {
                'username': 'testadmin',
                'email': 'testadmin@test.com',
                'password': 'admin123',
                'role': 'admin'
            },
            {
                'username': 'testmanager',
                'email': 'testmanager@test.com',
                'password': 'manager123',
                'role': 'manager'
            },
            {
                'username': 'testuser',
                'email': 'testuser@test.com',
                'password': 'user123',
                'role': 'normal_user'
            }
        ]
        
        print("👥 Creating test users...")
        user_query = """
            INSERT INTO users (username, email, password_hash, role, company_id, is_active)
            VALUES (%s, %s, %s, %s, %s, TRUE)
            ON DUPLICATE KEY UPDATE 
                password_hash=VALUES(password_hash),
                role=VALUES(role),
                company_id=VALUES(company_id)
        """
        
        for user in test_users:
            password_hash = hash_password(user['password'])
            cursor.execute(user_query, (
                user['username'],
                user['email'],
                password_hash,
                user['role'],
                company_id
            ))
            print(f"  ✅ {user['role']:12} | {user['username']:12} | {user['password']:12}")
        
        conn.commit()
        
        print("\n" + "=" * 60)
        print("🎉 Test users created successfully!")
        print("=" * 60)
        print("\n📝 Test Credentials:")
        print("-" * 60)
        print(f"{'Role':<12} | {'Username':<15} | {'Password':<12}")
        print("-" * 60)
        for user in test_users:
            print(f"{user['role']:<12} | {user['username']:<15} | {user['password']:<12}")
        print("-" * 60)
        print(f"\n🏢 Company: Test Company Ltd (CODE: TEST001)")
        print("\n💡 All users are associated with Test Company Ltd")
        print("💡 Use these accounts to test role-based permissions\n")
        
        cursor.close()
        conn.close()
        return True
        
    except Error as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    success = create_test_users()
    sys.exit(0 if success else 1)
