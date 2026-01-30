import streamlit as st
import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.pipelines.landmark_extraction_pipeline import LandmarkExtractor
from src.pipelines.geocoding_pipeline import GeocodingPipeline

# Initialize pipelines
@st.cache_resource
def load_pipelines():
    extractor = LandmarkExtractor()
    geocoder = GeocodingPipeline()
    return extractor, geocoder

def main():
    st.set_page_config(
        page_title="Address Intelligence Pipeline",
        page_icon="🏢",
        layout="wide"
    )
    
    st.title("📍 Address Intelligence Pipeline")
    st.subheader("Landmark Extraction + Geocoding with Pincode Accuracy")
    
    # Load pipelines
    extractor, geocoder = load_pipelines()
    
    # Input section
    st.header("Input Address")
    address_input = st.text_area(
        "Enter Indian address (Hinglish supported):",
        placeholder="e.g., 101/102, Ebrahim Manzil , Bazar gali, near Fish Market, Versova, Andheri West, Mumbai - 400061",
        height=100
    )
    
    # Extraction method selection
    method = st.radio(
        "Landmark Extraction Method:",
        ["Rule-based (Recommended)", "spaCy Matcher"],
        horizontal=True
    )
    
    extraction_method = "rule_based" if method == "Rule-based (Recommended)" else "spacy_matcher"
    
    # Process button
    if st.button("🔍 Process Address", type="primary"):
        if not address_input.strip():
            st.warning("Please enter an address to process")
            return
        
        with st.spinner("Processing address..."):
            try:
                # Step 1: Extract landmarks
                st.subheader("📍 Landmark Extraction Results")
                
                if extraction_method == "spacy_matcher":
                    landmark_result = extractor.extract_with_spacy_matcher(address_input)
                else:
                    landmark_result = extractor.extract_landmarks(address_input)
                
                # Display landmarks
                if landmark_result["landmarks"]:
                    landmark_data = []
                    for i, lm in enumerate(landmark_result["landmarks"], 1):
                        col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
                        with col1:
                            st.write(f"**{i}.**")
                        with col2:
                            st.write(f"**{lm['relation']}** {lm['landmark']}")
                        with col3:
                            st.write(f"*{lm['type']}*")
                        with col4:
                            st.write(f"`{lm['weight']}`")
                        
                        landmark_data.append({
                            "relation": lm["relation"],
                            "landmark": lm["landmark"],
                            "type": lm["type"],
                            "weight": lm["weight"]
                        })
                    
                    st.info(f"✅ Found {len(landmark_result['landmarks'])} landmarks")
                else:
                    st.warning("⚠️ No landmarks detected")
                    landmark_data = []
                
                # Display additional directions if any
                if landmark_result["additional_directions"]:
                    st.subheader("📋 Additional Information")
                    for direction in landmark_result["additional_directions"]:
                        st.caption(f"• {direction}")
                
                # Step 2: Prepare context for geocoding
                st.subheader("🗺️ Geocoding Process")
                
                import re
                
                # Extract pincode
                pincode_match = re.search(r'\b(\d{6})\b', address_input)
                pincode = pincode_match.group(1) if pincode_match else ""
                
                # Extract city
                city = "Mumbai" if "mumbai" in address_input.lower() or "mumbra" in address_input.lower() else ""
                if not city:
                    city_match = re.search(r',\s*([A-Za-z\s]+)(?:\s*-\s*\d{6}|$)', address_input)
                    if city_match:
                        city = city_match.group(1).strip()
                
                # Extract locality tokens
                words = address_input.split(',')
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
                
                # Prepare context
                context = {
                    "building": "",
                    "house": "",
                    "locality": "",
                    "city": city,
                    "state": "",
                    "pincode": pincode,
                    "landmarks": landmark_result["landmarks"],
                    "raw_text": address_input,
                    "locality_tokens": locality_tokens
                }
                
                # Display context
                with st.expander("🔍 Geocoding Context (Click to view)"):
                    st.json(context)
                
                # Step 3: Geocode the address
                geocoding_result = geocoder.geocode_address(context)
                
                if geocoding_result:
                    # Check if it's an error response
                    if "error" in geocoding_result:
                        st.error(f"❌ Geocoding failed: {geocoding_result['error']}")
                        st.info(f"**Attempts made:** {geocoding_result.get('attempts', 0)}")
                        st.info(f"**Fallback attempts:** {geocoding_result.get('fallback_attempts', 0)}")
                        
                        with st.expander("🔍 Debug Information"):
                            st.write("**Queries tried:**")
                            for query in geocoding_result.get("queries_tried", []):
                                st.code(query)
                            st.write("**Context used:**")
                            st.json(geocoding_result.get("context_used", {}))
                    else:
                        st.subheader("🎯 Final Geocoding Result")
                        
                        # Display key information
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Latitude", f"{geocoding_result['latitude']:.6f}")
                        with col2:
                            st.metric("Longitude", f"{geocoding_result['longitude']:.6f}")
                        with col3:
                            st.metric("Confidence", f"{geocoding_result['confidence']:.3f}")
                        
                        # Display address and pincode
                        st.success(f"**📍 Formatted Address:** {geocoding_result['formatted_address']}")
                        
                        result_pincode = geocoding_result["address_components"].get("postcode", "Not found")
                        st.info(f"**📮 Pincode:** {result_pincode}")
                        
                        st.info(f"**🔍 Query Used:** {geocoding_result['used_query']}")
                        
                        # Warning for fallback results
                        if geocoding_result.get("fallback_used"):
                            st.warning(f"⚠️ {geocoding_result.get('warning', 'Low confidence result')}")
                        
                        # Check if result is correct (for the problematic case)
                        if "101/102" in address_input and "400061" in address_input:
                            addr_lower = geocoding_result['formatted_address'].lower()
                            has_versova = 'versova' in addr_lower
                            has_andheri_west = 'andheri west' in addr_lower
                            has_correct_pincode = result_pincode == '400061'
                            has_mulund = 'mulund' in addr_lower
                            
                            if has_correct_pincode and (has_versova or has_andheri_west) and not has_mulund:
                                st.success("✅ **CORRECT RESULT**: Address properly geocoded to Versova/Andheri West with correct pincode!")
                            elif has_mulund or not has_correct_pincode:
                                st.error("❌ **INCORRECT RESULT**: Still pointing to wrong location or pincode")
                            else:
                                st.warning("⚠️ **PARTIAL RESULT**: May need refinement")
                        
                        # Display alternatives if any
                        if geocoding_result.get('alternatives'):
                            st.subheader("🔄 Alternative Results")
                            for i, alt in enumerate(geocoding_result['alternatives'][:3], 1):
                                with st.expander(f"Alternative {i} (Score: {alt['final_score']:.3f})"):
                                    st.write(f"**Address:** {alt['display_name']}")
                                    alt_pincode = alt.get('address', {}).get('postcode', 'N/A')
                                    st.write(f"**Pincode:** {alt_pincode}")
                
                else:
                    st.error("❌ Geocoding failed - no results found")
                
                # Step 4: Final JSON Output
                st.subheader("📄 Complete JSON Output")
                
                final_output = {
                    "input_address": address_input,
                    "extraction_method": extraction_method,
                    "landmark_extraction": {
                        "landmarks": landmark_data,
                        "total_landmarks": len(landmark_data),
                        "additional_directions": landmark_result["additional_directions"]
                    },
                    "geocoding_context": context,
                    "geocoding_result": geocoding_result
                }
                
                # Display JSON
                st.json(final_output)
                
                # Download button
                json_str = json.dumps(final_output, indent=2, ensure_ascii=False)
                st.download_button(
                    label="📥 Download JSON Output",
                    data=json_str,
                    file_name="address_intelligence_output.json",
                    mime="application/json"
                )
                
            except Exception as e:
                st.error(f"❌ Error processing address: {str(e)}")
                st.exception(e)
    
    # Example addresses
    st.sidebar.header("📝 Example Addresses")
    
    examples = [
        "101/102, Ebrahim Manzil , Bazar gali, near Fish Market, Versova, Andheri West, Mumbai - 400061",
        "sai prasad,mahesh 202 ,gaulwada,vasai west,suruchi road",
        "Near Hanuman Mandir, after chai tapri, opposite Nagar Parishad office, lane behind big tree",
        "opp police station, nr temple, behind reliance mart"
    ]
    
    selected_example = st.sidebar.selectbox(
        "Select an example:",
        [""] + examples,
        format_func=lambda x: x[:50] + "..." if len(x) > 50 else x
    )
    
    if selected_example:
        st.sidebar.text_area("Example Address:", value=selected_example, height=100, key="example_addr")
        if st.sidebar.button("Use This Example"):
            st.session_state.address_input = selected_example
            st.rerun()
    
    # Information section
    st.sidebar.header("ℹ️ About")
    st.sidebar.info("""
    This application combines:
    
    1. **Landmark Extraction**: Identifies landmarks and their relations
    2. **Geocoding**: Converts addresses to GPS coordinates
    3. **Pincode Accuracy**: Ensures correct location matching
    
    **Key Features:**
    - Hinglish address support
    - Multiple extraction methods
    - Improved pincode constraints
    - JSON output for integration
    """)

if __name__ == "__main__":
    main()