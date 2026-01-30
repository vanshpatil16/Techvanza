from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.pipelines.historical_matching_pipeline import HistoricalMatchingPipeline

app = FastAPI(
    title="Historical Address Matching API",
    description="Predict locations using historical delivery dataset matching",
    version="1.0.0"
)

# Global pipeline instance
pipeline = None

# Request/Response Models
class AddressRequest(BaseModel):
    address: str
    k: int = 5  # Number of top matches to consider

class LocationPrediction(BaseModel):
    predicted_city: str
    predicted_locality: str
    predicted_lat: float
    predicted_lng: float
    predicted_pincode: str
    confidence: float
    top_matches: List[Dict[str, Any]]

class MatchResult(BaseModel):
    raw_address: str
    locality: str
    lat: float
    lng: float
    similarity: float

class DatasetStats(BaseModel):
    total_records: int
    unique_cities: int
    unique_localities: int
    cities: Dict[str, int]
    sample_records: List[Dict[str, str]]

class HealthResponse(BaseModel):
    status: str
    dataset_loaded: bool
    pipeline_ready: bool

# Initialize pipeline on startup
@app.on_event("startup")
async def startup_event():
    global pipeline
    try:
        # Initialize pipeline (dataset path would be configured)
        pipeline = HistoricalMatchingPipeline()
        print("Historical matching pipeline initialized")
    except Exception as e:
        print(f"Failed to initialize pipeline: {e}")
        pipeline = None

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check if the API is running and pipeline is loaded"""
    return HealthResponse(
        status="healthy" if pipeline else "degraded",
        dataset_loaded=pipeline is not None and pipeline.df is not None,
        pipeline_ready=pipeline is not None
    )

@app.post("/predict_location", response_model=LocationPrediction)
async def predict_location(request: AddressRequest):
    """Predict location, coordinates, and pincode from historical matches"""
    if not pipeline:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    try:
        result = pipeline.predict_location(request.address, k=request.k)
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return LocationPrediction(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.get("/top_matches", response_model=List[MatchResult])
async def get_top_matches(
    address: str = Query(..., description="Input address to match"),
    k: int = Query(5, description="Number of matches to return", ge=1, le=20)
):
    """Get top-k similar addresses from historical dataset"""
    if not pipeline:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    try:
        matches = pipeline.get_top_matches(address, k=k)
        if matches.empty:
            return []
        
        results = []
        for _, row in matches.iterrows():
            results.append(MatchResult(
                raw_address=row["raw_address"],
                locality=row["locality"],
                lat=float(row["lat"]),
                lng=float(row["lng"]),
                similarity=float(row["similarity"])
            ))
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Matching failed: {str(e)}")

@app.get("/reverse_geocode")
async def reverse_geocode(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude")
):
    """Reverse geocode coordinates to get pincode"""
    if not pipeline:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    try:
        pincode = pipeline.reverse_geocode_pincode(lat, lng)
        return {
            "latitude": lat,
            "longitude": lng,
            "pincode": pincode if pincode else "Not found"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reverse geocoding failed: {str(e)}")

@app.get("/dataset_stats", response_model=DatasetStats)
async def get_dataset_stats():
    """Get statistics about the loaded historical dataset"""
    if not pipeline:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    try:
        stats = pipeline.get_dataset_stats()
        if "error" in stats:
            raise HTTPException(status_code=404, detail=stats["error"])
        
        return DatasetStats(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@app.post("/load_dataset")
async def load_dataset(request: dict):
    """Load historical dataset from file path"""
    global pipeline
    try:
        dataset_path = request.get("dataset_path")
        if not dataset_path:
            raise HTTPException(status_code=400, detail="dataset_path is required")
            
        if pipeline is None:
            pipeline = HistoricalMatchingPipeline()
        
        pipeline.load_dataset(dataset_path)
        return {"message": "Dataset loaded successfully", "dataset_path": dataset_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load dataset: {str(e)}")

@app.post("/load_pincode_mapping")
async def load_pincode_mapping(request: dict):
    """Load locality to pincode mapping file"""
    global pipeline
    try:
        pincode_path = request.get("pincode_path")
        if not pincode_path:
            raise HTTPException(status_code=400, detail="pincode_path is required")
            
        if pipeline is None:
            raise HTTPException(status_code=503, detail="Pipeline not initialized")
        
        pipeline.load_pincode_mapping(pincode_path)
        return {"message": "Pincode mapping loaded successfully", "mapping_path": pincode_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load pincode mapping: {str(e)}")

# Example endpoint for testing
@app.get("/")
async def root():
    return {
        "message": "Historical Address Matching API",
        "endpoints": [
            "POST /predict_location - Predict location from address",
            "GET /top_matches - Get similar historical addresses",
            "GET /reverse_geocode - Get pincode from coordinates",
            "GET /dataset_stats - Get dataset statistics",
            "POST /load_dataset - Load historical dataset",
            "POST /load_pincode_mapping - Load pincode mapping",
            "GET /health - Check API health"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)