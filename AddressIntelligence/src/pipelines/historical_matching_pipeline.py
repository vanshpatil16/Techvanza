import pandas as pd
import numpy as np
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import Dict, List, Optional, Tuple
import json
import os

class HistoricalMatchingPipeline:
    """Historical delivery dataset matching for address prediction"""
    
    def __init__(self, dataset_path: str = None):
        """Initialize the pipeline with historical dataset"""
        self.df = None
        self.vectorizer = None
        self.X = None
        self.pincode_map = {}
        
        # Hinglish to English mapping
        self.hinglish_map = {
            "ke paas": "near",
            "paas": "near", 
            "pass": "near",
            "ke peeche": "behind",
            "peeche": "behind",
            "piche": "behind",
            "ke samne": "opposite",
            "samne": "opposite",
            "saamne": "opposite",
            "gali": "lane",
            "tapri": "stall",
            "chai": "tea",
            "dukaan": "shop",
            "bada": "big",
            "ped": "tree",
            "mohalla": "area",
            "colony": "colony",
            "nagar": "nagar",
            "road": "road",
            "marg": "road",
            "path": "road"
        }
        
        if dataset_path and os.path.exists(dataset_path):
            self.load_dataset(dataset_path)
    
    def normalize_address(self, text: str) -> str:
        """Normalize address text with Hinglish conversion"""
        if not isinstance(text, str):
            return ""
        
        text = text.lower()
        # Remove special characters
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()
        
        # Replace Hinglish phrases
        for k, v in self.hinglish_map.items():
            text = text.replace(k, v)
        
        return text
    
    def load_dataset(self, dataset_path: str):
        """Load and preprocess the historical delivery dataset"""
        print(f"Loading dataset from {dataset_path}")
        self.df = pd.read_csv(dataset_path)
        print(f"Dataset shape: {self.df.shape}")
        
        # Clean dataset
        self.df = self.df.dropna(subset=["raw_address", "locality", "lat", "lng"])
        self.df["raw_address"] = self.df["raw_address"].astype(str)
        self.df["locality"] = self.df["locality"].astype(str)
        self.df["city"] = self.df["city"].astype(str)
        
        # Normalize addresses
        print("Normalizing addresses...")
        self.df["norm_address"] = self.df["raw_address"].apply(self.normalize_address)
        
        # Create TF-IDF vectors
        print("Creating TF-IDF vectors...")
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=2)
        self.X = self.vectorizer.fit_transform(self.df["norm_address"])
        
        print("Dataset loaded and processed successfully!")
    
    def load_pincode_mapping(self, pincode_path: str):
        """Load locality to pincode mapping"""
        if os.path.exists(pincode_path):
            pincode_df = pd.read_csv(pincode_path)
            self.pincode_map = dict(zip(pincode_df["locality"], pincode_df["pincode"]))
            print(f"Loaded {len(self.pincode_map)} locality-pincode mappings")
    
    def get_top_matches(self, input_address: str, k: int = 5) -> pd.DataFrame:
        """Find top-k similar addresses from historical dataset"""
        if self.df is None or self.vectorizer is None:
            raise ValueError("Dataset not loaded. Call load_dataset() first.")
        
        # Normalize input
        norm_input = self.normalize_address(input_address)
        if not norm_input:
            return pd.DataFrame()
        
        # Vectorize input
        q_vec = self.vectorizer.transform([norm_input])
        
        # Calculate similarities
        sims = cosine_similarity(q_vec, self.X).flatten()
        top_idx = np.argsort(sims)[::-1][:k]
        
        # Get matches with similarity scores
        matches = self.df.iloc[top_idx].copy()
        matches["similarity"] = sims[top_idx]
        
        return matches
    
    def predict_location(self, input_address: str, k: int = 5) -> Dict:
        """Predict location, locality, and coordinates from historical matches"""
        matches = self.get_top_matches(input_address, k=k)
        
        if matches.empty:
            return {
                "error": "No matches found in historical dataset",
                "predicted_city": None,
                "predicted_locality": None,
                "predicted_lat": None,
                "predicted_lng": None,
                "confidence": 0.0,
                "top_matches": []
            }
        
        # Weighted locality voting
        locality_scores = {}
        for _, row in matches.iterrows():
            locality = row["locality"]
            similarity = row["similarity"]
            locality_scores[locality] = locality_scores.get(locality, 0) + similarity
        
        # Predicted locality (highest weighted vote)
        pred_locality = max(locality_scores, key=locality_scores.get)
        
        # Weighted average coordinates
        sims = matches["similarity"].values
        pred_lat = np.average(matches["lat"].values, weights=sims)
        pred_lng = np.average(matches["lng"].values, weights=sims)
        
        # Confidence calculation
        top_sim = matches["similarity"].iloc[0]
        agreement = (matches["locality"] == pred_locality).sum() / len(matches)
        confidence = round(0.6 * top_sim + 0.4 * agreement, 2)
        
        # Predict city (mode of top matches)
        pred_city = matches["city"].mode()[0] if not matches["city"].mode().empty else "Unknown"
        
        # Get pincode if mapping exists
        pred_pincode = self.pincode_map.get(pred_locality, "")
        
        return {
            "predicted_city": pred_city,
            "predicted_locality": pred_locality,
            "predicted_lat": float(pred_lat),
            "predicted_lng": float(pred_lng),
            "predicted_pincode": pred_pincode,
            "confidence": confidence,
            "top_matches": matches[["raw_address", "locality", "lat", "lng", "similarity"]].to_dict("records")
        }
    
    def reverse_geocode_pincode(self, lat: float, lng: float) -> Optional[str]:
        """Reverse geocode coordinates to get pincode (using external API)"""
        try:
            import requests
            url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json&addressdetails=1"
            headers = {"User-Agent": "Historical-Address-Matching/1.0"}
            
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get("address", {}).get("postcode", "")
        except Exception as e:
            print(f"Reverse geocoding failed: {e}")
        return None
    
    def get_dataset_stats(self) -> Dict:
        """Get statistics about the loaded dataset"""
        if self.df is None:
            return {"error": "No dataset loaded"}
        
        return {
            "total_records": len(self.df),
            "unique_cities": self.df["city"].nunique(),
            "unique_localities": self.df["locality"].nunique(),
            "cities": self.df["city"].value_counts().head(10).to_dict(),
            "sample_records": self.df[["city", "locality", "raw_address"]].head(3).to_dict("records")
        }

# Example usage
if __name__ == "__main__":
    # This would be used when you have the actual dataset
    # pipeline = HistoricalMatchingPipeline("indore_delivery_events_3000.csv")
    # result = pipeline.predict_location("chai tapri ke piche gate")
    # print(json.dumps(result, indent=2))
    pass