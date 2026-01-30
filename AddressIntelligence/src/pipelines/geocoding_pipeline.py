import requests
import re
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

@dataclass
class GeocodeCandidate:
    """Represents a geocoding candidate result"""
    lat: float
    lon: float
    display_name: str
    importance: float
    address_details: Dict[str, Any]
    final_score: float = 0.0

class GeocodeQueryBuilder:
    """Builds geocoding queries from landmark context"""
    
    @staticmethod
    def build_geocode_queries(context: Dict) -> List[str]:
        """
        Build multiple geocoding queries in order of preference
        
        Args:
            context: Geocode context from landmark extractor
            
        Returns:
            List of query strings ordered by priority
        """
        queries = []
        landmarks = context.get("landmarks", [])
        
        # Extract components
        pincode = context.get("pincode", "").strip()
        city = context.get("city", "").strip()
        locality = context.get("locality", "").strip()
        state = context.get("state", "").strip()
        
        # Extract additional locality tokens from landmarks for more precise location matching
        locality_tokens = []
        landmarks = context.get("landmarks", [])
        for landmark in landmarks:
            if landmark.get("type") in ["LOCALITY", "ROAD", "GOV", "EDUCATION", "HEALTH"]:
                locality_tokens.append(landmark["landmark"])
        locality_tokens = list(set(locality_tokens))  # Remove duplicates
        
        # Sort landmarks by importance (weight)
        sorted_landmarks = sorted(landmarks, key=lambda x: x["weight"], reverse=True)
        
        # Q1: Strongest landmark + all location constraints
        if sorted_landmarks and city:
            base_query = f"{sorted_landmarks[0]['landmark']}, {city}"
            if locality:
                base_query = f"{sorted_landmarks[0]['landmark']}, {locality}, {city}"
            # Add locality tokens to narrow down location
            for loc_token in locality_tokens:
                if loc_token.lower() not in base_query.lower():
                    base_query = f"{sorted_landmarks[0]['landmark']}, {loc_token}, {base_query}"
                    break  # Add only the first relevant locality token
            if pincode:
                base_query += f", {pincode}"
            if state:
                base_query += f", {state}"
            base_query += ", India"
            queries.append(base_query)
        
        # Q2: Locality + city + pincode
        if locality and city:
            query = f"{locality}, {city}"
            # Add locality tokens for precision
            for loc_token in locality_tokens:
                if loc_token.lower() not in query.lower():
                    query = f"{loc_token}, {query}"
                    break
            if pincode:
                query += f", {pincode}"
            if state:
                query += f", {state}"
            query += ", India"
            queries.append(query)
        
        # Q3: Building + landmark + locality + city + pincode
        if context.get("building") and sorted_landmarks and city:
            query = f"{context['building']}, {sorted_landmarks[0]['landmark']}"
            if locality:
                query += f", {locality}"
            query += f", {city}"
            # Add locality tokens for precision
            for loc_token in locality_tokens:
                if loc_token.lower() not in query.lower():
                    query += f", {loc_token}"
                    break
            if pincode:
                query += f", {pincode}"
            if state:
                query += f", {state}"
            query += ", India"
            queries.append(query)
        
        # Q4: City + pincode fallback
        if city:
            query = f"{city}"
            # Add locality tokens for precision
            for loc_token in locality_tokens:
                if loc_token.lower() not in query.lower():
                    query = f"{loc_token}, {query}"
                    break
            if pincode:
                query += f", {pincode}"
            if state:
                query += f", {state}"
            query += ", India"
            queries.append(query)
        
        # Q5: Raw cleaned text with constraints
        if context.get("raw_text"):
            # Clean the raw text for better geocoding
            cleaned_raw = GeocodeQueryBuilder._clean_raw_text(context["raw_text"])
            if cleaned_raw:
                query = f"{cleaned_raw}"
                if city:
                    query += f", {city}"
                # Add locality tokens for precision
                for loc_token in locality_tokens:
                    if loc_token.lower() not in query.lower():
                        query += f", {loc_token}"
                        break
                if pincode:
                    query += f", {pincode}"
                if state:
                    query += f", {state}"
                query += ", India"
                queries.append(query)
        
        # Remove duplicates while preserving order
        unique_queries = []
        seen = set()
        for query in queries:
            query_clean = query.strip()
            if query_clean and query_clean not in seen:
                seen.add(query_clean)
                unique_queries.append(query_clean)
        
        # Ensure we have at least one query
        if not unique_queries and context.get("city"):
            # Fallback to basic city query
            fallback_query = f"{context.get('city')}, India"
            if fallback_query not in seen:
                unique_queries.append(fallback_query)
        
        return unique_queries
    
    @staticmethod
    def _clean_raw_text(raw_text: str) -> str:
        """Clean raw text for better geocoding results"""
        # Remove common address components that might confuse geocoder
        stop_words = ['flat', 'room', 'house', 'no', 'number', 'plot']
        
        # Split and clean
        words = raw_text.split(',')
        cleaned_parts = []
        
        for part in words:
            part = part.strip().lower()
            # Skip stop words and very short parts
            if len(part) > 2 and not any(sw in part for sw in stop_words):
                # Remove numbers at the beginning
                part = re.sub(r'^\d+\s*', '', part)
                if part:
                    cleaned_parts.append(part.title())
        
        return ', '.join(cleaned_parts[:3])  # Limit to 3 parts for clarity

