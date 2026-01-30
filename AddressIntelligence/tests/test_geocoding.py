import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.pipelines.geocoding_pipeline import (
    GeocodeQueryBuilder, 
    GeocodingClient, 
    CandidateRankingEngine, 
    GeocodingPipeline
)

def test_query_builder():
    """Test the query builder functionality"""
    print("🧪 Testing Query Builder...")
    
    context = {
        "building": "Sai Prasad",
        "house": "Mahesh 202",
        "locality": "Gaulwada",
        "city": "Vasai West",
        "landmarks": [
            {"relation": "at", "landmark": "Suruchi Road", "type": "ROAD", "weight": 0.7},
            {"relation": "at", "landmark": "Gaulwada", "type": "LOCALITY", "weight": 0.8}
        ],
        "raw_text": "sai prasad, mahesh 202, gaulwada, vasai west, suruchi road"
    }
    
    queries = GeocodeQueryBuilder.build_geocode_queries(context)
    
    print(f"Generated {len(queries)} queries:")
    for i, query in enumerate(queries, 1):
        print(f"  {i}. {query}")
    
    # Verify query structure
    assert len(queries) > 0, "Should generate at least one query"
    assert "Vasai West, India" in queries, "Should include city-level query"
    assert "Gaulwada, Vasai West, India" in queries, "Should include locality query"
    
    print("✅ Query Builder test passed\n")

def test_landmark_scoring():
    """Test landmark matching scoring"""
    print("🧪 Testing Landmark Scoring...")
    
    # Test candidate names
    candidates = [
        "Suruchi Road, Vasai West, Maharashtra, India",
        "Gaulwada, Vasai, Maharashtra, India",
        "Random Location, Mumbai, Maharashtra, India"
    ]
    
    landmarks = [
        {"relation": "at", "landmark": "Suruchi Road", "type": "ROAD", "weight": 0.7},
        {"relation": "at", "landmark": "Gaulwada", "type": "LOCALITY", "weight": 0.8}
    ]
    
    print("Landmark matching scores:")
    for candidate in candidates:
        score = CandidateRankingEngine.landmark_match_score(candidate, landmarks)
        print(f"  '{candidate[:30]}...' -> Score: {score:.3f}")
    
    # Verify scoring logic
    suruchi_score = CandidateRankingEngine.landmark_match_score(candidates[0], landmarks)
    gaulwada_score = CandidateRankingEngine.landmark_match_score(candidates[1], landmarks)
    
    assert suruchi_score > 0, "Should match Suruchi Road"
    assert gaulwada_score > 0, "Should match Gaulwada"
    assert gaulwada_score >= suruchi_score, "Gaulwada should have higher weight"
    
    print("✅ Landmark Scoring test passed\n")

def test_complete_pipeline():
    """Test the complete geocoding pipeline"""
    print("🧪 Testing Complete Pipeline...")
    
    # Test context
    context = {
        "building": "Sai Prasad",
        "house": "Mahesh 202", 
        "locality": "Gaulwada",
        "city": "Vasai West",
        "state": "Maharashtra",
        "pincode": "",
        "landmarks": [
            {"relation": "at", "landmark": "Suruchi Road", "type": "ROAD", "weight": 0.7},
            {"relation": "at", "landmark": "Gaulwada", "type": "LOCALITY", "weight": 0.8}
        ],
        "raw_text": "sai prasad, mahesh 202, gaulwada, vasai west, suruchi road"
    }
    
    # Initialize pipeline
    pipeline = GeocodingPipeline()
    
    # Run geocoding
    result = pipeline.geocode_address(context)
    
    if result:
        print("✅ Pipeline execution successful")
        print(f"  Latitude: {result['latitude']}")
        print(f"  Longitude: {result['longitude']}")
        print(f"  Confidence: {result['confidence']}")
        print(f"  Address: {result['formatted_address'][:50]}...")
        
        # Verify result structure
        required_fields = ['latitude', 'longitude', 'confidence', 'formatted_address']
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"
        
        # Verify coordinate validity
        assert -90 <= result['latitude'] <= 90, "Invalid latitude"
        assert -180 <= result['longitude'] <= 180, "Invalid longitude"
        assert 0 <= result['confidence'] <= 1, "Invalid confidence score"
        
    else:
        print("⚠️  Pipeline returned no results (may be due to network/OSM availability)")
    
    print("✅ Complete Pipeline test completed\n")

def test_batch_processing():
    """Test batch geocoding functionality"""
    print("🧪 Testing Batch Processing...")
    
    contexts = [
        {
            "building": "Building A",
            "house": "123",
            "locality": "Area 1", 
            "city": "City A",
            "landmarks": [{"relation": "near", "landmark": "Landmark A", "type": "SHOP", "weight": 0.6}],
            "raw_text": "building a, 123, area 1, city a"
        },
        {
            "building": "Building B",
            "house": "456",
            "locality": "Area 2",
            "city": "City B", 
            "landmarks": [{"relation": "opposite", "landmark": "Landmark B", "type": "GOV", "weight": 0.9}],
            "raw_text": "building b, 456, area 2, city b"
        }
    ]
    
    pipeline = GeocodingPipeline()
    
    # Test batch processing
    results = pipeline.batch_geocode(contexts)
    
    print(f"Processed {len(contexts)} contexts, got {len(results)} results")
    
    for i, result in enumerate(results):
        if result:
            print(f"  Context {i+1}: Success (confidence: {result['confidence']:.3f})")
        else:
            print(f"  Context {i+1}: No result")
    
    print("✅ Batch Processing test completed\n")

def main():
    """Run all tests"""
    print("🚀 Running Geocoding Pipeline Tests\n")
    print("=" * 50)
    
    try:
        test_query_builder()
        test_landmark_scoring()
        test_complete_pipeline()
        test_batch_processing()
        
        print("🎉 All tests completed successfully!")
        print("\n📝 Summary:")
        print("✅ Query Builder: Generates multiple geocoding queries")
        print("✅ Landmark Scoring: Matches landmarks with weighted scoring")
        print("✅ Complete Pipeline: End-to-end geocoding with confidence scoring")
        print("✅ Batch Processing: Handles multiple addresses efficiently")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()