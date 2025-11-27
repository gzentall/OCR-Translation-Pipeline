#!/usr/bin/env python3

"""
Geoapify API client for geocoding and location services.
Provides address search, autocomplete, and reverse geocoding functionality.
Documentation: https://www.geoapify.com/
"""

import os
import requests
from typing import Dict, List, Optional
from pathlib import Path


class GeoapifyClient:
    """Client for Geoapify Location Platform API."""
    
    def __init__(self, api_key: str = None):
        """Initialize Geoapify client with API key."""
        self.api_key = api_key or self._load_api_key()
        self.base_url = "https://api.geoapify.com/v1"
        
        if not self.api_key:
            print("Warning: No Geoapify API key found. Set GEOAPIFY_API_KEY environment variable.")
    
    def _load_api_key(self) -> Optional[str]:
        """Load API key from environment variable or .env file."""
        # Try environment variable first
        api_key = os.environ.get('GEOAPIFY_API_KEY')
        if api_key:
            return api_key
        
        # Try .env file in project root
        project_root = Path(__file__).parent.parent
        env_file = project_root / '.env'
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    if line.startswith('GEOAPIFY_API_KEY='):
                        return line.split('=', 1)[1].strip().strip('"\'')
        
        return None
    
    def geocode_address(self, address: str, country: str = None, prefer_european: bool = False) -> Optional[Dict]:
        """
        Convert an address to coordinates.
        
        Args:
            address: The address to geocode
            country: Optional country code to filter results (e.g., 'FR', 'US')
            prefer_european: If True, prefer European results for ambiguous locations
        
        Returns:
            Dict with lat, lon, formatted_address and other location data, or None if not found
        """
        try:
            if not self.api_key:
                return None
            
            params = {
                'text': address,
                'apiKey': self.api_key,
                'limit': 5 if prefer_european else 1  # Get multiple results if we need to choose European
            }
            
            if country:
                params['filter'] = f'countrycode:{country.lower()}'
            
            response = requests.get(
                f"{self.base_url}/geocode/search",
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('features') and len(data['features']) > 0:
                    features = data['features']
                    
                    # If prefer_european, try to find a European result first
                    if prefer_european and len(features) > 1:
                        european_countries = ['de', 'fr', 'cz', 'at', 'pl', 'hu', 'sk', 'it', 'ch', 'be', 'nl', 'es', 'pt', 'uk', 'gb']
                        for feature in features:
                            properties = feature.get('properties', {})
                            country_code = properties.get('country_code', '').lower()
                            if country_code in european_countries:
                                # Found a European match!
                                geometry = feature.get('geometry', {})
                                coordinates = geometry.get('coordinates', [])
                                
                                return {
                                    'lat': coordinates[1] if len(coordinates) > 1 else None,
                                    'lon': coordinates[0] if len(coordinates) > 0 else None,
                                    'formatted': properties.get('formatted', ''),
                                    'street': properties.get('street', ''),
                                    'housenumber': properties.get('housenumber', ''),
                                    'city': properties.get('city', ''),
                                    'state': properties.get('state', ''),
                                    'postcode': properties.get('postcode', ''),
                                    'country': properties.get('country', ''),
                                    'country_code': properties.get('country_code', '')
                                }
                    
                    # Fallback to first result
                    feature = features[0]
                    properties = feature.get('properties', {})
                    geometry = feature.get('geometry', {})
                    coordinates = geometry.get('coordinates', [])
                    
                    return {
                        'lat': coordinates[1] if len(coordinates) > 1 else None,
                        'lon': coordinates[0] if len(coordinates) > 0 else None,
                        'formatted': properties.get('formatted', ''),
                        'street': properties.get('street', ''),
                        'housenumber': properties.get('housenumber', ''),
                        'city': properties.get('city', ''),
                        'state': properties.get('state', ''),
                        'postcode': properties.get('postcode', ''),
                        'country': properties.get('country', ''),
                        'country_code': properties.get('country_code', '')
                    }
            
            return None
        except Exception as e:
            print(f"Error geocoding address: {e}")
            return None
    
    def autocomplete_location(self, query: str, country: str = None, limit: int = 5) -> List[Dict]:
        """
        Search for locations with autocomplete suggestions.
        
        Args:
            query: The search query
            country: Optional country code to filter results
            limit: Maximum number of results (default 5)
        
        Returns:
            List of location suggestions with lat, lon, and formatted address
        """
        try:
            if not self.api_key:
                return []
            
            params = {
                'text': query,
                'apiKey': self.api_key,
                'limit': limit
            }
            
            if country:
                params['filter'] = f'countrycode:{country.lower()}'
            
            response = requests.get(
                f"{self.base_url}/geocode/autocomplete",
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                for feature in data.get('features', []):
                    properties = feature.get('properties', {})
                    geometry = feature.get('geometry', {})
                    coordinates = geometry.get('coordinates', [])
                    
                    results.append({
                        'lat': coordinates[1] if len(coordinates) > 1 else None,
                        'lon': coordinates[0] if len(coordinates) > 0 else None,
                        'formatted': properties.get('formatted', ''),
                        'name': properties.get('name', ''),
                        'street': properties.get('street', ''),
                        'city': properties.get('city', ''),
                        'state': properties.get('state', ''),
                        'postcode': properties.get('postcode', ''),
                        'country': properties.get('country', ''),
                        'country_code': properties.get('country_code', ''),
                        'place_id': properties.get('place_id', '')
                    })
                
                return results
            
            return []
        except Exception as e:
            print(f"Error in autocomplete: {e}")
            return []
    
    def reverse_geocode(self, lat: float, lon: float) -> Optional[Dict]:
        """
        Convert coordinates to an address.
        
        Args:
            lat: Latitude
            lon: Longitude
        
        Returns:
            Dict with formatted address and location components, or None if not found
        """
        try:
            if not self.api_key:
                return None
            
            params = {
                'lat': lat,
                'lon': lon,
                'apiKey': self.api_key
            }
            
            response = requests.get(
                f"{self.base_url}/geocode/reverse",
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('features') and len(data['features']) > 0:
                    feature = data['features'][0]
                    properties = feature.get('properties', {})
                    
                    return {
                        'formatted': properties.get('formatted', ''),
                        'street': properties.get('street', ''),
                        'housenumber': properties.get('housenumber', ''),
                        'city': properties.get('city', ''),
                        'state': properties.get('state', ''),
                        'postcode': properties.get('postcode', ''),
                        'country': properties.get('country', ''),
                        'country_code': properties.get('country_code', '')
                    }
            
            return None
        except Exception as e:
            print(f"Error in reverse geocode: {e}")
            return None


def main():
    """Test the Geoapify client."""
    print("🧪 Testing Geoapify Client")
    print("=" * 40)
    
    client = GeoapifyClient()
    
    if not client.api_key:
        print("❌ No API key found. Please set GEOAPIFY_API_KEY environment variable.")
        return
    
    # Test geocoding
    print("\n1. Testing geocode_address():")
    result = client.geocode_address("Paris, France")
    if result:
        print(f"✅ Found: {result['formatted']}")
        print(f"   Coordinates: {result['lat']}, {result['lon']}")
    else:
        print("❌ No results found")
    
    # Test autocomplete
    print("\n2. Testing autocomplete_location():")
    results = client.autocomplete_location("Lond", limit=3)
    print(f"✅ Found {len(results)} suggestions:")
    for r in results[:3]:
        print(f"   - {r['formatted']}")
    
    # Test reverse geocode
    print("\n3. Testing reverse_geocode():")
    result = client.reverse_geocode(48.8566, 2.3522)  # Paris coordinates
    if result:
        print(f"✅ Found: {result['formatted']}")
    else:
        print("❌ No results found")


if __name__ == "__main__":
    main()





