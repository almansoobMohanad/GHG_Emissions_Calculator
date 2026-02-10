"""Test database connection with the current configuration."""

import sys
import os
import socket
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error

load_dotenv()

def get_config():
    """Load database configuration from environment variables."""
    return {
        'host': os.getenv('DB_HOST'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'database': os.getenv('DB_NAME'),
        'port': int(os.getenv('DB_PORT', 3306))
    }

def test_dns_resolution(host):
    """Test if the host can be resolved."""
    print(f"\n📍 Testing DNS resolution for: {host}")
    try:
        ip = socket.gethostbyname(host)
        print(f"   ✅ DNS resolved: {host} -> {ip}")
        return True
    except socket.gaierror as e:
        print(f"   ❌ DNS resolution failed: {e}")
        return False

def test_network_connectivity(host, port):
    """Test if the host is reachable on the port."""
    print(f"\n🌐 Testing network connectivity to {host}:{port}")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"   ✅ Port {port} is reachable")
            return True
        else:
            print(f"   ❌ Port {port} is not reachable (error code: {result})")
            return False
    except Exception as e:
        print(f"   ❌ Network test failed: {e}")
        return False

def test_database_connection(config):
    """Test the actual database connection."""
    print(f"\n🗄️  Testing MySQL connection")
    print(f"   Host: {config['host']}")
    print(f"   User: {config['user']}")
    print(f"   Database: {config['database']}")
    print(f"   Port: {config['port']}")
    
    try:
        conn = mysql.connector.connect(**config)
        print(f"   ✅ MySQL connection successful!")
        
        # Test the connection with a query
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        print(f"   📊 MySQL Version: {version[0]}")
        
        cursor.execute("SELECT DATABASE()")
        db = cursor.fetchone()
        print(f"   📁 Current Database: {db[0]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Error as e:
        print(f"   ❌ MySQL connection failed")
        print(f"   Error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False

def main():
    """Run all connection tests."""
    print("=" * 60)
    print("DATABASE CONNECTION TEST")
    print("=" * 60)
    
    config = get_config()
    
    # Validate config
    if not all(config.values()):
        print("\n❌ Missing database configuration in .env file")
        print(f"   Config: {config}")
        return False
    
    # Run tests
    dns_ok = test_dns_resolution(config['host'])
    network_ok = test_network_connectivity(config['host'], config['port'])
    db_ok = test_database_connection(config)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"DNS Resolution: {'✅ PASS' if dns_ok else '❌ FAIL'}")
    print(f"Network Connectivity: {'✅ PASS' if network_ok else '❌ FAIL'}")
    print(f"Database Connection: {'✅ PASS' if db_ok else '❌ FAIL'}")
    print("=" * 60)
    
    if dns_ok and network_ok and db_ok:
        print("\n🎉 All tests passed! Your database connection is working.")
        return True
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
