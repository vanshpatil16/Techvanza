from src.pipelines.landmark_extraction_pipeline import LandmarkExtractor

# Test the enhanced landmark classification
extractor = LandmarkExtractor()

# Test address with roads, beaches, parks, and malls
test_address = "near central park, opposite marine drive beach, behind phoenix mall, lane beside main road"

print("Testing enhanced landmark extraction...")
print(f"Input: {test_address}\n")

result = extractor.extract_landmarks(test_address)

print(f"Total landmarks found: {result['total_landmarks']}")
print("\nExtracted landmarks:")

for i, landmark in enumerate(result['landmarks'], 1):
    print(f"{i}. {landmark['relation']} {landmark['landmark']} -> {landmark['type']} (weight: {landmark['weight']})")

print(f"\nAdditional directions: {result['additional_directions']}")

# Test individual classifications
print("\n" + "="*50)
print("Testing individual landmark classifications:")

test_cases = [
    "central park",
    "marine drive beach", 
    "phoenix mall",
    "main road",
    "shopping complex",
    "sports playground"
]

for test_case in test_cases:
    classification = extractor.classify_landmark_type(test_case)
    weight = extractor.calculate_landmark_weight(classification)
    print(f"'{test_case}' -> {classification} (weight: {weight})")