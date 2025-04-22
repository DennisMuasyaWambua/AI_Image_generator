import os
import streamlit as st
import glob
import base64
import io
from PIL import Image
import time

def get_3d_obj_models():
    """Get all OBJ models in the output directory"""
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    obj_files = glob.glob(os.path.join(output_dir, "*.obj"))
    obj_files.sort(key=os.path.getmtime, reverse=True)  # Sort by modification time (newest first)
    return obj_files

def get_model_images():
    """Get all corresponding images for OBJ models"""
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    image_files = glob.glob(os.path.join(output_dir, "image_*.png"))
    image_files.sort(key=os.path.getmtime, reverse=True)  # Sort by modification time (newest first)
    return image_files

def create_obj_viewer_html(obj_path):
    """Create HTML for viewing OBJ model using Three.js"""
    obj_filename = os.path.basename(obj_path)
    
    # Basic Three.js viewer for OBJ files
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>3D Model Viewer</title>
        <style>
            body {{ margin: 0; padding: 0; overflow: hidden; }}
            canvas {{ width: 100%; height: 100%; }}
        </style>
    </head>
    <body>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
        <script src="https://threejs.org/examples/js/loaders/OBJLoader.js"></script>
        <script src="https://threejs.org/examples/js/controls/OrbitControls.js"></script>
        
        <script>
            // Set up scene
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0x333333);
            
            // Set up camera
            const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
            camera.position.z = 5;
            
            // Set up renderer
            const renderer = new THREE.WebGLRenderer({{ antialias: true }});
            renderer.setSize(window.innerWidth, window.innerHeight);
            document.body.appendChild(renderer.domElement);
            
            // Set up lights
            const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
            scene.add(ambientLight);
            
            const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
            directionalLight.position.set(1, 1, 1);
            scene.add(directionalLight);
            
            // Set up controls
            const controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.25;
            
            // Load OBJ model
            const loader = new THREE.OBJLoader();
            loader.load(
                '/output/{obj_filename}',  # URL to your OBJ file
                function (object) {{
                    // Center the model
                    const box = new THREE.Box3().setFromObject(object);
                    const center = box.getCenter(new THREE.Vector3());
                    object.position.sub(center);
                    
                    // Scale the model to fit the view
                    const size = box.getSize(new THREE.Vector3());
                    const maxDim = Math.max(size.x, size.y, size.z);
                    const scale = 3 / maxDim;
                    object.scale.set(scale, scale, scale);
                    
                    // Add to scene
                    scene.add(object);
                    
                    // Add wireframe material to all meshes
                    object.traverse(function(child) {{
                        if (child instanceof THREE.Mesh) {{
                            // Create material with random color
                            const material = new THREE.MeshPhongMaterial({{
                                color: 0x00ff00, // Green color
                                specular: 0x111111,
                                shininess: 30,
                                flatShading: true,
                            }});
                            child.material = material;
                        }}
                    }});
                }},
                function (xhr) {{
                    console.log((xhr.loaded / xhr.total * 100) + '% loaded');
                }},
                function (error) {{
                    console.error('Error loading OBJ file:', error);
                }}
            );
            
            // Handle window resize
            window.addEventListener('resize', function() {{
                camera.aspect = window.innerWidth / window.innerHeight;
                camera.updateProjectionMatrix();
                renderer.setSize(window.innerWidth, window.innerHeight);
            }});
            
            // Animation loop
            function animate() {{
                requestAnimationFrame(animate);
                controls.update();
                renderer.render(scene, camera);
            }}
            animate();
        </script>
    </body>
    </html>
    """
    return html

def get_image_download_link(image_path, link_text):
    """Create a download link for an image file"""
    with open(image_path, "rb") as f:
        img_bytes = f.read()
    b64 = base64.b64encode(img_bytes).decode()
    filename = os.path.basename(image_path)
    return f'<a href="data:image/png;base64,{b64}" download="{filename}">{link_text}</a>'

def get_model_download_link(model_path, link_text):
    """Create a download link for an OBJ model file"""
    with open(model_path, "rb") as f:
        model_bytes = f.read()
    b64 = base64.b64encode(model_bytes).decode()
    filename = os.path.basename(model_path)
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">{link_text}</a>'

def display_3d_viewer():
    """Main function to display the 3D model viewer"""
    # We don't call st.set_page_config() here since it's already called in the main app
    # This function is intended to be imported and used within an existing Streamlit app
    
    st.title("🔍 3D Model Browser")
    st.write("Explore your generated 3D models and images")
    
    # Get list of models and images
    models = get_3d_obj_models()
    images = get_model_images()
    
    if not models:
        st.info("No models found. Generate some dragons first!")
        return
    
    # Create a gallery layout
    st.subheader("Model Gallery")
    
    # Create columns for the gallery
    cols = st.columns(3)
    
    for idx, (model_path, image_path) in enumerate(zip(models, images)):
        # Get timestmap from filename
        model_filename = os.path.basename(model_path)
        timestamp_str = model_filename.split("_")[1].split(".")[0]
        try:
            timestamp = int(timestamp_str)
            formatted_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
        except:
            formatted_date = "Unknown date"
        
        with cols[idx % 3]:
            # Show image
            try:
                image = Image.open(image_path)
                st.image(image, use_container_width=True)
            except:
                st.error(f"Could not load image: {image_path}")
            
            # Create model viewer button
            if st.button(f"View 3D Model", key=f"view_{idx}"):
                # Create HTML for the viewer
                viewer_html = create_obj_viewer_html(model_path)
                
                # Display in Streamlit
                st.components.v1.html(viewer_html, height=600)
            
            # Download links
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(get_image_download_link(image_path, "📥 Download Image"), unsafe_allow_html=True)
            with col2:
                st.markdown(get_model_download_link(model_path, "📥 Download Model"), unsafe_allow_html=True)
            
            st.caption(f"Created: {formatted_date}")
            st.divider()

if __name__ == "__main__":
    # When running standalone, we need to set the page config
    st.set_page_config(
        page_title="3D Model Browser",
        page_icon="🔍",
        layout="wide"
    )
    display_3d_viewer()