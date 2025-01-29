import streamlit as st
import requests
import time
from pathlib import Path
import json
import os

# API endpoints
BACKEND_URL = "http://backend-fastapi:8001"
UPLOAD_ENDPOINT = f"{BACKEND_URL}/api/v1/pdf/upload"
STATUS_ENDPOINT = f"{BACKEND_URL}/api/v1/pdf/status"
RESULT_ENDPOINT = f"{BACKEND_URL}/api/v1/pdf/result"

st.set_page_config(
    page_title="PDF Destroyer Max",
    page_icon="📄",
    layout="wide"
)

def upload_file(file):
    """Upload file to backend service"""
    files = {"file": file.getvalue()}
    try:
        response = requests.post(UPLOAD_ENDPOINT, files=files)
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Upload failed: {str(e)}")
        return None

def get_processing_status(task_id):
    """Check processing status"""
    try:
        response = requests.get(f"{STATUS_ENDPOINT}/{task_id}")
        return response.json()
    except requests.exceptions.RequestException:
        return {"status": "error"}

def get_results(task_id):
    """Get processing results"""
    try:
        response = requests.get(f"{RESULT_ENDPOINT}/{task_id}")
        return response.json()
    except requests.exceptions.RequestException:
        return None

def main():
    st.title("🚀 PDF Destroyer Max")
    st.subheader("Advanced PDF Processing with OCR & AI Summarization")

    # Sidebar
    with st.sidebar:
        st.header("Settings")
        ocr_enabled = st.checkbox("Enable OCR", value=True)
        summarize_enabled = st.checkbox("Enable AI Summarization", value=True)
        st.divider()
        st.markdown("### Processing Options")
        chunk_size = st.slider("Text Chunk Size", 500, 2000, 1000)
        
    # Main content
    uploaded_file = st.file_uploader("Upload your PDF", type=["pdf"])
    
    if uploaded_file:
        st.info("File uploaded: " + uploaded_file.name)
        
        if st.button("Start Processing"):
            with st.spinner("Uploading file..."):
                # Upload file and get task ID
                response = upload_file(uploaded_file)
                if response and "task_id" in response:
                    task_id = response["task_id"]
                    
                    # Create progress bar
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Poll for status
                    while True:
                        status = get_processing_status(task_id)
                        if status["status"] == "completed":
                            progress_bar.progress(100)
                            status_text.success("Processing completed!")
                            break
                        elif status["status"] == "failed":
                            progress_bar.empty()
                            status_text.error("Processing failed!")
                            break
                        else:
                            progress = status.get("progress", 0)
                            progress_bar.progress(progress)
                            status_text.text(f"Processing: {status.get('message', '')}...")
                            time.sleep(1)
                    
                    # Show results
                    if status["status"] == "completed":
                        results = get_results(task_id)
                        if results:
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("### Summary")
                                st.text_area("AI Generated Summary", 
                                           results.get("summary", ""),
                                           height=300)
                                
                            with col2:
                                st.markdown("### Extracted Text")
                                st.text_area("Full Text", 
                                           results.get("full_text", ""),
                                           height=300)
                            
                            # Download buttons
                            st.download_button(
                                "Download Summary",
                                results.get("summary", ""),
                                file_name=f"{uploaded_file.name}_summary.txt"
                            )
                            st.download_button(
                                "Download Full Text",
                                results.get("full_text", ""),
                                file_name=f"{uploaded_file.name}_full.txt"
                            )

if __name__ == "__main__":
    main()