import re
import yaml
from pathlib import Path
from src.utils import clean_text, expand_abbreviations, translate_terms, normalize_address

class AddressParser:
    def __init__(self, config_path: str = "config/model_config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self.patterns = self.config.get('patterns', {})
        self.abbreviations = self.config.get('abbreviations', {})
        self.translations = self.config.get('translations', {})
        self.states = [state.lower() for state in self.config.get('states', [])]
        self.pincode_regex = re.compile(self.patterns.get('pincode', r'\b\d{6}\b'))
        self.house_no_regex = re.compile(self.patterns.get('house_number', r'\b(?:No\.?|#|Plot No\.?|Flat No\.?|H\.No\.?)\s*[\w\-/]+'), re.IGNORECASE)

    def _load_config(self):
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}

    def extract_pincode(self, text):
        matches = self.pincode_regex.findall(text)
        if matches:
            return matches[-1], text.replace(matches[-1], "").strip() # Return last match as pincode usually at end
        return "", text

    def extract_state(self, text):
        found_state = ""
        # Search for full state names
        for state in self.states:
            if state in text:
                found_state = state.title()
                text = text.replace(state, "").strip()
                break # Heuristic: only one state per address
        return found_state, text

    def extract_house_number(self, text):
        match = self.house_no_regex.search(text)
        if match:
            house_no = match.group()
            # Clean up the house number string if needed
            return house_no, text.replace(house_no, "").strip()
        # Fallback: check for numbers at the very start
        start_match = re.match(r'^(\d+[\w-]*)', text)
        if start_match:
             house_no = start_match.group(1)
             return house_no, text[len(house_no):].strip()
        return "", text

    def calculate_confidence(self, extracted_data):
        score = 0.0
        reasons = []

        # Weights
        weights = {
            'pincode': 0.3,
            'state': 0.2,
            'house_number': 0.2,
            'city': 0.15,
            'locality': 0.15
        }

        if extracted_data['pincode']:
            score += weights['pincode']
            reasons.append("Pincode found")
        else:
            reasons.append("Pincode missing")

        if extracted_data['state']:
            score += weights['state']
            reasons.append("State found")

        if extracted_data['house_number']:
            score += weights['house_number']
            reasons.append("House number found")

        # Simplified city/locality check for confidence
        if extracted_data['city']:
            score += weights['city']
            reasons.append("City/Locality likely identified")

        return round(min(score, 1.0), 2), reasons

    def parse(self, raw_address):
        # 1. Preprocessing
        cleaned_text = clean_text(raw_address)
        
        # 2. Expand & Translate
        # We need to tokenize to expand/translate safely or use regex replacement
        # For simplicity, doing string replacement on whole text might be risky for short words, 
        # but okay for this heuristic approach with specific keys.
        # Better: split by space, map, join.
        match_words = cleaned_text.split()
        expanded_words = [self.abbreviations.get(w, w) for w in match_words]
        translated_words = [self.translations.get(w, w) for w in expanded_words]
        processed_text = " ".join(translated_words)

        # 3. Extraction
        pincode, processed_text = self.extract_pincode(processed_text)
        state, processed_text = self.extract_state(processed_text)
        house_number, processed_text = self.extract_house_number(processed_text)

        # Remaining text likely contains Building, Street, Locality/City, Landmark
        # This is the hardest part for heuristics without NER.
        # Heuristic: 
        # - Split by commas if present
        # - If commas, assume structure: [Building], [Street], [Locality], [City]
        # - If no commas, rely on keywords.

        # Heuristic for City: Last part of remaining text?
        # Or look for known cities? (Not implemented here without big DB)
        # Fallback: Assume the word before pincode/state was City if punctuation allows.
        
        parts = [p.strip() for p in processed_text.split(',') if p.strip()]
        
        building_name = ""
        street = ""
        locality = ""
        city = ""
        landmark = ""
        additional = ""

        if len(parts) >= 3:
             city = parts[-1]
             locality = parts[-2]
             street = parts[-3]
             if len(parts) > 3:
                 building_name = parts[0] # Very rough guess
        elif len(parts) == 2:
             city = parts[-1]
             locality = parts[0]
        elif len(parts) == 1:
             # Just one blob
             locality = parts[0]
        
        # Refine Landmark: search for "near", "opposite", "behind" in the chunks
        # and extract the phrase after it.
        # (This is a simplified implementation)
        
        country = "India" # Default as per requirements context

        # 4. Construct Result
        normalized = normalize_address(
            house_number.title(), 
            building_name.title(), 
            street.title(), 
            locality.title(), 
            landmark.title(), 
            city.title(), 
            state.title(), 
            pincode, 
            country
        )

        result = {
            "house_number": house_number,
            "building_name": building_name.title(),
            "street_or_lane": street.title(),
            "locality_or_area": locality.title(),
            "landmark": landmark.title(),
            "city": city.title(),
            "state": state.title(),
            "pincode": pincode,
            "country": country,
            "additional_directions": additional,
            "normalized_address": normalized
        }
        
        score, reasons = self.calculate_confidence(result)
        result["confidence_score"] = score
        result["reasons"] = reasons

        return result

if __name__ == "__main__":
    # Test run
    parser = AddressParser()
    sample = "Flat 101, Sun Tower, MG Road, nr Tech Park, Bangalore, Karnataka 560001"
    print(parser.parse(sample))
