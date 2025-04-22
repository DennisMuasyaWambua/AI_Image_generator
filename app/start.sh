#!/bin/bash

echo "Starting AI Image Generator application with ChromaDB and 3D Viewer"

# Make sure required packages are installed
echo "Checking for required packages..."
python3 -m pip install -q streamlit chromadb Pillow importlib-metadata watchdog

# Clean up any previous logs
echo "" > logs_backend.txt
echo "" > logs_frontend.txt

# Create output directory if it doesn't exist
mkdir -p ./output

# Create datastore directory if it doesn't exist
mkdir -p ./datastore

# Create ChromaDB directory
mkdir -p ./datastore/chroma_db

# Kill any existing processes
echo "Stopping any previously running instances..."
pkill -f "python3 test_app.py" 2>/dev/null || true
pkill -f "streamlit run streamlit_app.py" 2>/dev/null || true
pkill -f "streamlit run model_viewer.py" 2>/dev/null || true
sleep 1

# Start the backend API
echo "Starting backend API on port 8888..."
python3 test_app.py > logs_backend.txt 2>&1 &
BACKEND_PID=$!

# Wait for backend to start
echo "Waiting for backend to initialize..."
sleep 3

# Check if backend started successfully
if ! ps -p $BACKEND_PID > /dev/null; then
    echo "ERROR: Backend failed to start. Check logs_backend.txt for details."
    exit 1
fi

# Start the Streamlit frontend
echo "Starting Streamlit frontend..."
streamlit run streamlit_app.py > logs_frontend.txt 2>&1 &
STREAMLIT_PID=$!

# Wait for Streamlit to start
echo "Waiting for Streamlit to initialize..."
sleep 3

# Check if Streamlit started successfully
if ! ps -p $STREAMLIT_PID > /dev/null; then
    echo "ERROR: Streamlit failed to start. Check logs_frontend.txt for details."
    kill $BACKEND_PID
    exit 1
fi

echo "============================================"
echo "✅ Application is running!"
echo "- Backend API: http://localhost:8888"
echo "- Frontend UI: http://localhost:8501"
echo ""
echo "Features:"
echo "- Image Generator with vector similarity search via ChromaDB"
echo "- 3D Model Browser for exploring your creations"
echo "- Voice-to-text simulation"
echo "============================================"
echo ""
echo "Press Ctrl+C to stop all services"

# Keep the script running and gracefully handle termination
trap "echo 'Shutting down services...'; kill $BACKEND_PID $STREAMLIT_PID; echo 'Application stopped.'; exit" INT TERM
wait $BACKEND_PID $STREAMLIT_PID