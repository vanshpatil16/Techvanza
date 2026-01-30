import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from src.pipelines.landmark_extraction_pipeline import LandmarkExtractor

class TestLandmarkExtractor:
    def setup_method(self):
        """Initialize the extractor for each test."""
        self.extractor = LandmarkExtractor()
    
    def test_preprocessing_hinglish(self):
        """Test Hinglish to English conversion."""
        test_cases = [
            ("ke paas mandir hai", "near temple hai"),
            ("opp police station", "opposite police station"),
            ("b/h big tree", "behind big tree"),
            ("nr chai tapri", "near tea stall")
        ]
        
        for input_text, expected in test_cases:
            result = self.extractor.preprocess_text(input_text)
            assert expected in result.lower()
    
    def test_relation_detection(self):
        """Test relation detection in clauses."""
        test_cases = [
            ("near hanuman mandir", "near"),
            ("opposite nagar parishad office", "opposite"),
            ("behind big tree", "behind"),
            ("after chai tapri", "after")
        ]
        
        for clause, expected_relation in test_cases:
            result = self.extractor.detect_relation(clause)
            assert result == expected_relation
    
    def test_landmark_validation(self):
        """Test landmark validation."""
        valid_landmarks = [
            "Hanuman Mandir",
            "Police Station", 
            "Big Tree",
            "Chai Tapri",
            "Nagar Parishad Office",
            "Dmart Store"
        ]
        
        invalid_landmarks = [
            "200 meters",
            "straight road",
            "left turn",
            ""
        ]
        
        for landmark in valid_landmarks:
            assert self.extractor.validate_landmark(landmark) == True
        
        for landmark in invalid_landmarks:
            assert self.extractor.validate_landmark(landmark) == False
    
    def test_landmark_classification(self):
        """Test landmark type classification."""
        test_cases = [
            ("Hanuman Mandir", "RELIGIOUS"),
            ("Police Station", "GOV"),
            ("Government School", "EDUCATION"),
            ("City Hospital", "HEALTH"),
            ("Dmart Supermarket", "SHOP"),
            ("Railway Station", "TRANSPORT"),
            ("Big Tree", "NATURAL"),
            ("Main Chowk", "ROAD_JUNCTION")
        ]
        
        for landmark, expected_type in test_cases:
            result = self.extractor.classify_landmark_type(landmark)
            assert result == expected_type
    
    def test_landmark_weight_calculation(self):
        """Test landmark importance weighting."""
        test_cases = [
            ("GOV", 0.9),
            ("HEALTH", 0.85),
            ("EDUCATION", 0.8),
            ("RELIGIOUS", 0.7),
            ("SHOP", 0.6),
            ("NATURAL", 0.3)
        ]
        
        for landmark_type, expected_weight in test_cases:
            result = self.extractor.calculate_landmark_weight(landmark_type)
            assert result == expected_weight
    
    def test_complete_extraction_rule_based(self):
        """Test complete landmark extraction using rule-based method."""
        address = "Near Hanuman Mandir, after chai tapri, opposite Nagar Parishad office, lane behind big tree"
        
        result = self.extractor.extract_landmarks(address)
        
        # Check structure
        assert "landmarks" in result
        assert "additional_directions" in result
        assert "total_landmarks" in result
        assert result["total_landmarks"] >= 4
        
        # Check expected landmarks are present
        landmarks = result["landmarks"]
        landmark_names = [lm["landmark"] for lm in landmarks]
        
        expected_landmarks = ["Hanuman Mandir", "Chai Tapri", "Nagar Parishad Office", "Big Tree"]
        for expected in expected_landmarks:
            assert any(expected in name for name in landmark_names)
    
    def test_complete_extraction_spacy_matcher(self):
        """Test complete landmark extraction using spaCy Matcher method."""
        address = "opp police station, nr temple, behind reliance mart"
        
        result = self.extractor.extract_with_spacy_matcher(address)
        
        # Check structure
        assert "landmarks" in result
        assert "additional_directions" in result
        assert "total_landmarks" in result
        assert result["method"] == "spacy_matcher"
        
        # Should find at least 3 landmarks
        assert result["total_landmarks"] >= 3
    
    def test_chained_landmarks(self):
        """Test extraction of chained landmarks in single clause."""
        address = "near temple behind school opposite bank"
        
        result = self.extractor.extract_landmarks(address)
        
        # Should extract multiple landmarks from single clause
        assert result["total_landmarks"] >= 3
        
        relations = [lm["relation"] for lm in result["landmarks"]]
        assert "near" in relations
        assert "behind" in relations
        assert "opposite" in relations
    
    def test_abbreviation_expansion(self):
        """Test that abbreviations are properly expanded."""
        address = "opp Nagar Parishad office, nr temple"
        
        result = self.extractor.preprocess_text(address)
        
        # Should expand abbreviations
        assert "opposite" in result.lower()
        assert "near" in result.lower()
    
    def test_duplicate_removal(self):
        """Test that duplicate landmarks are removed."""
        # This would require a more complex test with actual duplicates
        address = "near temple, near temple, opposite school"
        
        result = self.extractor.extract_landmarks(address)
        
        # Should not have duplicate (relation, landmark) pairs
        unique_pairs = set()
        for lm in result["landmarks"]:
            pair = (lm["relation"], lm["landmark"])
            unique_pairs.add(pair)
        
        assert len(unique_pairs) == len(result["landmarks"])
    
    def test_weight_sorting(self):
        """Test that landmarks are sorted by weight/importance."""
        address = "near temple, opposite police station, behind tree"
        
        result = self.extractor.extract_landmarks(address)
        landmarks = result["landmarks"]
        
        # Police station (GOV) should have higher weight than temple (RELIGIOUS) 
        # which should have higher weight than tree (NATURAL)
        if len(landmarks) >= 3:
            weights = [lm["weight"] for lm in landmarks]
            # Weights should be in descending order
            assert weights == sorted(weights, reverse=True)
    
    def test_edge_cases(self):
        """Test edge cases and malformed input."""
        edge_cases = [
            "",  # Empty string
            "123 main street",  # No landmarks
            "near",  # Incomplete
            "xyz abc def",  # No recognizable landmarks
        ]
        
        for case in edge_cases:
            result = self.extractor.extract_landmarks(case)
            # Should not crash and return proper structure
            assert isinstance(result, dict)
            assert "landmarks" in result
            assert "additional_directions" in result

