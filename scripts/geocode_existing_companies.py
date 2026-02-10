"""
Geocode existing companies that don't have coordinates yet.
This script will find all companies with NULL latitude/longitude and geocode their addresses.
"""
import sys
from pathlib import Path

# Add parent directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.database import DatabaseManager
from core.geocoding import geocode_address_silent, is_geocoding_available
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def geocode_existing_companies(filter_all=False):
    """Geocode all companies with missing coordinates.
    
    Args:
        filter_all: If True, re-geocode ALL companies. If False, only geocode those with NULL coords.
    
    Returns:
        tuple: (success_count, failed_count, skipped_count)
    """
    if not is_geocoding_available():
        logger.error("❌ Geocoding service not available. Install geopy: pip install geopy")
        return 0, 0, 0
    
    db = DatabaseManager()
    if not db.connect():
        logger.error("❌ Failed to connect to database")
        return 0, 0, 0
    
    try:
        # Get companies that need geocoding
        if filter_all:
            query = """
            SELECT id, company_name, address 
            FROM companies 
            WHERE address IS NOT NULL
            ORDER BY company_name
            """
            logger.info("📍 Re-geocoding ALL companies with addresses...")
        else:
            query = """
            SELECT id, company_name, address 
            FROM companies 
            WHERE address IS NOT NULL AND (latitude IS NULL OR longitude IS NULL)
            ORDER BY company_name
            """
            logger.info("📍 Geocoding companies with missing coordinates...")
        
        companies = db.fetch_query(query)
        
        if not companies:
            logger.info("✅ All companies already have coordinates or no addresses available")
            return 0, 0, 0
        
        logger.info(f"\n📊 Found {len(companies)} companies to process\n")
        
        success_count = 0
        failed_count = 0
        skipped_count = 0
        
        for idx, (company_id, company_name, address) in enumerate(companies, 1):
            try:
                logger.info(f"[{idx}/{len(companies)}] Processing: {company_name}")
                logger.info(f"         Address: {address[:80]}")
                
                # Geocode address
                latitude, longitude = geocode_address_silent(address)
                
                if latitude and longitude:
                    # Update database
                    update_query = """
                    UPDATE companies 
                    SET latitude = %s, longitude = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """
                    
                    success = db.execute_query(
                        update_query,
                        (latitude, longitude, company_id)
                    )
                    
                    if success:
                        logger.info(f"         ✅ Success: {latitude}, {longitude}")
                        success_count += 1
                    else:
                        logger.error(f"         ❌ Failed to update database")
                        failed_count += 1
                
                else:
                    logger.warning(f"         ⚠️ Could not geocode address")
                    failed_count += 1
            
            except Exception as e:
                logger.error(f"         ❌ Error: {e}")
                failed_count += 1
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ GEOCODING COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Successful:  {success_count}")
        logger.info(f"Failed:      {failed_count}")
        logger.info(f"Skipped:     {skipped_count}")
        logger.info(f"Total:       {len(companies)}")
        
        return success_count, failed_count, skipped_count
    
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return 0, 0, 0
    
    finally:
        db.disconnect()


def geocode_single_company(company_id):
    """Geocode a single company by ID.
    
    Args:
        company_id: The company ID to geocode.
    
    Returns:
        bool: True if successful, False otherwise.
    """
    db = DatabaseManager()
    if not db.connect():
        logger.error("❌ Failed to connect to database")
        return False
    
    try:
        # Get company
        query = "SELECT id, company_name, address FROM companies WHERE id = %s"
        result = db.fetch_one(query, (company_id,))
        
        if not result:
            logger.error(f"❌ Company with ID {company_id} not found")
            return False
        
        company_id, company_name, address = result
        
        if not address:
            logger.error(f"❌ Company '{company_name}' has no address")
            return False
        
        logger.info(f"Geocoding: {company_name}")
        logger.info(f"Address: {address}")
        
        latitude, longitude = geocode_address_silent(address)
        
        if latitude and longitude:
            update_query = """
            UPDATE companies 
            SET latitude = %s, longitude = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """
            
            success = db.execute_query(
                update_query,
                (latitude, longitude, company_id)
            )
            
            if success:
                logger.info(f"✅ Success: {latitude}, {longitude}")
                return True
            else:
                logger.error("❌ Failed to update database")
                return False
        else:
            logger.error("❌ Could not geocode address")
            return False
    
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return False
    
    finally:
        db.disconnect()


if __name__ == "__main__":
    print("=" * 80)
    print("BULK GEOCODING FOR EXISTING COMPANIES")
    print("=" * 80)
    print("\nOptions:")
    print("  1. Geocode companies with missing coordinates (default)")
    print("  2. Re-geocode ALL companies")
    print("  3. Geocode single company by ID")
    print("  4. Exit")
    
    choice = input("\nSelect option (1-4): ").strip()
    
    if choice == "1":
        print("\n🚀 Starting geocoding process...\n")
        success, failed, skipped = geocode_existing_companies(filter_all=False)
        
    elif choice == "2":
        response = input("\n⚠️  This will re-geocode ALL companies. Continue? (yes/no): ").strip().lower()
        if response == "yes":
            print("\n🚀 Starting re-geocoding process...\n")
            success, failed, skipped = geocode_existing_companies(filter_all=True)
        else:
            print("❌ Cancelled")
    
    elif choice == "3":
        company_id = input("\nEnter company ID: ").strip()
        try:
            company_id = int(company_id)
            geocode_single_company(company_id)
        except ValueError:
            print("❌ Invalid company ID")
    
    elif choice == "4":
        print("❌ Exiting")
    
    else:
        print("❌ Invalid option")
