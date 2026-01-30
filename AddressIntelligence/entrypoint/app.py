import streamlit as st
import json
import sys
import os
import re
from typing import Dict, Any

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from src.pipelines.inference_pipeline import AddressParser
from src.utils.hinglish_processor import process_hinglish_address


from src.pipelines.inference_pipeline import AddressParser

def display_analysis(metadata: Dict[str, Any]) -> None:
    """Display the analysis of the processed address."""
    if not metadata.get('is_hinglish'):
        return
        
    with st.expander("🔍 Hinglish Processing Analysis", expanded=True):
        st.markdown("### Processing Steps")
        st.markdown(f"**Original:** `{metadata['original']}`")
        st.markdown(f"**Normalized:** `{metadata['normalized']}`")
        
        if metadata['components']:
            st.markdown("### Extracted Components")
            if metadata['components']['landmarks']:
                st.markdown(f"**Landmarks:** {', '.join(metadata['components']['landmarks'])}")
            if metadata['components']['directions']:
                st.markdown(f"**Directions:** {', '.join(metadata['components']['directions'])}")
            if metadata['components']['street_parts']:
                st.markdown(f"**Street Indicators:** {', '.join(metadata['components']['street_parts'])}")

def main():
    st.set_page_config(page_title="Address Intelligence", layout="wide")
    st.title("Address Intelligence System")
    st.markdown("Extract structured entities from messy Indian addresses. Supports Hinglish input like 'dmart ke peeche wali gali'.")

    # Initialize parser
    try:
        parser = AddressParser(config_path=os.path.join(project_root, "config", "model_config.yaml"))
    except Exception as e:
        st.error(f"Failed to load parser config: {e}")
        return

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Input Address")
        example_phrases = [
            "dmart ke peeche wali gali",
            "mandir ke paas, gali no 5",
            "school ke samne wala ghar",
            "society ke andar, tower 3"
        ]
        
        # Show example phrases as buttons
        st.markdown("**Examples:** " + " • ".join([f"`{p}`" for p in example_phrases]))
        
        raw_address = st.text_area(
            "Paste address here (English or Hinglish):",
            height=150,
            value="dmart ke peeche wali gali, mandir ke paas"
        )
        
        # Process Hinglish input
        if raw_address:
            processed_address, metadata = process_hinglish_address(raw_address)
            
            if metadata['is_hinglish']:
                with st.expander("🔍 View Processed Text", expanded=True):
                    st.markdown(f"**Processed:** `{processed_address}`")
                display_analysis(metadata)
            else:
                with st.expander("🔍 View Processed Text", expanded=False):
                    st.markdown("No Hinglish patterns detected.")
                    st.code(processed_address, language="text")
        
        analyze_btn = st.button("Parse Address", type="primary")

    if analyze_btn and raw_address:
        with st.spinner("Parsing..."):
            try:
                # Process Hinglish input first
                processed_address, _ = process_hinglish_address(raw_address)
                # Parse the processed address
                result = parser.parse(processed_address)
                
                with col2:
                    st.subheader("Extracted Details")
                    
                    # Confidence Score
                    score_val = result.get('confidence_score', 0) * 100
                    st.progress(int(score_val), f"Confidence Score: {score_val:.0f}%")
                    
                    # Address Components
                    st.subheader("Address Components")
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        if result.get('house_number'):
                            st.metric("House Number", result['house_number'])
                        if result.get('building_name'):
                            st.metric("Building Name", result['building_name'])
                        if result.get('street_or_lane'):
                            st.metric("Street/Lane", result['street_or_lane'])
                        if result.get('locality_or_area'):
                            st.metric("Locality/Area", result['locality_or_area'])
                        if result.get('landmark'):
                            st.metric("Landmark", result['landmark'])
                    
                    with col_b:
                        if result.get('city'):
                            st.metric("City", result['city'])
                        if result.get('state'):
                            st.metric("State", result['state'])
                        if result.get('pincode'):
                            st.metric("Pincode", result['pincode'])
                        if result.get('country'):
                            st.metric("Country", result['country'])
                        if result.get('additional_directions'):
                            st.metric("Additional Directions", result['additional_directions'])
                    
                    # Normalized Address
                    st.subheader("Normalized Address")
                    st.code(result.get('normalized_address', ''), language='text')
                    
                    # Analysis
                    if result.get('reasons'):
                        st.subheader("Analysis")
                        for reason in result.get('reasons', []):
                            st.markdown(f"- {reason}")
                    
                    # Raw JSON (collapsible)
                    with st.expander("View Raw JSON"):
                        st.json(result)

            except Exception as e:
                st.error(f"Error parsing address: {e}")

if __name__ == "__main__":
    main()
