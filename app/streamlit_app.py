import streamlit as st
import requests
import os
import tempfile
import base64
import json
import time
import random
from PIL import Image
import io
import uuid

# We'll import the 3D model viewer directly when needed to avoid conflicts

# Set page configuration
st.set_page_config(
    page_title="AI Image Generator",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Function to create a simple in-memory database for the session
def init_session_memory():
    if 'memory' not in st.session_state:
        st.session_state.memory = []
        st.session_state.current_images = {}
        st.session_state.current_model = {}
        st.session_state.page = "generator"  # Default page

# Function to add an item to memory
def add_to_memory(prompt, image_url, model_url, viewer_url):
    memory_item = {
        "id": str(uuid.uuid4()),
        "timestamp": time.time(),
        "prompt": prompt,
        "image_url": image_url,
        "model_url": model_url,
        "viewer_url": viewer_url
    }
    st.session_state.memory.append(memory_item)
    return memory_item

# Function to get recent creations from API
def get_recent_creations(limit=5):
    try:
        response = requests.get(f"http://localhost:8888/recent?limit={limit}")
        if response.status_code == 200:
            return response.json().get("results", [])
        return []
    except Exception as e:
        st.error(f"Error fetching recent creations: {str(e)}")
        return []

# Function to find similar images
def find_similar_images(prompt, limit=5):
    try:
        response = requests.post(
            "http://localhost:8888/similar",
            json={"prompt": prompt, "limit": limit}
        )
        if response.status_code == 200:
            return response.json().get("results", [])
        return []
    except Exception as e:
        st.error(f"Error finding similar images: {str(e)}")
        return []

# Function to search by keyword
def search_by_keyword(keyword, limit=5):
    try:
        response = requests.post(
            "http://localhost:8888/keyword",
            json={"keyword": keyword, "limit": limit}
        )
        if response.status_code == 200:
            return response.json().get("results", [])
        return []
    except Exception as e:
        st.error(f"Error searching by keyword: {str(e)}")
        return []

# Initialize memory
init_session_memory()

# Navigation in sidebar
with st.sidebar:
    st.title("🎨 AI Image Generator")
    
    # Navigation
    nav_selection = st.radio(
        "Navigation",
        ["Image Generator", "3D Model Browser", "Similar Search"]
    )
    
    # Set the current page based on selection
    if nav_selection == "Image Generator":
        st.session_state.page = "generator"
    elif nav_selection == "3D Model Browser":
        st.session_state.page = "3d_browser"
    elif nav_selection == "Similar Search":
        st.session_state.page = "similar_search"
    
    st.divider()
    
    # History section
    st.title("📚 History")
    
    # Create tabs for different sections
    if st.session_state.page == "generator":
        tab1, tab2 = st.tabs(["Recent Creations", "Settings"])
        
        with tab1:
            st.subheader("Your Past Creations")
            
            # Fetch recent creations from API
            recent_creations = get_recent_creations(5)
            
            if not recent_creations:
                st.info("No images generated yet! Create your first one.")
            else:
                # Display recent creations in reverse chronological order
                for item in recent_creations:
                    image_path = item.get("image_path", "")
                    model_path = item.get("model_path", "")
                    prompt = item.get("prompt", "Unknown")
                    
                    # Convert paths to URLs
                    image_filename = os.path.basename(image_path)
                    model_filename = os.path.basename(model_path)
                    
                    image_url = f"http://localhost:8888/output/{image_filename}"
                    model_url = f"http://localhost:8888/output/{model_filename}"
                    
                    with st.expander(f"{prompt[:30]}..."):
                        try:
                            st.image(image_url, width=200)
                        except Exception as e:
                            st.warning(f"Could not load image preview: {str(e)}")
                        timestamp = item.get("timestamp", 0)
                        if isinstance(timestamp, (int, float)):
                            st.markdown(f"Created: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))}")
                        
                        if st.button("Load", key=f"load_{item['id']}"):
                            # Load this creation into the main view
                            memory_id = str(uuid.uuid4())
                            st.session_state.current_images[memory_id] = image_url
                            st.session_state.current_model[memory_id] = model_url
                            st.rerun()
        
        with tab2:
            st.subheader("Color Themes")
            dragon_color = st.selectbox(
                "Preferred Color Scheme",
                ["Green", "Blue", "Red", "Gold", "Black", "White"]
            )
            
            st.subheader("Advanced Settings")
            add_magical = st.checkbox("Add Magical Effects", value=True)
            add_fire = st.checkbox("Add Dynamic Elements", value=True)
    
    st.divider()
    st.caption("Made with ❤️ by Dennis Muasya")

# Conditional display based on the current page
if st.session_state.page == "generator":
    # Image generator page
    st.title("🎨 AI Image Generator")
    st.subheader("Create stunning AI-generated imagery")
    
    # Create column layout for input and output
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### Image Creation")
        
        # Input form for text prompt
        with st.form(key="generation_form"):
            prompt = st.text_area(
                "Describe your image:", 
                placeholder="Example: A green dragon, a blue robot, a futuristic city, or a planet in space",
                height=100
            )
            
            # Add suggested elements from settings
            if 'add_magical' in locals() and add_magical:
                prompt_help = "Adding 'magical' to your prompt will create magical effects"
            else:
                prompt_help = "Describe what you want to generate with details about colors and environment"
                
            st.caption(prompt_help)
            
            col_a, col_b = st.columns(2)
            with col_a:
                generate_button = st.form_submit_button("Generate Image", use_container_width=True)
            with col_b:
                clear_button = st.form_submit_button("Clear", use_container_width=True)
        
        # Voice input option
        st.markdown("### Or use voice input")
        voice_placeholder = st.empty()
        with voice_placeholder.container():
            if st.button("🎤 Record Voice", use_container_width=True):
                # In a production app, you would implement voice recording here
                # For this demo, we'll simulate voice input
                st.info("Voice recording would be implemented here with SpeechRecognition library...")
                time.sleep(2)
                # Random example based on image types
                example_texts = [
                    "a green dragon in a magical forest",
                    "a blue robot with glowing eyes",
                    "a futuristic city at night with neon lights",
                    "a red planet with rings in space"
                ]
                voice_text = random.choice(example_texts)
                
                # Update the text area with the voice input
                st.session_state.voice_text = voice_text
                st.rerun()
        
        # Apply voice text if present
        if 'voice_text' in st.session_state:
            prompt = st.session_state.voice_text
            
        # Display information about the API
        with st.expander("How does it work?"):
            st.markdown("""
            1. Enter a description of what you want to generate
            2. Our AI detects the type of image to create (dragon, robot, city, space, or landscape)
            3. You get both a 2D image and a 3D model
            4. All creations are stored with vector embeddings for similarity search
            5. Use the 3D Model Browser to explore your creations in 3D
            
            **Supported image types:**
            - **Dragons**: "A red dragon breathing fire", "Green dragon with emerald scales"
            - **Robots**: "Blue robot with glowing eyes", "Mechanical android with laser weapons"
            - **Cities**: "Futuristic city at night with neon lights", "Cyberpunk urban landscape"
            - **Space**: "Red planet with rings in space", "Cosmic nebula with stars"
            - **Landscapes**: Any other type of scenery or object
            
            **Tips for best results:**
            - Mention specific colors like "green", "blue", "red", "gold", "purple", "black", "white"
            - Add details about the environment like "forest", "mountains", "castle", "night"
            - Use terms like "magical" for special effects
            """)
    
    with col2:
        st.markdown("### Your Image Visualization")
        
        # Display area for the generated image and model
        image_container = st.empty()
        model_viewer = st.empty()
        result_text = st.empty()
        
        # Check if there's a current image to display
        if len(st.session_state.current_images) > 0:
            current_id = list(st.session_state.current_images.keys())[-1]
            image_container.image(st.session_state.current_images[current_id], use_container_width=True)
            
            with model_viewer.container():
                st.markdown("### 3D Model Viewer")
                st.markdown("Your 3D model is ready!")
                st.markdown(f"[Download 3D Model]({st.session_state.current_model[current_id]})")
                
                # Link to 3D browser
                if st.button("View in 3D Browser"):
                    st.session_state.page = "3d_browser"
                    st.rerun()
        else:
            # Show placeholder
            image_container.image("https://placehold.co/600x400?text=Your+Image+Will+Appear+Here", use_container_width=True)
            model_viewer.info("Generate an image to see the 3D model")
    
    # Process the generation when the button is clicked
    if generate_button:
        if not prompt:
            st.error("Please enter a description for your image")
        else:
            with st.spinner("🔮 Creating your masterpiece..."):
                try:
                    # Add the selected color from settings if defined and not already in prompt
                    if 'dragon_color' in locals() and dragon_color.lower() not in prompt.lower():
                        enhanced_prompt = f"{dragon_color.lower()} {prompt}"
                    else:
                        enhanced_prompt = prompt
                    
                    # Add magical effects if selected and not already in prompt
                    if 'add_magical' in locals() and add_magical and "magical" not in prompt.lower():
                        enhanced_prompt = f"{enhanced_prompt} with magical effects"
                    
                    # Add fire breath if selected and not already in prompt
                    if 'add_fire' in locals() and add_fire and "fire" not in prompt.lower():
                        enhanced_prompt = f"{enhanced_prompt} breathing fire"
                    
                    # Make API call to the backend
                    response = requests.post(
                        "http://localhost:8888/generate",
                        json={"prompt": enhanced_prompt}
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        # Get URLs to the files
                        base_url = "http://localhost:8888"
                        image_url = f"{base_url}{result['files']['image']}"
                        model_url = f"{base_url}{result['files']['model']}"
                        viewer_url = f"{base_url}{result['files']['viewer']}"
                        
                        # Add to memory
                        memory_item = add_to_memory(enhanced_prompt, image_url, model_url, viewer_url)
                        
                        # Update current display
                        st.session_state.current_images[memory_item['id']] = image_url
                        st.session_state.current_model[memory_item['id']] = model_url
                        
                        # Display generated image
                        image_container.image(image_url, use_container_width=True)
                        
                        with model_viewer.container():
                            st.markdown("### 3D Model Viewer")
                            st.markdown("Your 3D model is ready!")
                            st.markdown(f"[Download 3D Model]({model_url})")
                            st.markdown(f"[Open in Web Viewer]({viewer_url})")
                            
                            # Link to 3D browser
                            if st.button("View in 3D Browser"):
                                st.session_state.page = "3d_browser"
                                st.rerun()
                        
                        # Clear the spinning message
                        result_text.success(f"Your image has been generated! Prompt: '{enhanced_prompt}'")
                    else:
                        result_text.error(f"Failed to generate image: {response.text}")
                except Exception as e:
                    result_text.error(f"Error: {str(e)}")
    
    # Clear button logic
    if clear_button:
        # Reset form and displayed image
        prompt = ""
        if 'voice_text' in st.session_state:
            del st.session_state.voice_text
        
        # Clear current display but keep history
        st.session_state.current_images = {}
        st.session_state.current_model = {}
        st.rerun()

elif st.session_state.page == "3d_browser":
    # Import and run the 3D browser module
    try:
        # Use a direct import to avoid module conflicts
        import importlib.util
        spec = importlib.util.spec_from_file_location("model_viewer", 
                                                     os.path.join(os.path.dirname(__file__), "model_viewer.py"))
        model_viewer_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(model_viewer_module)
        
        # Call the display function
        model_viewer_module.display_3d_viewer()
    except Exception as e:
        st.error(f"Error loading 3D viewer: {str(e)}")
        st.error("Try restarting the application with './start.sh'")

elif st.session_state.page == "similar_search":
    # Similar search page
    st.title("🔍 Similar Image Search")
    st.subheader("Find images that match your description")
    
    # Search form
    search_col1, search_col2 = st.columns([3, 1])
    
    with search_col1:
        search_query = st.text_input("Enter your search", placeholder="Example: red dragon")
    
    with search_col2:
        search_type = st.selectbox("Search type", ["Semantic", "Keyword"])
    
    if st.button("Search"):
        if not search_query:
            st.error("Please enter a search query")
        else:
            with st.spinner("Searching..."):
                if search_type == "Semantic":
                    results = find_similar_images(search_query)
                else:
                    results = search_by_keyword(search_query)
                
                if not results:
                    st.info("No results found for your search.")
                else:
                    st.success(f"Found {len(results)} matching images")
                    
                    # Display results in a grid
                    cols = st.columns(3)
                    
                    for idx, item in enumerate(results):
                        image_path = item.get("image_path", "")
                        model_path = item.get("model_path", "")
                        prompt = item.get("prompt", "Unknown")
                        
                        # Convert paths to URLs
                        image_filename = os.path.basename(image_path)
                        model_filename = os.path.basename(model_path)
                        
                        image_url = f"http://localhost:8888/output/{image_filename}"
                        model_url = f"http://localhost:8888/output/{model_filename}"
                        
                        with cols[idx % 3]:
                            try:
                                st.image(image_url, use_container_width=True)
                            except Exception as e:
                                st.warning(f"Could not load image: {str(e)}")
                                st.warning("Image may not exist or server may be unavailable")
                            st.markdown(f"**Prompt:** {prompt}")
                            
                            # Create columns for buttons
                            btn_col1, btn_col2 = st.columns(2)
                            
                            with btn_col1:
                                if st.button("Show Details", key=f"details_{idx}"):
                                    memory_id = str(uuid.uuid4())
                                    st.session_state.current_images[memory_id] = image_url
                                    st.session_state.current_model[memory_id] = model_url
                                    st.session_state.page = "generator"
                                    st.rerun()
                            
                            with btn_col2:
                                if st.button("View 3D", key=f"3d_{idx}"):
                                    memory_id = str(uuid.uuid4())
                                    st.session_state.current_images[memory_id] = image_url
                                    st.session_state.current_model[memory_id] = model_url
                                    st.session_state.page = "3d_browser"
                                    st.rerun()
                            
                            st.divider()

# Bottom section with additional information
st.divider()
st.caption("AI Image Generator v2.0 - Powered by AI - © 2025")