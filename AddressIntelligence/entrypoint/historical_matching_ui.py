import streamlit as st
import requests
import json
import pandas as pd
import folium
from streamlit_folium import st_folium
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# API Configuration
API_BASE_URL = "http://localhost:8002"

def call_api(endpoint: str, method: str = "GET", data: dict = None, params: dict = None):
    """Generic API call function"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url, params=params, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error {response.status_code}: {response.text}")
            return None
    except Exception as e:
        st.error(f"Connection error: {str(e)}")
        return None

def main():
    st.set_page_config(
        page_title="Historical Address Matching",
        page_icon="🏢",
        layout="wide"
    )
    
    st.title("🔍 Historical Address Matching")
    st.subheader("Predict locations using historical delivery dataset")
    
    # Check API health
    health = call_api("/health")
    if health:
        status_emoji = "✅" if health["status"] == "healthy" else "⚠️"
        st.sidebar.success(f"{status_emoji} API Status: {health['status']}")
        st.sidebar.info(f"Dataset loaded: {'Yes' if health['dataset_loaded'] else 'No'}")
    else:
        st.sidebar.error("❌ API Connection Failed")
        st.warning("Please ensure the FastAPI backend is running on port 8002")
        return
    
    # Tabs for different functionalities
    tab1, tab2, tab3, tab4 = st.tabs(["📍 Location Prediction", "📊 Top Matches", "🌍 Reverse Geocode", "📈 Dataset Stats"])
    
    with tab1:
        st.header("📍 Location Prediction")
        
        # Dataset loading section
        with st.expander("📂 Load Dataset (if not already loaded)"):
            col1, col2 = st.columns(2)
            with col1:
                dataset_path = st.text_input("Dataset Path", "indore_delivery_events_3000.csv")
                if st.button("Load Dataset"):
                    result = call_api("/load_dataset", "POST", {"dataset_path": dataset_path})
                    if result:
                        st.success(result["message"])
            
            with col2:
                pincode_path = st.text_input("Pincode Mapping Path", "indore_locality_pincode.csv")
                if st.button("Load Pincode Mapping"):
                    result = call_api("/load_pincode_mapping", "POST", {"pincode_path": pincode_path})
                    if result:
                        st.success(result["message"])
        
        # Prediction section
        st.subheader("Enter Address for Prediction")
        address_input = st.text_area(
            "Address:",
            placeholder="e.g., chai tapri ke piche gate",
            height=100
        )
        
        col1, col2 = st.columns([1, 2])
        with col1:
            k_value = st.slider("Number of matches (k)", 1, 20, 5)
        
        if st.button("🔍 Predict Location", type="primary") and address_input:
            with st.spinner("Predicting location..."):
                result = call_api("/predict_location", "POST", {
                    "address": address_input,
                    "k": k_value
                })
                
                if result:
                    st.success("✅ Prediction successful!")
                    
                    # Display results
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("City", result["predicted_city"])
                    with col2:
                        st.metric("Locality", result["predicted_locality"])
                    with col3:
                        st.metric("Confidence", f"{result['confidence']:.2f}")
                    with col4:
                        st.metric("Pincode", result["predicted_pincode"] or "N/A")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Latitude", f"{result['predicted_lat']:.6f}")
                    with col2:
                        st.metric("Longitude", f"{result['predicted_lng']:.6f}")
                    
                    # Map visualization
                    st.subheader("📍 Predicted Location")
                    m = folium.Map(
                        location=[result['predicted_lat'], result['predicted_lng']],
                        zoom_start=15
                    )
                    folium.Marker(
                        [result['predicted_lat'], result['predicted_lng']],
                        popup=f"Predicted: {result['predicted_locality']}",
                        tooltip="Predicted Location"
                    ).add_to(m)
                    st_folium(m, width=700, height=400)
                    
                    # Top matches table
                    st.subheader("🏆 Top Similar Historical Addresses")
                    matches_df = pd.DataFrame(result["top_matches"])
                    st.dataframe(
                        matches_df[["raw_address", "locality", "similarity"]].style
                        .format({"similarity": "{:.3f}"})
                        .background_gradient(cmap="Blues", subset=["similarity"]),
                        use_container_width=True
                    )
                    
                    # Download JSON
                    json_str = json.dumps(result, indent=2)
                    st.download_button(
                        "📥 Download Full Results (JSON)",
                        json_str,
                        "prediction_results.json",
                        "application/json"
                    )
    
    with tab2:
        st.header("📊 Top Matches Explorer")
        
        search_address = st.text_input("Search Address:", placeholder="Enter address to find similar historical records")
        num_matches = st.slider("Number of matches:", 1, 20, 10)
        
        if st.button("🔍 Find Matches") and search_address:
            with st.spinner("Searching matches..."):
                matches = call_api("/top_matches", "GET", params={
                    "address": search_address,
                    "k": num_matches
                })
                
                if matches:
                    st.success(f"Found {len(matches)} matches")
                    
                    # Display matches
                    matches_df = pd.DataFrame(matches)
                    st.dataframe(
                        matches_df.style
                        .format({"similarity": "{:.3f}", "lat": "{:.6f}", "lng": "{:.6f}"})
                        .background_gradient(cmap="Greens", subset=["similarity"]),
                        use_container_width=True
                    )
                    
                    # Map of all matches
                    if not matches_df.empty:
                        center_lat = matches_df["lat"].mean()
                        center_lng = matches_df["lng"].mean()
                        
                        m = folium.Map(location=[center_lat, center_lng], zoom_start=13)
                        
                        for _, row in matches_df.iterrows():
                            folium.Marker(
                                [row["lat"], row["lng"]],
                                popup=f"{row['raw_address']}<br>Locality: {row['locality']}<br>Similarity: {row['similarity']:.3f}",
                                tooltip=f"{row['locality']} ({row['similarity']:.3f})"
                            ).add_to(m)
                        
                        st_folium(m, width=700, height=500)
    
    with tab3:
        st.header("🌍 Reverse Geocode")
        st.info("Get pincode from GPS coordinates")
        
        col1, col2 = st.columns(2)
        with col1:
            lat_input = st.number_input("Latitude", value=22.7196, format="%.6f")
        with col2:
            lng_input = st.number_input("Longitude", value=75.8577, format="%.6f")
        
        if st.button("🔍 Get Pincode"):
            with st.spinner("Reverse geocoding..."):
                result = call_api("/reverse_geocode", "GET", params={
                    "lat": lat_input,
                    "lng": lng_input
                })
                
                if result:
                    st.success("✅ Reverse geocoding successful!")
                    st.metric("Pincode", result["pincode"])
                    
                    # Show location on map
                    m = folium.Map(location=[lat_input, lng_input], zoom_start=15)
                    folium.Marker(
                        [lat_input, lng_input],
                        popup=f"Coordinates: {lat_input:.6f}, {lng_input:.6f}<br>Pincode: {result['pincode']}",
                        tooltip="Location"
                    ).add_to(m)
                    st_folium(m, width=700, height=400)
    
    with tab4:
        st.header("📈 Dataset Statistics")
        
        if st.button("📊 Get Dataset Stats"):
            with st.spinner("Loading statistics..."):
                stats = call_api("/dataset_stats", "GET")
                
                if stats:
                    st.success("Dataset statistics loaded!")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Records", stats["total_records"])
                    with col2:
                        st.metric("Unique Cities", stats["unique_cities"])
                    with col3:
                        st.metric("Unique Localities", stats["unique_localities"])
                    
                    # City distribution
                    st.subheader("🏙️ Top Cities")
                    city_df = pd.DataFrame(list(stats["cities"].items()), columns=["City", "Count"])
                    st.bar_chart(city_df.set_index("City"))
                    
                    # Sample records
                    st.subheader("📝 Sample Records")
                    sample_df = pd.DataFrame(stats["sample_records"])
                    st.dataframe(sample_df, use_container_width=True)
    
    # Information sidebar
    st.sidebar.header("ℹ️ About")
    st.sidebar.info("""
    This application uses historical delivery data to:
    
    🔍 **Predict locations** from partial addresses
    📊 **Find similar** historical deliveries  
    🌍 **Reverse geocode** coordinates to pincode
    📈 **Analyze dataset** statistics
    
    **Key Features:**
    - Hinglish address support
    - Similarity-based matching
    - Confidence scoring
    - Interactive maps
    - JSON export capabilities
    """)
    
    st.sidebar.header("📁 Required Files")
    st.sidebar.code("""
    indore_delivery_events_3000.csv
    - order_id, city, locality, raw_address
    - lat, lng, status
    
    indore_locality_pincode.csv (optional)
    - locality, pincode
    """)

if __name__ == "__main__":
    main()