# Integration test
def test_integration_with_existing_pipeline():
    """Test that landmark extractor works with existing address parsing pipeline."""
    # This would integrate with the main AddressParser
    from src.pipelines.inference_pipeline import AddressParser
    
    parser = AddressParser()
    extractor = LandmarkExtractor()
    
    # Test address with landmarks
    address = "Flat 101, Sun Tower, MG Road, nr Tech Park, Bangalore, Karnataka 560001"
    
    # Parse with existing pipeline
    parsed_result = parser.parse(address)
    
    # Extract landmarks separately
    landmark_result = extractor.extract_landmarks(address)
    
    # Both should work without errors
    assert parsed_result is not None
    assert landmark_result is not None
    assert "landmarks" in landmark_result

if __name__ == "__main__":
    # Run tests manually
    extractor = LandmarkExtractor()
    
    # Quick manual test
    test_address = "Near Hanuman Mandir, after chai tapri, opposite Nagar Parishad office, lane behind big tree"
    result = extractor.extract_landmarks(test_address)
    
    print("=== Manual Test Results ===")
    print(f"Input: {test_address}")
    print(f"Total landmarks found: {result['total_landmarks']}")
    print("Extracted landmarks:")
    for i, lm in enumerate(result['landmarks'], 1):
        print(f"  {i}. {lm['relation']} {lm['landmark']} (Type: {lm['type']}, Weight: {lm['weight']})")
    print(f"Additional directions: {result['additional_directions']}")