class GeocodingClient:
    """Client for OpenStreetMap Nominatim geocoding service"""
    
    BASE_URL = "https://nominatim.openstreetmap.org/search"
    HEADERS = {
        "User-Agent": "PS1-Address-Intelligence-Hackathon/1.0 (educational-research)"
    }
    
    @staticmethod
    def geocode_query(query: str, limit: int = 5) -> List[Dict]:
        """
        Perform geocoding query using Nominatim
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            
        Returns:
            List of geocoding results
        """
        try:
            params = {
                "q": query,
                "format": "json",
                "addressdetails": 1,
                "limit": limit
            }
            
            response = requests.get(
                GeocodingClient.BASE_URL,
                params=params,
                headers=GeocodingClient.HEADERS,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Geocoding failed for query '{query}': {response.status_code}")
                return []
                
        except requests.exceptions.RequestException as e:
            print(f"Request error for query '{query}': {e}")
            return []
        except Exception as e:
            print(f"Unexpected error for query '{query}': {e}")
            return []

class CandidateRankingEngine:
    """Ranks geocoding candidates based on multiple factors"""
    
    @staticmethod
    def landmark_match_score(candidate_name: str, landmarks: List[Dict]) -> float:
        """
        Calculate how well candidate matches the landmarks
        
        Args:
            candidate_name: Display name from geocoding result
            landmarks: List of landmark dictionaries
            
        Returns:
            Score between 0.0 and 1.0
        """
        if not candidate_name or not landmarks:
            return 0.0
        
        score = 0.0
        candidate_lower = candidate_name.lower()
        
        # Check each landmark for matches
        for landmark in landmarks:
            landmark_text = landmark["landmark"].lower()
            
            # Direct match
            if landmark_text in candidate_lower:
                score += landmark["weight"]
            # Partial match (substring)
            elif any(word in candidate_lower for word in landmark_text.split()):
                score += landmark["weight"] * 0.5
        
        return min(score, 1.0)
    
    @staticmethod
    def score_candidate(candidate: Dict, query_index: int, context: Dict) -> float:
        """
        Calculate final score for a geocoding candidate
        
        Args:
            candidate: Geocoding result dictionary
            query_index: Index of the query that produced this candidate
            context: Original geocode context
            
        Returns:
            Final score between 0.0 and 1.0
        """
        display_name = candidate.get("display_name", "")
        osm_importance = float(candidate.get("importance", 0))
        
        # Landmark match score (30% weight)
        lm_score = CandidateRankingEngine.landmark_match_score(
            display_name, 
            context.get("landmarks", [])
        )
        
        # Pincode constraint (30% weight) - critical fix
        pincode_score = CandidateRankingEngine.pincode_score(candidate, context)
        
        # Locality match score (20% weight)
        locality_score = CandidateRankingEngine.locality_match_score(display_name, context)
        
        # Query position bonus (10% weight)
        # Earlier queries are more specific, so higher bonus
        query_bonus = max(0.0, 0.10 - query_index * 0.02)
        
        # OSM importance score (10% weight)
        # Normalize OSM importance (typically 0.0-0.5 range)
        osm_score = min(osm_importance * 2, 1.0)  # Scale to 0-1 range
        
        # Calculate weighted final score
        final_score = (
            0.30 * lm_score +
            0.30 * pincode_score +
            0.20 * locality_score +
            0.10 * query_bonus +
            0.10 * osm_score
        )
        
        return final_score  # Return actual score which can be negative for penalties
    
    @staticmethod
    def pincode_score(candidate: Dict, context: Dict) -> float:
        """
        Score based on pincode match - critical for location accuracy
        
        Args:
            candidate: Geocoding result dictionary
            context: Original geocode context
            
        Returns:
            Score: 1.0 if pincode matches, -1.0 if mismatches, 0.0 if not available
        """
        input_pincode = context.get("pincode", "").strip()
        if not input_pincode:
            return 0.0  # No pincode constraint to enforce
        
        # Extract pincode from candidate address
        candidate_pincode = ""
        if "address" in candidate and candidate["address"]:
            address = candidate["address"]
            # Look for various pincode/postcode fields
            for field in ["postcode", "postal_code", "zipcode"]:
                if field in address and address[field]:
                    candidate_pincode = str(address[field]).strip()
                    break
        
        if not candidate_pincode:
            # If no pincode found in candidate, but input has one, penalize slightly
            return -0.2
        
        # Normalize both pincodes for comparison (remove spaces, hyphens, etc.)
        input_normalized = ''.join(filter(str.isdigit, input_pincode))
        cand_normalized = ''.join(filter(str.isdigit, candidate_pincode))
        
        if input_normalized == cand_normalized:
            return 1.0  # Perfect match
        else:
            return -1.0  # Strong penalty for mismatch
    
    @staticmethod
    def locality_match_score(display_name: str, context: Dict) -> float:
        """
        Score based on locality and city match
        
        Args:
            display_name: Display name from geocoding result
            context: Original geocode context
            
        Returns:
            Score based on how many location tokens match
        """
        if not display_name:
            return 0.0
        
        # Collect location tokens from context
        tokens = []
        for key in ["locality", "city"]:
            if context.get(key):
                tokens.append(context[key].lower().strip())
        
        # Add landmark localities (like Versova, Andheri West from landmarks)
        landmarks = context.get("landmarks", [])
        for landmark in landmarks:
            # Add specific location-related landmarks
            if landmark.get("type") in ["LOCALITY", "ROAD_JUNCTION", "GOV"]:
                tokens.append(landmark["landmark"].lower().strip())
        
        # Add any additional locality tokens from context
        locality_tokens = context.get("locality_tokens", [])
        for token in locality_tokens:
            tokens.append(token.lower().strip())
        
        # Remove duplicates and empty strings
        tokens = [t for t in set(tokens) if t]
        
        if not tokens:
            return 0.0
        
        display_lower = display_name.lower()
        
        # Count how many tokens match
        matches = sum(1 for token in tokens if token and token in display_lower)
        
        # Return ratio of matches (0.0 to 1.0)
        return matches / len(tokens)
    
    @staticmethod
    def rank_candidates(all_candidates: List[Dict], context: Dict) -> List[Dict]:
        """
        Rank all candidates by their final scores
        
        Args:
            all_candidates: List of candidate dictionaries with query info
            context: Original geocode context
            
        Returns:
            List of ranked candidates with final scores
        """
        scored_candidates = []
        
        for candidate_data in all_candidates:
            candidate = candidate_data["candidate"]
            query_index = candidate_data["query_index"]
            
            # Calculate final score
            final_score = CandidateRankingEngine.score_candidate(
                candidate, 
                query_index, 
                context
            )
            
            # Add score to candidate
            scored_candidate = candidate.copy()
            scored_candidate["final_score"] = final_score
            scored_candidate["query_used"] = candidate_data["query"]
            scored_candidate["query_index"] = query_index
            
            scored_candidates.append(scored_candidate)
        
        # Sort by final score (descending) - higher scores first
        scored_candidates.sort(key=lambda x: x["final_score"], reverse=True)
        
        # Filter out candidates with very negative scores (strong penalties)
        # Only return candidates with scores > -0.5 to avoid completely wrong results
        filtered_candidates = [cand for cand in scored_candidates if cand["final_score"] > -0.5]
        
        return filtered_candidates

class GeocodingPipeline:
    """Main geocoding pipeline that orchestrates the entire process"""
    
    def __init__(self):
        self.query_builder = GeocodeQueryBuilder()
        self.client = GeocodingClient()
        self.ranker = CandidateRankingEngine()
    
    def geocode_address(self, context: Dict) -> Optional[Dict]:
        """
        Complete geocoding pipeline from context to GPS coordinates
        
        Args:
            context: Geocode context from landmark extractor
            
        Returns:
            Dictionary with geocoding result or None if no results found
        """
        # Step 1: Build queries
        queries = self.query_builder.build_geocode_queries(context)
        
        if not queries:
            # Fallback: create basic queries if none generated
            queries = self._create_fallback_queries(context)
            if not queries:
                return None
        
        # Step 2: Execute geocoding queries
        all_candidates = []
        
        for i, query in enumerate(queries):
            results = self.client.geocode_query(query, limit=5)  # Increased limit
            
            for result in results:
                all_candidates.append({
                    "query": query,
                    "query_index": i,
                    "candidate": result
                })
        
        # If no candidates found, try broader searches
        if not all_candidates:
            fallback_queries = self._create_broad_queries(context)
            for query in fallback_queries:
                results = self.client.geocode_query(query, limit=3)
                for result in results:
                    all_candidates.append({
                        "query": query,
                        "query_index": len(queries),  # Higher index for lower priority
                        "candidate": result
                    })
        
        if not all_candidates:
            return {
                "error": "No geocoding results found",
                "attempts": len(queries),
                "fallback_attempts": len(self._create_broad_queries(context)),
                "queries_tried": queries,
                "context_used": context
            }
        
        # Step 3: Rank candidates
        ranked_candidates = self.ranker.rank_candidates(all_candidates, context)
        
        # If no ranked candidates (all filtered out), return unranked best candidate
        if not ranked_candidates:
            # Sort by OSM importance as fallback
            unranked_candidates = sorted(
                all_candidates, 
                key=lambda x: float(x["candidate"].get("importance", 0)), 
                reverse=True
            )
            if unranked_candidates:
                best_candidate = unranked_candidates[0]["candidate"]
                return {
                    "latitude": float(best_candidate["lat"]),
                    "longitude": float(best_candidate["lon"]),
                    "formatted_address": best_candidate["display_name"],
                    "confidence": 0.1,  # Low confidence for fallback
                    "used_query": unranked_candidates[0]["query"],
                    "query_rank": unranked_candidates[0]["query_index"],
                    "osm_importance": float(best_candidate.get("importance", 0)),
                    "address_components": best_candidate.get("address", {}),
                    "alternatives": [],
                    "fallback_used": True,
                    "warning": "Low confidence result - using fallback ranking"
                }
            else:
                return {
                    "error": "No valid candidates after ranking",
                    "total_candidates": len(all_candidates),
                    "context_used": context
                }
        
        # Step 4: Return best result
        best_candidate = ranked_candidates[0]
        
        result = {
            "latitude": float(best_candidate["lat"]),
            "longitude": float(best_candidate["lon"]),
            "formatted_address": best_candidate["display_name"],
            "confidence": round(best_candidate["final_score"], 3),
            "used_query": best_candidate["query_used"],
            "query_rank": best_candidate["query_index"],
            "osm_importance": float(best_candidate.get("importance", 0)),
            "address_components": best_candidate.get("address", {}),
            "alternatives": ranked_candidates[1:3]  # Top 2 alternatives
        }
        
        return result
    
    def _create_fallback_queries(self, context: Dict) -> List[str]:
        """Create basic fallback queries when normal query building fails"""
        queries = []
        
        # Basic city + state query
        city = context.get("city", "").strip()
        state = context.get("state", "").strip()
        pincode = context.get("pincode", "").strip()
        
        if city:
            query = f"{city}"
            if state:
                query += f", {state}"
            if pincode:
                query += f", {pincode}"
            query += ", India"
            queries.append(query)
        
        # Pincode only query
        if pincode:
            queries.append(f"{pincode}, India")
        
        return queries
    
    def _create_broad_queries(self, context: Dict) -> List[str]:
        """Create very broad search queries as last resort"""
        queries = []
        
        # Try just the city
        city = context.get("city", "").strip()
        if city:
            queries.append(f"{city}, India")
        
        # Try state
        state = context.get("state", "").strip()
        if state:
            queries.append(f"{state}, India")
        
        # Try major metropolitan areas
        queries.extend([
            "Mumbai, Maharashtra, India",
            "Delhi, India",
            "Bangalore, Karnataka, India",
            "Chennai, Tamil Nadu, India",
            "Kolkata, West Bengal, India"
        ])
        
        return list(set(queries))  # Remove duplicates
    
    def batch_geocode(self, contexts: List[Dict]) -> List[Dict]:
        """
        Geocode multiple addresses in batch
        
        Args:
            contexts: List of geocode contexts
            
        Returns:
            List of geocoding results (None for failed geocodes)
        """
        results = []
        for context in contexts:
            result = self.geocode_address(context)
            results.append(result)
        return results

# Example usage and testing
if __name__ == "__main__":
    # Test with the example context from the specification
    test_context = {
        "building": "Sai Prasad",
        "house": "Mahesh 202",
        "locality": "Gaulwada",
        "city": "Vasai West",
        "state": "",
        "pincode": "",
        "landmarks": [
            {"relation": "at", "landmark": "Suruchi Road", "type": "ROAD", "weight": 0.7},
            {"relation": "at", "landmark": "Gaulwada", "type": "LOCALITY", "weight": 0.8}
        ],
        "raw_text": "sai prasad, mahesh 202, gaulwada, vasai west, suruchi road"
    }
    
    # Initialize pipeline
    pipeline = GeocodingPipeline()
    
    print("=== Geocoding Pipeline Test ===")
    print(f"Input context: {test_context}")
    
    # Run geocoding
    result = pipeline.geocode_address(test_context)
    
    if result:
        print("\n✅ Geocoding Successful!")
        print(f"Latitude: {result['latitude']}")
        print(f"Longitude: {result['longitude']}")
        print(f"Formatted Address: {result['formatted_address']}")
        print(f"Confidence: {result['confidence']}")
        print(f"Used Query: {result['used_query']}")
        print(f"OSM Importance: {result['osm_importance']}")
        
        if result['alternatives']:
            print(f"\nTop Alternatives:")
            for i, alt in enumerate(result['alternatives'], 1):
                print(f"  {i}. {alt['display_name']} (score: {round(alt['final_score'], 3)})")
    else:
        print("\n❌ Geocoding Failed - No results found")