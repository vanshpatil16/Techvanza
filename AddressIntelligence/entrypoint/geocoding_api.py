from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
from src.pipelines.geocoding_pipeline import GeocodingPipeline

# Initialize FastAPI app
app = FastAPI(
    title="PS1 Geocoding API",
    description="Landmark-based geocoding service for Tier 2/3 Indian addresses",
    version="1.0.0"
)

# Initialize geocoding pipeline
geocoder = GeocodingPipeline()

# Pydantic models for request/response
class Landmark(BaseModel):
    relation: str
    landmark: str
    type: str
    weight: float

class GeocodeContext(BaseModel):
    building: Optional[str] = ""
    house: Optional[str] = ""
    locality: Optional[str] = ""
    city: Optional[str] = ""
    state: Optional[str] = ""
    pincode: Optional[str] = ""
    landmarks: List[Landmark] = []
    raw_text: str

class GeocodeResult(BaseModel):
    latitude: float
    longitude: float
    formatted_address: str
    confidence: float
    used_query: str
    query_rank: int
    osm_importance: float
    address_components: Dict[str, Any]
    alternatives: List[Dict[str, Any]]

class GeocodeResponse(BaseModel):
    status: str
    result: Optional[GeocodeResult] = None
    message: Optional[str] = None

class BatchGeocodeRequest(BaseModel):
    contexts: List[GeocodeContext]

class BatchGeocodeResponse(BaseModel):
    status: str
    results: List[Optional[GeocodeResult]]
    message: Optional[str] = None

# API Endpoints
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "PS1 Geocoding API is running",
        "version": "1.0.0",
        "status": "healthy"
    }

@app.post("/geocode", response_model=GeocodeResponse)
async def geocode_address(context: GeocodeContext):
    """
    Geocode a single address using landmark context
    
    Args:
        context: Geocode context with landmarks and address components
        
    Returns:
        Geocoding result with GPS coordinates and confidence score
    """
    try:
        # Convert Pydantic model to dictionary
        context_dict = context.dict()
        # Convert landmarks to dictionaries
        context_dict["landmarks"] = [lm.dict() for lm in context.landmarks]
        
        # Run geocoding
        result = geocoder.geocode_address(context_dict)
        
        if not result:
            return GeocodeResponse(
                status="fail",
                message="No location found for the given address"
            )
        
        # Convert result to Pydantic model
        geocode_result = GeocodeResult(**result)
        
        return GeocodeResponse(
            status="success",
            result=geocode_result
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Geocoding failed: {str(e)}"
        )

@app.post("/batch-geocode", response_model=BatchGeocodeResponse)
async def batch_geocode(request: BatchGeocodeRequest):
    """
    Geocode multiple addresses in batch
    
    Args:
        request: Contains list of geocode contexts
        
    Returns:
        List of geocoding results
    """
    try:
        # Convert contexts to dictionaries
        contexts = []
        for context in request.contexts:
            context_dict = context.dict()
            context_dict["landmarks"] = [lm.dict() for lm in context.landmarks]
            contexts.append(context_dict)
        
        # Run batch geocoding
        results = geocoder.batch_geocode(contexts)
        
        # Convert results to Pydantic models where applicable
        formatted_results = []
        for result in results:
            if result:
                formatted_results.append(GeocodeResult(**result))
            else:
                formatted_results.append(None)
        
        return BatchGeocodeResponse(
            status="success",
            results=formatted_results
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Batch geocoding failed: {str(e)}"
        )

@app.get("/confidence/{score}")
async def interpret_confidence(score: float):
    """
    Interpret confidence score for UI/display purposes
    
    Args:
        score: Confidence score between 0.0 and 1.0
        
    Returns:
        Interpretation of the confidence level
    """
    if not 0 <= score <= 1:
        raise HTTPException(
            status_code=400,
            detail="Score must be between 0.0 and 1.0"
        )
    
    if score >= 0.85:
        interpretation = "Safe to dispatch"
        color = "green"
    elif score >= 0.60:
        interpretation = "Likely correct"
        color = "yellow"
    elif score >= 0.45:
        interpretation = "Verify with user"
        color = "orange"
    else:
        interpretation = "Ambiguous"
        color = "red"
    
    return {
        "confidence": score,
        "interpretation": interpretation,
        "color": color,
        "recommendation": interpretation
    }

# Example data for testing
@app.get("/examples")
async def get_examples():
    """Return example contexts for testing"""
    examples = [
        {
            "name": "Suruchi Road Example",
            "context": {
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
        },
        {
            "name": "Temple Near Example",
            "context": {
                "building": "",
                "house": "",
                "locality": "Dadar",
                "city": "Mumbai",
                "state": "Maharashtra",
                "pincode": "",
                "landmarks": [
                    {"relation": "near", "landmark": "Hanuman Mandir", "type": "RELIGIOUS", "weight": 0.7},
                    {"relation": "opposite", "landmark": "Police Station", "type": "GOV", "weight": 0.9}
                ],
                "raw_text": "near hanuman mandir, opposite police station, dadar, mumbai"
            }
        }
    ]
    
    return {"examples": examples}

if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "geocoding_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )