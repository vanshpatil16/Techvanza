from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.pipelines.landmark_extraction_pipeline import LandmarkExtractor
from src.pipelines.geocoding_pipeline import GeocodingPipeline

app = FastAPI(
    title="Landmark Geocoding API",
    description="API for extracting landmarks from addresses and geocoding with improved accuracy",
    version="1.0.0"
)

# Request/Response Models
class AddressRequest(BaseModel):
    address: str
    method: str = "rule_based"  # "rule_based" or "spacy_matcher"

class Landmark(BaseModel):
    relation: str
    landmark: str
    type: str
    weight: float

class GeocodingResult(BaseModel):
    latitude: float
    longitude: float
    formatted_address: str
    confidence: float
    used_query: str
    pincode: Optional[str]
    landmarks: List[Landmark]
    landmark_extraction_method: str

class BatchAddressRequest(BaseModel):
    addresses: List[str]
    method: str = "rule_based"

class HealthResponse(BaseModel):
    status: str
    landmark_extractor: str
    geocoding_pipeline: str

# Initialize pipelines
landmark_extractor = LandmarkExtractor()
geocoding_pipeline = GeocodingPipeline()

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check if the API is running and pipelines are loaded"""
    return HealthResponse(
        status="healthy",
        landmark_extractor="loaded",
        geocoding_pipeline="loaded"
    )

@app.post("/extract-landmarks", response_model=Dict[str, Any])
async def extract_landmarks(request: AddressRequest):
    """Extract landmarks from an address"""
    try:
        if request.method == "spacy_matcher":
            result = landmark_extractor.extract_with_spacy_matcher(request.address)
        else:
            result = landmark_extractor.extract_landmarks(request.address)
        
        return {
            "address": request.address,
            "landmarks": result["landmarks"],
            "total_landmarks": result["total_landmarks"],
            "additional_directions": result["additional_directions"],
            "method": result.get("method", "rule_based")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Landmark extraction failed: {str(e)}")

@app.post("/geocode-with-landmarks", response_model=GeocodingResult)
async def geocode_with_landmarks(request: AddressRequest):
    """Extract landmarks and geocode in one step"""
    try:
        # Step 1: Extract landmarks
        if request.method == "spacy_matcher":
            landmark_result = landmark_extractor.extract_with_spacy_matcher(request.address)
        else:
            landmark_result = landmark_extractor.extract_landmarks(request.address)
        
        # Step 2: Extract pincode from address
        import re
        pincode_match = re.search(r'\b(\d{6})\b', request.address)
        pincode = pincode_match.group(1) if pincode_match else ""
        
        # Step 3: Extract city
        city = "Mumbai" if "mumbai" in request.address.lower() or "mumbra" in request.address.lower() else ""
        if not city:
            city_match = re.search(r',\s*([A-Za-z\s]+)(?:\s*-\s*\d{6}|$)', request.address)
            if city_match:
                city = city_match.group(1).strip()
        
        # Step 4: Extract locality tokens
        words = request.address.split(',')
        locality_tokens = []
        for word in words:
            word = word.strip()
            potential_tokens = word.split()
            for token in potential_tokens:
                token = token.strip().strip('-')
                if (token and len(token) > 3 and token[0].isupper() and 
                    token.lower() not in ['near', 'behind', 'opposite', 'after', 'before', 'mumbai', 'mumbra']):
                    if token not in locality_tokens:
                        locality_tokens.append(token)
        
        # Step 5: Prepare context for geocoding
        context = {
            "building": "",
            "house": "",
            "locality": "",
            "city": city,
            "state": "",
            "pincode": pincode,
            "landmarks": landmark_result["landmarks"],
            "raw_text": request.address,
            "locality_tokens": locality_tokens
        }
        
        # Step 6: Geocode the address
        geocoding_result = geocoding_pipeline.geocode_address(context)
        
        if not geocoding_result:
            raise HTTPException(status_code=404, detail="Geocoding failed - no results found")
        
        # Convert landmarks to Pydantic models
        landmarks = [
            Landmark(
                relation=lm["relation"],
                landmark=lm["landmark"],
                type=lm["type"],
                weight=lm["weight"]
            )
            for lm in landmark_result["landmarks"]
        ]
        
        return GeocodingResult(
            latitude=geocoding_result["latitude"],
            longitude=geocoding_result["longitude"],
            formatted_address=geocoding_result["formatted_address"],
            confidence=geocoding_result["confidence"],
            used_query=geocoding_result["used_query"],
            pincode=geocoding_result["address_components"].get("postcode", ""),
            landmarks=landmarks,
            landmark_extraction_method=request.method
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Landmark geocoding failed: {str(e)}")

@app.post("/batch-geocode-with-landmarks", response_model=List[Dict[str, Any]])
async def batch_geocode_with_landmarks(request: BatchAddressRequest):
    """Batch process multiple addresses with landmark extraction and geocoding"""
    results = []
    
    for address in request.addresses:
        try:
            # Process each address
            addr_request = AddressRequest(address=address, method=request.method)
            result = await geocode_with_landmarks(addr_request)
            
            results.append({
                "address": address,
                "success": True,
                "result": result
            })
        except Exception as e:
            results.append({
                "address": address,
                "success": False,
                "error": str(e)
            })
    
    return results

@app.post("/geocode-context", response_model=Dict[str, Any])
async def geocode_context_only(context: Dict[str, Any]):
    """Geocode using a pre-prepared context (for advanced usage)"""
    try:
        result = geocoding_pipeline.geocode_address(context)
        
        if not result:
            raise HTTPException(status_code=404, detail="Geocoding failed - no results found")
        
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Geocoding failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)