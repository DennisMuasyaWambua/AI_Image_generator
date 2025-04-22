# AI Image Generator (Previously "Dragon Generator")

An AI-powered application that generates 2D images and 3D models from natural language descriptions. 
Now enhanced with ChromaDB for vector similarity search and a dedicated 3D model browser.

## Features

- Generate detailed images from text descriptions
- Create corresponding 3D models in OBJ format
- Interactive frontend with voice input simulation
- ChromaDB vector database for semantic similarity search
- 3D model browser for exploring your creations
- Memory system to save and retrieve past generations

## Overview

The application works as follows:
1. A user provides a text prompt (e.g., "Make me a glowing dragon standing on a cliff at sunset")
2. The prompt is processed to generate a detailed visual
3. The system creates both a 2D image and a 3D model
4. All creations are stored in ChromaDB with vector embeddings for similarity search
5. Users can browse their 3D models and find similar images semantically

## Setup and Installation

### Prerequisites
- Python 3.8+
- Flask
- Streamlit
- Pillow (PIL)
- ChromaDB

## Option 1: Using the Start Script (Recommended)

1. Run the application with the all-in-one start script:
   ```bash
   ./start.sh
   ```
   
   This will:
   - Install required dependencies
   - Start the backend API
   - Launch the Streamlit frontend
   - Create necessary directories

2. Access the applications:
   - Backend API: http://localhost:8888/
   - Streamlit UI: http://localhost:8501/

## Option 2: Running Components Separately

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the backend API:
   ```bash
   python test_app.py
   ```

3. Run the Streamlit frontend:
   ```bash
   streamlit run streamlit_app.py
   ```

4. (Optional) Run the 3D model browser directly:
   ```bash
   streamlit run 3d_viewer.py
   ```

## Usage

### Streamlit Frontend

The Streamlit interface provides three main sections:

1. **Image Generator**
   - Enter a description in the text area
   - Use the simulated voice input option
   - Configure color themes and effects
   - Generate images and see results instantly

2. **3D Model Browser**
   - Explore all generated 3D models in an interactive viewer
   - Download models and images
   - View model details and creation dates

3. **Similar Search**
   - Search for images similar to a description (semantic search)
   - Find images by keywords
   - Browse and interact with search results

### API Endpoints

The backend API is available at http://localhost:8888 with the following endpoints:

- `POST /generate`: Generate an image from a text prompt
  ```json
  {
    "prompt": "A green dragon with emerald scales in a magical forest"
  }
  ```

- `POST /similar`: Find images similar to a description
  ```json
  {
    "prompt": "red dragon",
    "limit": 5
  }
  ```

- `POST /keyword`: Search for images by keyword
  ```json
  {
    "keyword": "forest",
    "limit": 5
  }
  ```

- `GET /recent`: Get most recent generations
  ```
  /recent?limit=5
  ```

- `GET /output/<filename>`: Retrieve generated files

## ChromaDB Vector Database

The application uses ChromaDB to store vector embeddings of your prompts, enabling:
- Semantic search for similar images
- Keyword-based retrieval
- Advanced memory management with vector database

Data is stored in the `datastore/chroma_db` directory.

## Generated Files

For each generation, the system creates:
1. An image file (PNG format) - a visual representation of your prompt
2. A 3D model file (OBJ format) - a 3D model that can be viewed and manipulated
3. An HTML viewer - to easily see the generated content in your browser

All files are saved in the `output` directory.

## Troubleshooting

### Common Issues

1. **Application fails to start**
   - Check log files (`logs_backend.txt` and `logs_frontend.txt`) for specific errors
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Make sure the output and datastore directories exist and are writable

2. **ChromaDB errors**
   - Make sure the datastore/chroma_db directory exists and is writable
   - If you encounter database errors, try deleting the chroma_db directory and restarting

3. **Port conflicts**
   - Make sure ports 8501 and 8888 are available and not used by other applications
   - Change ports if needed by modifying the code

4. **3D viewer issues**
   - The 3D viewer requires Three.js loaded from CDN, so internet access is needed
   - Make sure your browser supports WebGL

## Customization

You can customize your images by including these keywords in your prompt:
- Colors: "green", "blue", "red", "gold", "black", "white"
- Special effects: "magical", "fire"
- Environments: "forest", "mountains", "castle"