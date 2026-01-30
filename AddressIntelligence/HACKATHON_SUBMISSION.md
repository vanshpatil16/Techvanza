# 🏆 PS1 Landmark Extraction Pipeline - Hackathon Submission

## 🎯 Executive Summary

I've successfully implemented a **comprehensive landmark extraction pipeline** for your PS1 project that addresses the core challenge of extracting structured landmark information from Tier 2/3 Indian addresses.

## ✅ What's Been Delivered

### 1. **Core Pipeline** (`src/pipelines/landmark_extraction_pipeline.py`)
- **Dual extraction methods**: Rule-based (fast) and spaCy Matcher (AI-powered)
- **Complete workflow**: Preprocessing → Segmentation → Relation detection → Landmark extraction → Validation → Classification → Weighting
- **Hinglish support**: Converts mixed English-Hindi addresses to English
- **Structured JSON output**: Ready for geocoding integration

### 2. **Comprehensive Testing** (`tests/test_landmark_extraction.py`)
- 12+ test cases covering all functionality
- Edge case handling and validation tests
- Integration tests with existing pipeline

### 3. **Interactive Demo** (`entrypoint/landmark_demo.py`)
- Streamlit web application for live demonstration
- Multiple example addresses
- Visual results display with charts
- Technical details explainer

### 4. **Documentation** (`README_LANDMARK.md`)
- Complete installation and usage guide
- Technical workflow explanation
- Judge presentation materials

## 🚀 Key Features Implemented

### 🔍 **Relation Detection**
- **Keywords**: near, opposite, behind, after, before, beside, inside, outside
- **Hinglish variants**: ke paas, ke peeche, ke samne, etc.
- **Abbreviation expansion**: opp→opposite, nr→near, b/h→behind

### 🏛️ **Landmark Classification**
- **RELIGIOUS**: temples, mosques, churches, gurudwaras
- **GOV**: police stations, government offices, Nagar Parishad
- **EDUCATION**: schools, colleges, universities
- **HEALTH**: hospitals, clinics, medical centers
- **SHOP**: dmart, reliance, petrol pumps, shops
- **TRANSPORT**: railway stations, bus stands
- **NATURAL**: trees, parks, gardens
- **ROAD_JUNCTION**: chowks, intersections

### ⚖️ **Importance Weighting**
- GOV/Police stations: **0.9** (highest priority)
- Hospitals/Schools: **0.8-0.85**
- Religious places: **0.7**
- Shops: **0.6**
- Natural landmarks: **0.3**

### 🧠 **Advanced Capabilities**
- **Chained landmark detection**: "near temple behind school opposite bank" → 3 landmarks
- **Duplicate removal**: Eliminates repeated landmark entries
- **Validation system**: Filters out non-landmark phrases
- **Clause segmentation**: Handles complex address structures

## 🎯 Sample Output

**Input**: `"Near Hanuman Mandir, after chai tapri, opposite Nagar Parishad office, lane behind big tree"`

**Output**:
```json
{
  "landmarks": [
    {
      "relation": "opposite",
      "landmark": "Nagar Parishad Office",
      "type": "GOV",
      "weight": 0.9
    },
    {
      "relation": "near",
      "landmark": "Hanuman Mandir",
      "type": "RELIGIOUS",
      "weight": 0.7
    },
    {
      "relation": "behind",
      "landmark": "Big Tree",
      "type": "NATURAL",
      "weight": 0.3
    }
  ],
  "additional_directions": ["after chai tapri"],
  "total_landmarks": 3
}
```

## 🏅 For Judges - Presentation Points

### 💡 **One-liner Pitch**
*"We extract landmark relations as structured graph-like data and use weighted landmark ranking to build accurate geocoding queries for Tier 2/3 Indian addresses."*

### 🔥 **Technical Highlights**
1. **Dual Approach**: Fast rule-based + sophisticated spaCy NLP
2. **Hinglish Processing**: Handles India's mixed-language address culture
3. **Relation-Aware**: Understands spatial semantics (near/behind/opposite/after)
4. **Structured Output**: JSON format ready for geocoding APIs
5. **Importance Ranking**: Weighted landmarks for better location accuracy

### 🏆 **Hackathon Advantages**
- ✅ **Ready-to-use**: Complete pipeline with demo application
- ✅ **Well-tested**: Comprehensive test suite with 12+ test cases
- ✅ **Interactive**: Streamlit demo for live judging
- ✅ **Scalable**: Modular design for future enhancements
- ✅ **Documented**: Clear usage instructions and technical details

## 📋 Quick Start Guide

### 1. Install Dependencies
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 2. Run Tests
```bash
python tests/test_landmark_extraction.py
```

### 3. Launch Demo
```bash
streamlit run entrypoint/landmark_demo.py
```

### 4. Use in Code
```python
from src.pipelines.landmark_extraction_pipeline import LandmarkExtractor

extractor = LandmarkExtractor()
result = extractor.extract_landmarks("Your address here")
print(result['landmarks'])
```

## 🎯 Test Results

The pipeline successfully handles:
- ✅ Basic landmark extraction
- ✅ Hinglish address processing
- ✅ Chained landmarks in single clauses
- ✅ Abbreviation expansion
- ✅ Landmark type classification
- ✅ Importance weighting
- ✅ Duplicate removal

## 🚀 Ready for Demo

The complete pipeline is ready for your hackathon presentation with:
- Interactive web demo application
- Comprehensive test coverage
- Clear documentation
- Production-ready code structure

**You're all set for an impressive PS1 presentation!** 🏆