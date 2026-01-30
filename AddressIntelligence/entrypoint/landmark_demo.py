import sys
import os

# Add the parent directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

import streamlit as st
from src.pipelines.landmark_extraction_pipeline import LandmarkExtractor

def main():
    st.set_page_config(
        page_title="Landmark Extraction Demo",
        page_icon="📍",
        layout="wide"
    )
    
    st.title("📍 Landmark Extraction Pipeline")
    st.markdown("""
    **PS1 Landmark Extraction Demo** - Extract structured landmark information from Indian addresses
    
    This demo showcases the enhanced landmark extraction pipeline that powers Tier 2/3 address parsing by identifying:
    - **Relations**: near, opposite, behind, after, etc. (with new "at" for standalone landmarks)
    - **Landmarks**: temples, schools, police stations, shops, roads, parks, beaches, malls
    - **Types**: RELIGIOUS, GOV, EDUCATION, HEALTH, SHOP, MALL, PARK, BEACH, ROAD, ROAD_JUNCTION, etc.
    - **Weights**: Importance ranking for geocoding (0.3-0.9)
    
    **✨ New Feature**: Now handles standalone landmarks like "Suruchi Road" without requiring relation words!
    """)
    
    # Initialize extractor
    @st.cache_resource
    def load_extractor():
        return LandmarkExtractor()
    
    extractor = load_extractor()
    
    # Example addresses
    example_addresses = {
        "Basic Example": "Near Hanuman Mandir, after chai tapri, opposite Nagar Parishad office, lane behind big tree",
        "Hinglish Example": "ke paas mandir hai, ke peeche school hai, opp police station",
        "Abbreviated": "opp Nagar Parishad office, nr temple, behind reliance mart",
        "Chained Landmarks": "near temple behind school opposite bank",
        "Standalone Road": "sai prasad,mahesh 202 ,gaulwada,vasai west,suruchi road",
        "Mixed Address": "Flat 101, Sun Tower, MG Road, nr Tech Park, behind HDFC Bank, Bangalore",
        "Beach & Park": "near central park, opposite marine drive beach, behind phoenix mall"
    }
    
    st.sidebar.header("🎯 Try Examples")
    
    # Example selection
    selected_example = st.sidebar.selectbox(
        "Choose an example:",
        list(example_addresses.keys())
    )
    
    # Input area
    user_input = st.text_area(
        "Enter address text:",
        value=example_addresses[selected_example],
        height=100,
        help="Enter any Indian address with landmark references"
    )
    
    # Extraction method selection
    method = st.radio(
        "Extraction Method:",
        ["Rule-based (Fast)", "spaCy Matcher (AI-powered)"],
        horizontal=True
    )
    
    if st.button("📍 Extract Landmarks", type="primary"):
        if user_input.strip():
            with st.spinner("Extracting landmarks..."):
                # Choose extraction method
                if method == "Rule-based (Fast)":
                    result = extractor.extract_landmarks(user_input)
                else:
                    result = extractor.extract_with_spacy_matcher(user_input)
            
            # Display results
            st.subheader("📊 Extraction Results")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total Landmarks Found", result["total_landmarks"])
                st.metric("Additional Directions", len(result["additional_directions"]))
            
            with col2:
                if result["landmarks"]:
                    avg_weight = sum(lm["weight"] for lm in result["landmarks"]) / len(result["landmarks"])
                    st.metric("Average Weight", f"{avg_weight:.2f}")
            
            # Display landmarks table
            if result["landmarks"]:
                st.subheader("📍 Extracted Landmarks")
                
                # Prepare data for display
                display_data = []
                for lm in result["landmarks"]:
                    display_data.append({
                        "Relation": lm["relation"].title(),
                        "Landmark": lm["landmark"],
                        "Type": lm["type"],
                        "Weight": lm["weight"],
                        "Confidence": "High" if lm["weight"] > 0.7 else "Medium" if lm["weight"] > 0.4 else "Low"
                    })
                
                st.dataframe(
                    display_data,
                    use_container_width=True,
                    hide_index=True
                )
                
                # Visualization
                st.subheader("📈 Landmark Weight Distribution")
                weights = [lm["weight"] for lm in result["landmarks"]]
                labels = [f"{lm['relation']} {lm['landmark']}" for lm in result["landmarks"]]
                
                # Simple bar chart using st.bar_chart
                chart_data = {label: weight for label, weight in zip(labels, weights)}
                st.bar_chart(chart_data)
            
            # Display additional directions
            if result["additional_directions"]:
                st.subheader("🧭 Additional Directions")
                for i, direction in enumerate(result["additional_directions"], 1):
                    st.info(f"{i}. {direction}")
            
            # Display preprocessing
            with st.expander("🔍 Preprocessing Details"):
                st.text("Preprocessed text:")
                st.code(result["preprocessed_text"])
                
                if "method" in result:
                    st.text(f"Method used: {result['method']}")
            
            # Technical details
            with st.expander("⚙️ Technical Details"):
                st.markdown("""
                **Enhanced Extraction Process:**
                1. **Preprocessing**: Hinglish conversion, abbreviation expansion, normalization
                2. **Clause Segmentation**: Split by commas and relation keywords
                3. **Relation Detection**: Identify near/behind/opposite/after etc. (plus standalone validation)
                4. **Landmark Extraction**: Capture landmark phrases after relations OR validate standalone landmarks
                5. **Validation**: Ensure extracted text is a proper landmark (keywords, proper nouns, etc.)
                6. **Classification**: Categorize landmark type (RELIGIOUS, GOV, MALL, PARK, BEACH, ROAD, etc.)
                7. **Weighting**: Assign importance scores for geocoding (0.3-0.9)
                8. **Deduplication**: Remove duplicate landmark entries
                """)
                
                st.markdown("**Relation Types Detected:**")
                for rel_type, variants in extractor.RELATIONS.items():
                    st.code(f"{rel_type}: {', '.join(variants)}")
                
                st.markdown("**Enhanced Landmark Categories:**")
                categories = {
                    "RELIGIOUS": "Temples, mosques, churches, gurudwaras",
                    "GOV": "Police stations, government offices, Nagar Parishad",
                    "EDUCATION": "Schools, colleges, universities",
                    "HEALTH": "Hospitals, clinics, medical centers",
                    "SHOP": "Dmart, Reliance, petrol pumps, small shops",
                    "MALL": "Shopping malls, complexes, plazas",
                    "PARK": "Parks, gardens, playgrounds, recreational areas",
                    "BEACH": "Beaches, sea fronts, waterfronts",
                    "ROAD": "Roads, highways, expressways, boulevards",
                    "ROAD_JUNCTION": "Chowks, nakas, road intersections",
                    "TRANSPORT": "Railway stations, bus stands, airports",
                    "NATURAL": "Trees, lakes, rivers, hills (other natural features)"
                }
                
                for cat, desc in categories.items():
                    st.markdown(f"- **{cat}**: {desc}")
        
        else:
            st.warning("Please enter an address to extract landmarks.")
    
    # About section
    st.sidebar.markdown("---")
    st.sidebar.header("ℹ️ About")
    st.sidebar.markdown("""
    **Enhanced Landmark Extraction Pipeline**
    
    - **Purpose**: Extract structured landmark data from Indian addresses
    - **Target**: Tier 2/3 address parsing for geocoding
    - **Methods**: Rule-based and spaCy Matcher approaches
    - **Enhanced Features**: 
      - Hinglish processing
      - Relation-aware extraction
      - **Standalone landmark detection** (roads, parks, malls without relations)
      - Advanced landmark classification (12+ categories)
      - Importance weighting (0.3-0.9)
    
    **For Judges**: 
    *"We extract landmark relations as structured graph-like data and use weighted ranking for accurate geocoding - now supporting standalone landmarks like 'Suruchi Road'"*
    """)

if __name__ == "__main__":
    main()