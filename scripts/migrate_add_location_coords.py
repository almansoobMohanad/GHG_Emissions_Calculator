"""
Database migration: Add latitude and longitude to companies table
This allows for geolocation mapping of company locations.
"""
import sys
from pathlib import Path

# Add parent directory to path so we can import from core
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.database import DatabaseManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    """Add latitude and longitude columns to companies table."""
    db = DatabaseManager()
    
    if not db.connect():
        logger.error("❌ Failed to connect to database")
        return False
    
    try:
        # Add latitude and longitude columns
        alter_queries = [
            """
            ALTER TABLE companies 
            ADD COLUMN latitude DECIMAL(10, 8) NULL 
            COMMENT 'Latitude coordinate for company location'
            AFTER address
            """,
            """
            ALTER TABLE companies 
            ADD COLUMN longitude DECIMAL(11, 8) NULL 
            COMMENT 'Longitude coordinate for company location'
            AFTER latitude
            """
        ]
        
        for query in alter_queries:
            logger.info(f"Executing: {query.strip()[:100]}...")
            success = db.execute_query(query)
            if not success:
                logger.error(f"❌ Failed to execute query")
                return False
        
        logger.info("✅ Successfully added latitude and longitude columns to companies table")
        
        # Create index for geospatial queries (optional but recommended)
        index_query = """
        CREATE INDEX idx_companies_location ON companies(latitude, longitude)
        """
        logger.info("Creating geospatial index...")
        db.execute_query(index_query)
        logger.info("✅ Geospatial index created")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False
    
    finally:
        db.disconnect()


if __name__ == "__main__":
    print("=" * 80)
    print("COMPANY LOCATION COORDINATES MIGRATION")
    print("=" * 80)
    print("\nThis will add latitude and longitude fields to the companies table.")
    print("\nChanges:")
    print("  ✓ Add 'latitude' column (DECIMAL(10,8))")
    print("  ✓ Add 'longitude' column (DECIMAL(11,8))")
    print("  ✓ Create geospatial index for location queries")
    print("\n" + "=" * 80)
    
    response = input("\nProceed with migration? (yes/no): ").strip().lower()
    
    if response == 'yes':
        print("\n🚀 Starting migration...\n")
        success = migrate()
        
        if success:
            print("\n" + "=" * 80)
            print("✅ MIGRATION COMPLETED SUCCESSFULLY")
            print("=" * 80)
            print("\nNext steps:")
            print("  1. Install geocoding package: pip install geopy")
            print("  2. Geocoding will be automatically applied during company registration")
            print("  3. Existing companies can be geocoded via admin panel (future feature)")
        else:
            print("\n" + "=" * 80)
            print("❌ MIGRATION FAILED")
            print("=" * 80)
            print("\nPlease check the error messages above and try again.")
    else:
        print("\n❌ Migration cancelled.")
