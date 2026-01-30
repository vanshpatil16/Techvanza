#!/usr/bin/env python3
"""
Test script to verify the scoring improvements for pincode accuracy.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.pipelines.geocoding_pipeline import CandidateRankingEngine

def test_scoring_improvements():
    """Test that the scoring improvements work as expected."""
    
    print("Testing Scoring Improvements")
    print("="*40)
    
    # Test candidate with wrong pincode
    wrong_pin_candidate = {
        "display_name": "Fish Market, Mulund Colony, Mumbai 400080, India",
        "address": {"postcode": "400080", "city": "Mumbai", "suburb": "Mulund Colony"},
        "lat": 19.1810,
        "lon": 72.9357,
        "importance": 0.5
    }
    
    # Test candidate with correct pincode
    correct_pin_candidate = {
        "display_name": "Fish Market, Versova, Andheri West, Mumbai 400061, India", 
        "address": {"postcode": "400061", "city": "Mumbai", "suburb": "Versova", "city_district": "Andheri West"},
        "lat": 19.1194,
        "lon": 72.8357,
        "importance": 0.3
    }
    
    # Context with correct pincode and locality tokens
    context = {
        "pincode": "400061",
        "city": "Mumbai",
        "locality_tokens": ["Versova", "Andheri West"],
        "landmarks": [{"landmark": "Fish Market", "weight": 0.7}]
    }
    
    print("Testing wrong pincode candidate:")
    wrong_score = CandidateRankingEngine.score_candidate(wrong_pin_candidate, 0, context)
    print(f"Wrong pincode candidate score: {wrong_score:.3f}")
    
    print("\nTesting correct pincode candidate:")
    correct_score = CandidateRankingEngine.score_candidate(correct_pin_candidate, 0, context)
    print(f"Correct pincode candidate score: {correct_score:.3f}")
    
    print(f"\nScore difference (correct - wrong): {correct_score - wrong_score:.3f}")
    
    if correct_score > wrong_score:
        print("✅ SUCCESS: Correct pincode gets higher score than wrong pincode")
    else:
        print("❌ ISSUE: Wrong pincode has higher score than correct pincode")
    
    # Test individual scoring functions
    print("\n" + "-"*40)
    print("Testing Individual Scoring Functions")
    print("-"*40)
    
    print("Pincode score for wrong pincode:", CandidateRankingEngine.pincode_score(wrong_pin_candidate, context))
    print("Pincode score for correct pincode:", CandidateRankingEngine.pincode_score(correct_pin_candidate, context))
    
    print("Locality score for wrong candidate:", CandidateRankingEngine.locality_match_score(wrong_pin_candidate["display_name"], context))
    print("Locality score for correct candidate:", CandidateRankingEngine.locality_match_score(correct_pin_candidate["display_name"], context))
    
    print("Landmark score for wrong candidate:", CandidateRankingEngine.landmark_match_score(wrong_pin_candidate["display_name"], context["landmarks"]))
    print("Landmark score for correct candidate:", CandidateRankingEngine.landmark_match_score(correct_pin_candidate["display_name"], context["landmarks"]))


if __name__ == "__main__":
    test_scoring_improvements()