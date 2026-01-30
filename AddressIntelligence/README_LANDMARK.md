# 📍 Landmark Extraction Pipeline for PS1

## Overview
This is a comprehensive landmark extraction pipeline designed for PS1 hackathon that extracts structured landmark information from Indian addresses, particularly for Tier 2/3 locations where addresses are primarily described through landmarks and spatial relations.

## Key Features

### 🎯 Core Capabilities
- **Relation Detection**: Identifies spatial relations (near, opposite, behind, after, etc.)
- **Landmark Extraction**: Captures landmark entities from complex address text
- **Hinglish Processing**: Converts Hinglish addresses to English for better processing
- **Landmark Classification**: Categorizes landmarks into types (RELIGIOUS, GOV, EDUCATION, etc.)
- **Importance Weighting**: Assigns weights for geocoding priority
- **Duplicate Handling**: Removes duplicate landmark entries

### 🧠 Technical Approach
**Two Implementation Methods:**
1. **Rule-based (Fast)**: Quick pattern matching for hackathon speed
2. **spaCy Matcher (AI-powered)**: More sophisticated NLP-based extraction

## Installation

### 1. Install Dependencies
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 2. Run Tests
```bash
python -m pytest tests/test_landmark_extraction.py -v
```

### 3. Run Demo Application
```bash
streamlit run entrypoint/landmark_demo.py
```

## Usage Examples

### Basic Usage
```python
from src.pipelines.landmark_extraction_pipeline import LandmarkExtractor

extractor = LandmarkExtractor()

# Input address
address = "Near Hanuman Mandir, after chai tapri, opposite Nagar Parishad office, lane behind big tree"

# Extract landmarks
result = extractor.extract_landmarks(address)

print(result['landmarks'])
# Output:
# [
#   {"relation": "near", "landmark": "Hanuman Mandir", "type": "RELIGIOUS", "weight": 0.7},
#   {"relation": "after", "landmark": "Chai Tapri", "type": "SHOP", "weight": 0.6},
#   {"relation": "opposite", "landmark": "Nagar Parishad Office", "type": "GOV", "weight": 0.9},
#   {"relation": "behind", "landmark": "Big Tree", "type": "NATURAL", "weight": 0.3}
# ]
```

### Using spaCy Matcher Method
```python
# More sophisticated extraction
result = extractor.extract_with_spacy_matcher(address)
```

## Pipeline Workflow

### 🔧 Step-by-Step Process

1. **Preprocessing**
   - Hinglish to English conversion
   - Abbreviation expansion (opp→opposite, nr→near)
   - Text normalization and cleaning

2. **Clause Segmentation**
   - Split by commas and connectors
   - Handle chained landmarks in single clauses

3. **Relation Detection**
   - Identify spatial relations using keyword matching
   - Priority-based relation selection

4. **Landmark Extraction**
   - Extract landmark phrase after relation keyword
   - Clean and validate extracted text

5. **Landmark Validation**
   - Check against landmark keywords
   - Validate proper noun structure
   - Filter out non-landmark phrases

6. **Type Classification**
   - RELIGIOUS: temples, mosques, churches
   - GOV: police stations, government offices
   - EDUCATION: schools, colleges
   - HEALTH: hospitals, clinics
   - SHOP: dmart, shops, stores
   - TRANSPORT: railway stations, bus stands
   - NATURAL: trees, parks
   - ROAD_JUNCTION: chowks, intersections

7. **Importance Weighting**
   - GOV/Police stations: 0.9
   - Hospitals/Schools: 0.8-0.85
   - Religious places: 0.7
   - Shops: 0.6
   - Natural landmarks: 0.3

8. **Deduplication & Sorting**
   - Remove duplicate (relation, landmark) pairs
   - Sort by weight/importance

## Test Cases

The pipeline handles various complex scenarios:

### ✅ Basic Extraction
```
Input: "Near Hanuman Mandir, after chai tapri"
Output: 2 landmarks with correct relations and types
```

### ✅ Hinglish Processing
```
Input: "ke paas mandir hai, ke peeche school hai"
Output: "near temple, behind school" correctly extracted
```

### ✅ Chained Landmarks
```
Input: "near temple behind school opposite bank"
Output: 3 separate landmarks extracted from single clause
```

### ✅ Abbreviation Handling
```
Input: "opp police station, nr temple"
Output: "opposite police station, near temple"
```

## For Judges - Key Points

### 🎯 One-liner Pitch
"We extract landmark relations as structured graph-like data and use weighted landmark ranking to build accurate geocoding queries for Tier 2/3 Indian addresses."

### 🔥 Technical Highlights
- **Dual Approach**: Rule-based speed + spaCy NLP sophistication
- **Hinglish Support**: Handles mixed English-Hindi addresses common in India
- **Relation-Aware**: Understands spatial semantics (near/behind/opposite/after)
- **Structured Output**: JSON format ready for geocoding APIs
- **Importance Ranking**: Weighted landmarks for better location accuracy

### 🏆 Hackathon Advantages
- **Fast Implementation**: Ready-to-use pipeline
- **Comprehensive Testing**: Extensive test coverage
- **Interactive Demo**: Streamlit application for live demonstration
- **Scalable Design**: Modular architecture for future enhancements

## Project Structure
```
AddressIntelligence/
├── src/
│   ├── pipelines/
│   │   ├── landmark_extraction_pipeline.py  # Main landmark extractor
│   │   └── inference_pipeline.py           # Existing address parser
│   └── utils/
│       └── hinglish_processor.py           # Hinglish conversion utilities
├── tests/
│   └── test_landmark_extraction.py         # Comprehensive test suite
├── entrypoint/
│   └── landmark_demo.py                    # Streamlit demo application
├── requirements.txt                        # Dependencies
└── README_LANDMARK.md                      # This file
```

## Future Enhancements
- Integration with geocoding APIs
- Machine learning model for landmark classification
- Multi-language support beyond Hinglish
- Address completion suggestions
- Real-time location verification

## Contact
For questions about the landmark extraction pipeline, please refer to the test files and demo application for detailed examples and usage patterns.