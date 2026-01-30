#!/usr/bin/env python3
"""
Complete demo application for the Address Intelligence pipeline.
This demonstrates both landmark extraction and geocoding working together.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.pipelines.landmark_extraction_pipeline import LandmarkExtractor
from src.pipelines.geocoding_pipeline import GeocodingPipeline

def run_full_pipeline_demo():
    """Run the complete pipeline from address to GPS coordinates."""
    
    print("🚀 Address Intelligence Pipeline Demo")
    print("="*60)
    
    # Example addresses to test
    test_addresses = [
        "101/102, Ebrahim Manzil , Bazar gali, near Fish Market, Versova, Andheri West, Mumbai - 400061",
        "sai prasad,mahesh 202 ,gaulwada,vasai west,suruchi road",
        "Near Hanuman Mandir, after chai tapri, opposite Nagar Parishad office, lane behind big tree",
        "opp police station, nr temple, behind reliance mart"
    ]
    
    extractor = LandmarkExtractor()
    geocoder = GeocodingPipeline()
    
    for i, address in enumerate(test_addresses, 1):
        print(f"\n📋 Address {i}: {address}")
        print("-" * 60)
        
        # Step 1: Extract landmarks
        print("🔍 Extracting landmarks...")
        landmark_result = extractor.extract_with_spacy_matcher(address)
        
        print(f"✅ Found {landmark_result['total_landmarks']} landmarks:")
        for j, landmark in enumerate(landmark_result['landmarks'], 1):
            print(f"   {j}. [{landmark['type']}] {landmark['relation']} {landmark['landmark']} (weight: {landmark['weight']})")
        
        # Step 2: Prepare context for geocoding
        print("\n📍 Preparing context for geocoding...")
        
        # Extract pincode from address if available
        import re
        pincode_match = re.search(r'\b(\d{6})\b', address)
        pincode = pincode_match.group(1) if pincode_match else ""
        
        # Extract city from address
        city = "Mumbai" if "mumbai" in address.lower() or "mumbra" in address.lower() else ""
        if not city:
            city_match = re.search(r',\s*([A-Za-z\s]+)(?:\s*-\s*\d{6}|$)', address)
            if city_match:
                city = city_match.group(1).strip()
        
        # Extract locality tokens (like Versova, Andheri West) from the address
        # We'll look for capitalized words that appear to be localities
        words = address.split(',')
        locality_tokens = []
        for word in words:
            word = word.strip()
            # Look for capitalized words that aren't common terms
            potential_tokens = word.split()
            for token in potential_tokens:
                token = token.strip().strip('-')
                if token and len(token) > 3 and token[0].isupper() and \
                   token.lower() not in ['near', 'behind', 'opposite', 'after', 'before', 'mumbai', 'mumbra']:
                    if token not in locality_tokens:
                        locality_tokens.append(token)
        
        # Prepare context
        context = {
            "building": "",
            "house": "",
            "locality": "",
            "city": city,
            "state": "",
            "pincode": pincode,
            "landmarks": landmark_result['landmarks'],
            "raw_text": address,
            "locality_tokens": locality_tokens
        }
        
        print(f"📋 Context prepared:")
        print(f"   - City: {context['city']}")
        print(f"   - Pincode: {context['pincode']}")
        print(f"   - Locality tokens: {context['locality_tokens']}")
        print(f"   - Total landmarks: {len(context['landmarks'])}")
        
        # Step 3: Geocode the address
        print("\n🗺️  Geocoding address...")
        result = geocoder.geocode_address(context)
        
        if result:
            print("✅ Geocoding successful!")
            print(f"   📍 Latitude: {result['latitude']}")
            print(f"   📍 Longitude: {result['longitude']}")
            print(f"   🏠 Address: {result['formatted_address']}")
            print(f"   💯 Confidence: {result['confidence']}")
            print(f"   🔍 Used query: {result['used_query']}")
            print(f"   📮 Pincode in result: {result['address_components'].get('postcode', 'Not found')}")
            
            if result['alternatives']:
                print(f"   🔄 Top alternative:")
                for k, alt in enumerate(result['alternatives'][:1], 1):  # Show top 1
                    print(f"      {k}. {alt['display_name']} (score: {round(alt['final_score'], 3)})")
        else:
            print("❌ Geocoding failed - no results found")
        
        print("\n" + "="*60)


def test_specific_problematic_case():
    """Test the specific case that was failing."""
    
    print("\n🔧 Testing Specific Problem Case")
    print("="*60)
    
    address = "101/102, Ebrahim Manzil , Bazar gali, near Fish Market, Versova, Andheri West, Mumbai - 400061"
    
    print(f"Input Address: {address}")
    
    extractor = LandmarkExtractor()
    geocoder = GeocodingPipeline()
    
    # Extract landmarks
    landmark_result = extractor.extract_with_spacy_matcher(address)
    print(f"Extracted Landmarks: {landmark_result['landmarks']}")
    
    # Create context with specific information for this case
    context = {
        "building": "Ebrahim Manzil",
        "house": "101/102",
        "locality": "Bazar gali",
        "city": "Mumbai",
        "state": "Maharashtra",
        "pincode": "400061",  # Correct pincode for Versova/Andheri West
        "landmarks": [
            {"relation": "near", "landmark": "Fish Market", "type": "SHOP", "weight": 0.7},
            {"relation": "at", "landmark": "Versova", "type": "LOCALITY", "weight": 0.8},
            {"relation": "at", "landmark": "Andheri West", "type": "LOCALITY", "weight": 0.8}
        ],
        "raw_text": address,
        "locality_tokens": ["Versova", "Andheri West"]
    }
    
    print(f"Custom Context: {context}")
    
    # Geocode
    result = geocoder.geocode_address(context)
    
    if result:
        print(f"\n✅ SUCCESS! Result:")
        print(f"   Address: {result['formatted_address']}")
        print(f"   Confidence: {result['confidence']}")
        print(f"   Pincode: {result['address_components'].get('postcode', 'N/A')}")
        
        # Check if result contains expected localities
        formatted_addr_lower = result['formatted_address'].lower()
        has_versova = 'versova' in formatted_addr_lower
        has_andheri_west = 'andheri west' in formatted_addr_lower
        
        print(f"   Contains 'Versova': {has_versova}")
        print(f"   Contains 'Andheri West': {has_andheri_west}")
        
        if has_versova or has_andheri_west:
            print("   🎉 CORRECT: Address properly located in Versova/Andheri West area!")
        else:
            print("   ⚠️  RESULT MAY BE INCORRECT: Doesn't contain expected locality")
    else:
        print("❌ FAILED: No geocoding result found")


if __name__ == "__main__":
    run_full_pipeline_demo()
    test_specific_problematic_case()