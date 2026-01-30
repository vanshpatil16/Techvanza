import re
import spacy
from spacy.matcher import Matcher
from typing import List, Dict, Tuple, Optional
from src.utils.hinglish_processor import process_hinglish_address

class LandmarkExtractor:
    def __init__(self):
        """Initialize the landmark extraction pipeline with spaCy and predefined patterns."""
        # Load spaCy model
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            raise Exception("Please install en_core_web_sm model: python -m spacy download en_core_web_sm")
        
        self.matcher = Matcher(self.nlp.vocab)
        
        # Define relation keywords
        self.RELATIONS = {
            "near": ["near", "nr", "paas", "pass", "najdik", "nazdeek", "ke paas"],
            "behind": ["behind", "b/h", "peeche", "piche", "ke peeche"],
            "opposite": ["opposite", "opp", "samne", "saamne", "ke samne"],
            "beside": ["beside", "next to", "side", "baju", "bagal"],
            "after": ["after", "baad"],
            "before": ["before", "pehle"],
            "inside": ["inside", "andar", "ke andar"],
            "outside": ["outside", "bahar", "ke bahar"]
        }
        
        # Flatten all relations for quick lookup
        self.all_relations = []
        for rel_list in self.RELATIONS.values():
            self.all_relations.extend(rel_list)
        
        # Landmark keywords for validation
        self.LANDMARK_KEYWORDS = [
            "temple", "mandir", "masjid", "church", "gurudwara",
            "school", "college", "hospital", "clinic",
            "atm", "bank", "police station", "railway station",
            "bus stand", "post office",
            "dmart", "reliance", "petrol pump",
            "chowk", "naka", "market", "bazaar", "mall",
            "office", "building", "tower", "complex", "plaza", "centre",
            "park", "garden", "tree", "shop", "store",
            "beach", "sea", "ocean", "road", "highway", "lane", "gali",
            "playground", "recreation", "sports", "waterfront"
        ]
        
        # Compile patterns
        self._compile_patterns()
        
    def _compile_patterns(self):
        """Compile spaCy Matcher patterns for landmark extraction."""
        # Pattern 1: relation + Proper Noun(s) or Noun phrase
        pattern1 = [
            {"LOWER": {"IN": self.all_relations}},
            {"POS": {"IN": ["PROPN", "NOUN", "ADJ"]}, "OP": "+"}
        ]
        self.matcher.add("REL_LANDMARK", [pattern1])
        
        # Pattern 2: Lane/street + relation + landmark
        pattern2 = [
            {"LOWER": {"IN": ["lane", "gali", "road", "rd", "street", "st"]}},
            {"LOWER": {"IN": self.all_relations}},
            {"POS": {"IN": ["PROPN", "NOUN", "ADJ"]}, "OP": "+"}
        ]
        self.matcher.add("LANE_REL_LANDMARK", [pattern2])
        
        # Pattern 3: relation + "the" + landmark (optional "the")
        pattern3 = [
            {"LOWER": {"IN": self.all_relations}},
            {"LOWER": "the", "OP": "?"},
            {"POS": {"IN": ["PROPN", "NOUN", "ADJ"]}, "OP": "+"}
        ]
        self.matcher.add("REL_LANDMARK_THE", [pattern3])
        
        # Pattern 4: relation + determiner + landmark
        pattern4 = [
            {"LOWER": {"IN": self.all_relations}},
            {"POS": "DET", "OP": "?"},
            {"POS": {"IN": ["PROPN", "NOUN", "ADJ"]}, "OP": "+"}
        ]
        self.matcher.add("REL_LANDMARK_DET", [pattern4])
        
    def preprocess_text(self, text: str) -> str:
        """Preprocess text with Hinglish conversion and normalization."""
        # Convert Hinglish to English
        processed_text, _ = process_hinglish_address(text)
        
        # Additional normalization
        # Expand common abbreviations
        abbreviations = {
            "opp": "opposite",
            "nr": "near",
            "b/h": "behind",
            "sec": "sector",
            "blk": "block",
            "apt": "apartment",
            "flr": "floor"
        }
        
        words = processed_text.split()
        expanded_words = []
        for word in words:
            expanded_words.append(abbreviations.get(word.lower(), word))
        
        processed_text = " ".join(expanded_words)
        
        # Normalize separators
        processed_text = re.sub(r'[;|/\\-]', ',', processed_text)
        
        # Clean extra punctuation
        processed_text = re.sub(r'[^\w\s,]', ' ', processed_text)
        
        # Remove extra spaces
        processed_text = ' '.join(processed_text.split())
        
        return processed_text
    
    def segment_clauses(self, text: str) -> List[str]:
        """Segment address into meaningful clauses."""
        # Split by commas and connectors
        clauses = re.split(r'[,;&]', text)
        clauses = [clause.strip() for clause in clauses if clause.strip()]
        
        # Further split by relation keywords if multiple relations in one clause
        final_clauses = []
        for clause in clauses:
            # Check if clause contains multiple relations
            relation_matches = []
            for rel in self.all_relations:
                if rel in clause.lower():
                    relation_matches.append(rel)
            
            if len(relation_matches) > 1:
                # Split by relations
                parts = [clause]
                for rel in sorted(relation_matches, key=len, reverse=True):
                    new_parts = []
                    for part in parts:
                        if rel in part.lower():
                            # Split at this relation
                            split_parts = re.split(rf'\b{re.escape(rel)}\b', part, 1)
                            if len(split_parts) == 2:
                                before, after = split_parts
                                if before.strip():
                                    new_parts.append(before.strip())
                                new_parts.append(f"{rel} {after.strip()}")
                            else:
                                new_parts.append(part)
                        else:
                            new_parts.append(part)
                    parts = new_parts
                final_clauses.extend([p for p in parts if p.strip()])
            else:
                final_clauses.append(clause)
        
        return [clause for clause in final_clauses if clause]
    
    def detect_relation(self, clause: str) -> Optional[str]:
        """Detect the relation in a clause."""
        clause_lower = clause.lower()
        
        # Priority order for relations
        priority_order = ["opposite", "behind", "near", "after", "before", "beside", "inside", "outside"]
        
        for rel in priority_order:
            if rel in clause_lower:
                return rel
        
        # Check for other relation variants
        for rel_key, rel_variants in self.RELATIONS.items():
            for variant in rel_variants:
                if variant in clause_lower:
                    return rel_key
        
        return None
    
    def extract_landmark_phrase(self, clause: str, relation: str) -> str:
        """Extract the landmark phrase from a clause given the relation."""
        # Find the position of the relation
        rel_pos = clause.lower().find(relation.lower())
        if rel_pos == -1:
            return ""
        
        # Extract text after the relation
        landmark_text = clause[rel_pos + len(relation):].strip()
        
        # Clean the landmark phrase
        # Remove leading articles and determiners
        landmark_text = re.sub(r'^\s*(the|a|an)\s+', '', landmark_text, flags=re.IGNORECASE)
        
        # Remove trailing punctuation
        landmark_text = re.sub(r'[,\.\s]+$', '', landmark_text)
        
        # Remove extra spaces
        landmark_text = ' '.join(landmark_text.split())
        
        return landmark_text
    
    def validate_landmark(self, landmark: str) -> bool:
        """Validate if the extracted text is a proper landmark."""
        if not landmark or len(landmark.strip()) < 2:
            return False
        
        landmark_lower = landmark.lower()
        
        # Check if it contains landmark keywords
        for keyword in self.LANDMARK_KEYWORDS:
            if keyword in landmark_lower:
                return True
        
        # Check if it looks like a proper noun (capitalized words)
        words = landmark.split()
        if len(words) > 0 and words[0][0].isupper():
            return True
        
        # Check if it contains common landmark patterns
        landmark_patterns = [
            r'\b(temple|mandir|masjid|church|gurudwara)\b',
            r'\b(school|college|university|institute)\b',
            r'\b(hospital|clinic|medical)\b',
            r'\b(bank|atm|post office)\b',
            r'\b(station|airport|bus stand)\b',
            r'\b(market|mall|shop|store)\b',
            r'\b(office|building|tower)\b'
        ]
        
        for pattern in landmark_patterns:
            if re.search(pattern, landmark_lower):
                return True
        
        return False
    
    def classify_landmark_type(self, landmark: str) -> str:
        """Classify the type of landmark."""
        landmark_lower = landmark.lower()
        
        # Religious landmarks
        religious_keywords = ["temple", "mandir", "masjid", "church", "gurudwara", "mosque"]
        if any(keyword in landmark_lower for keyword in religious_keywords):
            return "RELIGIOUS"
        
        # Government/Official
        gov_keywords = ["office", "parishad", "nagar", "police", "court", "municipal"]
        if any(keyword in landmark_lower for keyword in gov_keywords):
            return "GOV"
        
        # Education
        edu_keywords = ["school", "college", "university", "institute", "academy"]
        if any(keyword in landmark_lower for keyword in edu_keywords):
            return "EDUCATION"
        
        # Health
        health_keywords = ["hospital", "clinic", "medical", "pharmacy", "nursing"]
        if any(keyword in landmark_lower for keyword in health_keywords):
            return "HEALTH"
        
        # Commercial/Retail
        commercial_keywords = ["dmart", "reliance", "shop", "store", "market"]
        if any(keyword in landmark_lower for keyword in commercial_keywords):
            return "SHOP"
        
        # Malls and Shopping Complexes
        mall_keywords = ["mall", "complex", "plaza", "centre", "center"]
        if any(keyword in landmark_lower for keyword in mall_keywords):
            return "MALL"
        
        # Transportation
        transport_keywords = ["station", "airport", "bus", "railway", "metro"]
        if any(keyword in landmark_lower for keyword in transport_keywords):
            return "TRANSPORT"
        
        # Parks and Recreation
        park_keywords = ["park", "garden", "playground", "recreation", "sports"]
        if any(keyword in landmark_lower for keyword in park_keywords):
            return "PARK"
        
        # Beaches and Water Bodies
        beach_keywords = ["beach", "sea", "ocean", "coast", "shore", "waterfront"]
        if any(keyword in landmark_lower for keyword in beach_keywords):
            return "BEACH"
        
        # Roads and Highways
        road_keywords = ["road", "highway", "expressway", "boulevard", "avenue"]
        if any(keyword in landmark_lower for keyword in road_keywords):
            return "ROAD"
        
        # Road Junctions/Intersections
        junction_keywords = ["chowk", "naka", "square", "junction", "crossing", "lane", "gali"]
        if any(keyword in landmark_lower for keyword in junction_keywords):
            return "ROAD_JUNCTION"
        
        # Natural landmarks (remaining)
        natural_keywords = ["tree", "lake", "river", "hill", "mountain", "forest"]
        if any(keyword in landmark_lower for keyword in natural_keywords):
            return "NATURAL"
        
        return "OTHER"
    
    def calculate_landmark_weight(self, landmark_type: str) -> float:
        """Calculate importance weight for landmark ranking."""
        weight_map = {
            "GOV": 0.9,
            "HEALTH": 0.85,
            "EDUCATION": 0.8,
            "TRANSPORT": 0.8,
            "RELIGIOUS": 0.7,
            "SHOP": 0.6,
            "MALL": 0.65,
            "PARK": 0.5,
            "BEACH": 0.55,
            "ROAD": 0.45,
            "ROAD_JUNCTION": 0.5,
            "NATURAL": 0.3,
            "OTHER": 0.4
        }
        return weight_map.get(landmark_type, 0.4)
    
    def extract_landmarks(self, address_text: str) -> Dict:
        """Main method to extract landmarks from address text."""
        # Step 1: Preprocess
        processed_text = self.preprocess_text(address_text)
        
        # Step 2: Segment into clauses
        clauses = self.segment_clauses(processed_text)
        
        # Step 3: Extract landmarks from each clause
        landmarks = []
        additional_directions = []
        
        for clause in clauses:
            relation = self.detect_relation(clause)
            if relation:
                landmark_phrase = self.extract_landmark_phrase(clause, relation)
                if landmark_phrase and self.validate_landmark(landmark_phrase):
                    landmark_type = self.classify_landmark_type(landmark_phrase)
                    weight = self.calculate_landmark_weight(landmark_type)
                    
                    landmarks.append({
                        "relation": relation,
                        "landmark": landmark_phrase.title(),
                        "type": landmark_type,
                        "weight": weight
                    })
                else:
                    # Store as additional direction if not a valid landmark
                    additional_directions.append(clause)
            else:
                # No relation found - check if clause itself is a valid landmark
                # This handles standalone roads, parks, buildings, etc.
                if self.validate_landmark(clause):
                    landmark_type = self.classify_landmark_type(clause)
                    weight = self.calculate_landmark_weight(landmark_type)
                    
                    # For standalone landmarks, use "at" as default relation
                    landmarks.append({
                        "relation": "at",
                        "landmark": clause.title(),
                        "type": landmark_type,
                        "weight": weight
                    })
                else:
                    # Check if it might be a locality/area name (like Versova, Andheri West)
                    # Even if not recognized as a landmark, these are important for location
                    clause_clean = clause.strip()
                    # Only treat as locality if it's alphabetic and not just numbers
                    if (len(clause_clean) >= 3 and 
                        not clause_clean.isdigit() and 
                        clause_clean.lower() not in ['mumbai', 'delhi', 'bangalore', 'chennai', 'kolkata']):  # Common cities
                        # Likely a locality or area name
                        landmarks.append({
                            "relation": "at",
                            "landmark": clause.title(),
                            "type": "LOCALITY",
                            "weight": 0.75  # Medium-high weight for localities
                        })
                    else:
                        # Not a valid landmark, store as additional direction
                        additional_directions.append(clause)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_landmarks = []
        for lm in landmarks:
            key = (lm["relation"], lm["landmark"])
            if key not in seen:
                seen.add(key)
                unique_landmarks.append(lm)
        
        # Sort by weight (importance)
        unique_landmarks.sort(key=lambda x: x["weight"], reverse=True)
        
        return {
            "landmarks": unique_landmarks,
            "additional_directions": additional_directions,
            "total_landmarks": len(unique_landmarks),
            "preprocessed_text": processed_text
        }
    
    def extract_with_spacy_matcher(self, address_text: str) -> Dict:
        """Alternative method using spaCy Matcher for more sophisticated extraction."""
        # Preprocess text
        processed_text = self.preprocess_text(address_text)
        
        # Process with spaCy
        doc = self.nlp(processed_text)
        
        # Find matches
        matches = self.matcher(doc)
        
        landmarks = []
        matched_spans = []
        
        # Extract matches
        for match_id, start, end in matches:
            span = doc[start:end]
            relation_token = span[0].text.lower()
            
            # Map relation token to canonical relation
            relation = None
            for rel_key, rel_variants in self.RELATIONS.items():
                if relation_token in rel_variants:
                    relation = rel_key
                    break
            
            if relation:
                # Extract landmark (everything after relation)
                landmark_tokens = span[1:]
                if landmark_tokens:
                    landmark_text = " ".join([token.text for token in landmark_tokens])
                    landmark_text = landmark_text.strip(",. ")
                    
                    if landmark_text and self.validate_landmark(landmark_text):
                        landmark_type = self.classify_landmark_type(landmark_text)
                        weight = self.calculate_landmark_weight(landmark_type)
                        
                        landmarks.append({
                            "relation": relation,
                            "landmark": landmark_text.title(),
                            "type": landmark_type,
                            "weight": weight,
                            "span_start": start,
                            "span_end": end
                        })
                        matched_spans.append((start, end))
        
        # Handle non-matched parts as additional directions
        additional_directions = []
        all_tokens = [token for token in doc]
        
        # Find unmatched tokens
        matched_positions = set()
        for start, end in matched_spans:
            for i in range(start, end):
                matched_positions.add(i)
        
        unmatched_tokens = [token for i, token in enumerate(all_tokens) if i not in matched_positions]
        if unmatched_tokens:
            additional_text = " ".join([token.text for token in unmatched_tokens])
            if additional_text.strip():
                additional_directions.append(additional_text.strip())
        
        # Remove duplicates and sort
        seen = set()
        unique_landmarks = []
        for lm in landmarks:
            key = (lm["relation"], lm["landmark"])
            if key not in seen:
                seen.add(key)
                unique_landmarks.append(lm)
        
        unique_landmarks.sort(key=lambda x: x["weight"], reverse=True)
        
        return {
            "landmarks": unique_landmarks,
            "additional_directions": additional_directions,
            "total_landmarks": len(unique_landmarks),
            "preprocessed_text": processed_text,
            "method": "spacy_matcher"
        }

# Example usage and testing
if __name__ == "__main__":
    extractor = LandmarkExtractor()
    
    # Test cases
    test_addresses = [
        "Near Hanuman Mandir, after chai tapri, opposite Nagar Parishad office, lane behind big tree",
        "opp police station, nr temple, behind reliance mart",
        "ke paas mandir hai, ke peeche school hai",
        "near big temple behind small hospital opposite bank"
    ]
    
    for i, address in enumerate(test_addresses, 1):
        print(f"\n=== Test Case {i} ===")
        print(f"Input: {address}")
        
        # Method 1: Rule-based
        result1 = extractor.extract_landmarks(address)
        print(f"Rule-based method:")
        print(f"Landmarks: {result1['landmarks']}")
        print(f"Additional: {result1['additional_directions']}")
        
        # Method 2: spaCy Matcher
        result2 = extractor.extract_with_spacy_matcher(address)
        print(f"\nspaCy Matcher method:")
        print(f"Landmarks: {result2['landmarks']}")
        print(f"Additional: {result2['additional_directions']}")