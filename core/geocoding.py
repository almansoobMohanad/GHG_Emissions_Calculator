"""
Geocoding utilities for converting addresses to coordinates.
Uses geopy library with multiple providers for reliability.
"""
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Lazy import to avoid breaking app if geopy not installed
_geocoder = None


def _get_geocoder():
    """Get or initialize geocoder instance (lazy loading)."""
    global _geocoder
    if _geocoder is None:
        try:
            from geopy.geocoders import Nominatim, ArcGIS
            from geopy.exc import GeocoderTimedOut, GeocoderServiceError
            
            # Try ArcGIS first (more reliable, higher limits)
            try:
                _geocoder = ArcGIS(timeout=10)
                logger.info("✅ Geocoder (ArcGIS) initialized successfully")
            except Exception as e:
                logger.warning(f"⚠️ ArcGIS failed: {e}. Falling back to Nominatim.")
                # Fallback to Nominatim (OpenStreetMap)
                _geocoder = Nominatim(
                    user_agent="sustainability_monitoring_hub_v2",
                    timeout=10
                )
                logger.info("✅ Geocoder (Nominatim) initialized successfully")

        except ImportError:
            logger.error("❌ geopy not installed. Run: pip install geopy")
            _geocoder = False
        except Exception as e:
            logger.error(f"❌ Failed to initialize geocoder: {e}")
            _geocoder = False
    
    return _geocoder if _geocoder is not False else None


def geocode_address(address: str) -> Tuple[Optional[float], Optional[float], str]:
    """Convert an address string to latitude and longitude coordinates.
    
    Args:
        address: Full address string to geocode.
    
    Returns:
        tuple: (latitude, longitude, status_message)
            - latitude: float or None if geocoding failed
            - longitude: float or None if geocoding failed
            - status_message: str describing the result
    
    Examples:
        >>> lat, lng, msg = geocode_address("1600 Amphitheatre Parkway, Mountain View, CA")
        >>> print(f"Coordinates: {lat}, {lng}")
        Coordinates: 37.4224764, -122.0842499
    """
    if not address or not address.strip():
        return None, None, "No address provided"
    
    geocoder = _get_geocoder()
    if geocoder is None:
        logger.warning("Geocoder not available - coordinates will not be set")
        return None, None, "Geocoding service unavailable (geopy not installed)"
    
    try:
        from geopy.exc import GeocoderTimedOut, GeocoderServiceError
        
        logger.info(f"Geocoding address: {address[:100]}...")
        location = geocoder.geocode(address)
        
        if location:
            latitude = round(location.latitude, 8)
            longitude = round(location.longitude, 8)
            logger.info(f"✅ Geocoded successfully: {latitude}, {longitude}")
            return latitude, longitude, f"Location geocoded successfully"
        else:
            logger.warning(f"⚠️ No results found for address: {address[:100]}")
            return None, None, "Address could not be geocoded - please check the address"
    
    except GeocoderTimedOut:
        logger.error("❌ Geocoding request timed out")
        return None, None, "Geocoding service timed out - coordinates not set"
    
    except GeocoderServiceError as e:
        logger.error(f"❌ Geocoding service error: {e}")
        return None, None, "Geocoding service temporarily unavailable"
    
    except Exception as e:
        logger.error(f"❌ Unexpected geocoding error: {e}")
        return None, None, f"Geocoding failed: {str(e)}"


def geocode_address_silent(address: str) -> Tuple[Optional[float], Optional[float]]:
    """Geocode address without logging (for batch operations).
    
    Args:
        address: Address string to geocode.
    
    Returns:
        tuple: (latitude, longitude) or (None, None) if failed
    """
    lat, lng, _ = geocode_address(address)
    return lat, lng


def validate_coordinates(latitude: float, longitude: float) -> bool:
    """Validate that latitude and longitude are within valid ranges.
    
    Args:
        latitude: Latitude value to check (-90 to 90).
        longitude: Longitude value to check (-180 to 180).
    
    Returns:
        bool: True if coordinates are valid, False otherwise.
    """
    try:
        lat = float(latitude)
        lng = float(longitude)
        
        if not (-90 <= lat <= 90):
            return False
            if not (-180 <= lng <= 180):
                return False
        
        return True
    except (TypeError, ValueError):
        return False


def format_coordinates(latitude: Optional[float], longitude: Optional[float]) -> str:
    """Format coordinates for display.
    
    Args:
        latitude: Latitude value.
        longitude: Longitude value.
    
    Returns:
        str: Formatted coordinate string or "Not available".
    
    Examples:
        >>> format_coordinates(37.4224764, -122.0842499)
        '37.4225°N, 122.0842°W'
    """
    if latitude is None or longitude is None:
        return "Not available"
    
    try:
        lat_dir = "N" if latitude >= 0 else "S"
        lng_dir = "E" if longitude >= 0 else "W"
        
        return f"{abs(latitude):.4f}°{lat_dir}, {abs(longitude):.4f}°{lng_dir}"
    except:
        return "Invalid coordinates"


def get_google_maps_link(latitude: Optional[float], longitude: Optional[float]) -> Optional[str]:
    """Generate a Google Maps link from coordinates.
    
    Args:
        latitude: Latitude value.
        longitude: Longitude value.
    
    Returns:
        str: Google Maps URL or None if coordinates invalid.
    """
    if latitude is None or longitude is None:
        return None
    
    if not validate_coordinates(latitude, longitude):
        return None
    
    return f"https://www.google.com/maps?q={latitude},{longitude}"


# Convenience function for checking if geocoding is available
def is_geocoding_available() -> bool:
    """Check if geocoding service is available.
    
    Returns:
        bool: True if geocoding can be performed.
    """
    return _get_geocoder() is not None
