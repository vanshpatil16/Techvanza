from src.pipelines.landmark_extraction_pipeline import LandmarkExtractor

extractor = LandmarkExtractor()

# Test your original address
address = "sai prasad,mahesh 202 ,gaulwada,vasai west,suruchi road"

print("=== TESTING ENHANCED PIPELINE ===")
print(f"Input: {address}")

result = extractor.extract_landmarks(address)

print(f"\n✅ TOTAL LANDMARKS FOUND: {result['total_landmarks']}")

if result['landmarks']:
    print("\n📍 EXTRACTED LANDMARKS:")
    for i, lm in enumerate(result['landmarks'], 1):
        print(f"  {i}. [{lm['relation'].upper()}] {lm['landmark']} → {lm['type']} (weight: {lm['weight']})")
else:
    print("\n❌ No landmarks found")

print(f"\n🧭 ADDITIONAL DIRECTIONS:")
for i, direction in enumerate(result['additional_directions'], 1):
    print(f"  {i}. {direction}")

# Test the specific case of "suruchi road"
print("\n" + "="*50)
print("Testing 'suruchi road' specifically:")
simple_result = extractor.extract_landmarks("suruchi road")
if simple_result['landmarks']:
    lm = simple_result['landmarks'][0]
    print(f"✅ Found: [{lm['relation'].upper()}] {lm['landmark']} → {lm['type']} (weight: {lm['weight']})")
else:
    print("❌ Not found")

# Test a few more road examples
print("\nTesting other road examples:")
road_tests = ["main road", "highway road", "gandhi road"]
for test in road_tests:
    res = extractor.extract_landmarks(test)
    if res['landmarks']:
        lm = res['landmarks'][0]
        print(f"  '{test}' → [{lm['relation']}] {lm['landmark']} ({lm['type']})")
    else:
        print(f"  '{test}' → Not extracted")