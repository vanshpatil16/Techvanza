#!/usr/bin/env python3
"""
Test script to verify the pincode fix for the geocoding pipeline.
This tests the specific case where "Fish Market, Versova, Andheri West, Mumbai - 400061" 
was being incorrectly geocoded to Mulund (400080) instead of Versova/Andheri West (400061).
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.pipelines.geocoding_pipeline import GeocodingPipeline
from src.pipelines.landmark_extraction_pipeline import LandmarkExtractor

def test_problematic_address():
    """Test the specific address that was causing issues."""
    print("Testing problematic address with pincode fix...")
    
    # The problematic address from the user
    address = "101/102, Ebrahim Manzil , Bazar gali, near Fish Market, Versova, Andheri West, Mumbai - 400061"
    
    # Extract landmarks first
    extractor = LandmarkExtractor()
    landmark_result = extractor.extract_with_spacy_matcher(address)
    
    print(f"Original Address: {address}")
    print(f"Extracted Landmarks: {landmark_result['landmarks']}")
    
    # Prepare context for geocoding with explicit pincode extraction
    context = {
        "building": "101/102, Ebrahim Manzil",
        "house": "101/102",
        "locality": "Bazar gali",
        "city": "Mumbai",
        "state": "Maharashtra",  # Assuming Maharashtra for Mumbai
        "pincode": "400061",  # Explicitly set the correct pincode
        "landmarks": landmark_result["landmarks"],
        "raw_text": address,
        # Add locality tokens to help with location matching
        "locality_tokens": ["Versova", "Andheri West"]
    }
    
    print(f"Context for geocoding: {context}")
    
    # Initialize and run geocoding pipeline
    pipeline = GeocodingPipeline()
    result = pipeline.geocode_address(context)
    
    if result:
        print("\n✅ Geocoding Successful!")
        print(f"Latitude: {result['latitude']}")
        print(f"Longitude: {result['longitude']}")
        print(f"Formatted Address: {result['formatted_address']}")
        print(f"Confidence: {result['confidence']}")
        print(f"Used Query: {result['used_query']}")
        print(f"Pincode in result: {result['address_components'].get('postcode', 'Not found')}")
        
        # Check if the result contains Versova/Andheri West and correct pincode
        formatted_addr = result['formatted_address'].lower()
        result_pincode = result['address_components'].get('postcode', '')
        
        has_versova = 'versova' in formatted_addr
        has_andheri_west = 'andheri west' in formatted_addr
        has_correct_pincode = result_pincode == '400061'
        
        print(f"\n🔍 Result Analysis:")
        print(f"Contains 'Versova': {has_versova}")
        print(f"Contains 'Andheri West': {has_andheri_west}")
        print(f"Has correct pincode (400061): {has_correct_pincode}")
        print(f"Result pincode: {result_pincode}")
        
        if has_correct_pincode and (has_versova or has_andheri_west):
            print("\n🎉 SUCCESS: Address correctly geocoded to Versova/Andheri West with correct pincode!")
        else:
            print("\n❌ ISSUE: Address still not correctly geocoded to Versova/Andheri West")
            
        if result['alternatives']:
            print(f"\nTop Alternatives:")
            for i, alt in enumerate(result['alternatives'], 1):
                alt_addr = alt['display_name'].lower()
                alt_pincode = alt.get('address', {}).get('postcode', 'N/A')
                has_alt_versova = 'versova' in alt_addr
                has_alt_andheri = 'andheri west' in alt_addr
                is_correct_pin = alt_pincode == '400061'
                
                print(f"  {i}. {alt['display_name']} (score: {round(alt['final_score'], 3)}, "
                      f"pincode: {alt_pincode})")
                print(f"     Contains Versova: {has_alt_versova}, Andheri West: {has_alt_andheri}, "
                      f"Correct pincode: {is_correct_pin}")
    else:
        print("\n❌ Geocoding Failed - No results found")
        print("Trying with rule-based extraction...")
        
        # Try with rule-based extraction
        landmark_result2 = extractor.extract_landmarks(address)
        context["landmarks"] = landmark_result2["landmarks"]
        
        result = pipeline.geocode_address(context)
        
        if result:
            print("\n✅ Geocoding Successful with rule-based extraction!")
            print(f"Formatted Address: {result['formatted_address']}")
            print(f"Confidence: {result['confidence']}")
            print(f"Used Query: {result['used_query']}")
            print(f"Pincode in result: {result['address_components'].get('postcode', 'Not found')}")
        else:
            print("\n❌ Geocoding still failed with rule-based extraction")


def test_scoring_verification():
    """Test the scoring function specifically to verify pincode penalties work."""
    from src.pipelines.geocoding_pipeline import CandidateRankingEngine
    
    print("\n" + "="*50)
    print("Testing Scoring Verification")
    print("="*50)
    
    # Create test candidates
    wrong_pin_candidate = {
        "display_name": "Fish Market, Mulund Colony, Mumbai 400080, India",
        "address": {"postcode": "400080", "city": "Mumbai"},
        "lat": 19.1810,
        "lon": 72.9357,
        "importance": 0.5
    }
    
    correct_pin_candidate = {
        "display_name": "Fish Market, Versova, Andheri West, Mumbai 400061, India", 
        "address": {"postcode": "400061", "city": "Mumbai", "suburb": "Versova", "city_district": "Andheri West"},
        "lat": 19.1194,
        "lon": 72.8357,
        "importance": 0.3
    }
    
    # Context with correct pincode
    context = {
        "pincode": "400061",
        "city": "Mumbai",
        "locality_tokens": ["Versova", "Andheri West"],
        "landmarks": [{"landmark": "Fish Market", "weight": 0.7}]
    }
    
    print("Testing wrong pincode candidate (should get penalty):")
    wrong_score = CandidateRankingEngine.score_candidate(wrong_pin_candidate, 0, context)
    print(f"Wrong pincode candidate score: {wrong_score}")
    
    print("\nTesting correct pincode candidate (should get boost):")
    correct_score = CandidateRankingEngine.score_candidate(correct_pin_candidate, 0, context)
    print(f"Correct pincode candidate score: {correct_score}")
    
    print(f"\nScore difference (correct - wrong): {correct_score - wrong_score}")
    
    if correct_score > wrong_score:
        print("✅ SUCCESS: Correct pincode gets higher score than wrong pincode")
    else:
        print("❌ ISSUE: Wrong pincode has higher score than correct pincode")


if __name__ == "__main__":
    print("Testing Pincode Fix for Geocoding Pipeline")
    print("="*60)
    
    test_scoring_verification()
    test_problematic_address()