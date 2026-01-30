import streamlit as st
import sys
import os

# Add the project root to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

# Try to import the Hinglish processor
try:
    from src.utils.hinglish_processor import process_hinglish_address
    st.success("Successfully imported Hinglish processor!")
except ImportError as e:
    st.error(f"Failed to import Hinglish processor: {e}")
    st.error(f"Python path: {sys.path}")
    st.stop()

def main():
    st.title("Address Parser")
    
    # Input text area
    text = st.text_area("Enter address:", "dmart ke peeche wali gali, mandir ke paas")
    
    if st.button("Process"):
        try:
            # Process the input
            processed, metadata = process_hinglish_address(text)
            
            # Display results
            st.subheader("Processed Address")
            st.code(processed)
            
            st.subheader("Metadata")
            st.json(metadata)
            
        except Exception as e:
            st.error(f"Error processing address: {e}")

if __name__ == "__main__":
    main()
