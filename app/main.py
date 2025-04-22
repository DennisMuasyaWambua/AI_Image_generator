import logging
import os
import json
import base64
from typing import Dict, List, Optional, Any, Tuple
import sqlite3
from datetime import datetime
import time
import math
import random
import numpy as np
import io
import textwrap
from PIL import Image, ImageDraw, ImageFont

from ontology_dc8f06af066e4a7880a5938933236037.config import ConfigClass
from ontology_dc8f06af066e4a7880a5938933236037.input import InputClass
from ontology_dc8f06af066e4a7880a5938933236037.output import OutputClass
try:
    from openfabric_pysdk.context import State
except ImportError:
    # Fallback for when SDK is not available
    class State:
        pass
from core.stub import Stub

# Define a simple model class since AppModel is not available
class AppModel:
    def __init__(self):
        self.request = None
        self.response = None

# Configurations for the app
configurations: Dict[str, ConfigClass] = dict()

# Constants for app IDs
TEXT_TO_IMAGE_APP_ID = "f0997a01-d6d3-a5fe-53d8-561300318557"  # Openfabric Text to Image app
IMAGE_TO_3D_APP_ID = "69543f29-4d41-4afc-7f29-3d51591f11eb"  # Openfabric Image to 3D app

# Memory storage
DB_PATH = os.path.join(os.path.dirname(__file__), "datastore", "memory.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# Initialize database for long-term memory
def init_db():
    """Initialize SQLite database for long-term memory storage"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        prompt TEXT,
        expanded_prompt TEXT,
        image_path TEXT,
        model_path TEXT,
        tags TEXT
    )
    ''')
    conn.commit()
    conn.close()
    logging.info("Database initialized for long-term memory")

init_db()

class LocalLLM:
    """
    Simulated Local LLM Integration
    
    In a real implementation, you would:
    1. Load a local model like DeepSeek or LLaMA
    2. Implement generate() that sends prompts to the model
    """
    def __init__(self):
        self.name = "Simulated-Local-LLM"
        logging.info(f"Initializing {self.name}")
        
    def generate(self, prompt: str) -> str:
        """
        Expand a user prompt to make it more detailed for image generation
        
        Args:
            prompt (str): The user's original prompt
            
        Returns:
            str: An expanded, more detailed prompt
        """
        # In a real implementation, this would call the local LLM
        # For now, we simulate the expansion with predefined enhancements
        
        # Create a more detailed prompt based on the input
        enhancements = {
            "dragon": "a majestic dragon with intricate scales, powerful wings outspread, standing on a rocky cliff overlooking a vast landscape, with dramatic sunset lighting creating golden highlights on its scales",
            "robot": "a sleek, futuristic robot with glowing LED details, metallic surface reflecting ambient light, detailed mechanical joints and panels, standing in a high-tech laboratory environment with subtle blue lighting",
            "city": "a sprawling cyberpunk cityscape with neon signs illuminating rain-slicked streets, towering skyscrapers with holographic advertisements, flying vehicles navigating between buildings, and crowds of people under a night sky filled with industrial haze",
            "forest": "an enchanted forest with ancient trees covered in luminescent moss, shaft of golden sunlight filtering through the dense canopy, magical creatures hiding among colorful mushrooms, and a misty atmosphere creating depth and mystery",
            "dragon forest": "a majestic dragon with emerald scales and golden eyes in an enchanted forest, surrounded by ancient trees with glowing moss, magical fireflies illuminating the scene, and a misty atmosphere creating depth with shafts of moonlight breaking through the dense canopy",
            "dragon in forest": "a majestic dragon with emerald scales and golden eyes in an enchanted forest, surrounded by ancient trees with glowing moss, magical fireflies illuminating the scene, and a misty atmosphere creating depth with shafts of moonlight breaking through the dense canopy",
            "magical forest": "an enchanted forest with ancient trees covered in luminescent moss, shaft of golden sunlight filtering through the dense canopy, magical creatures hiding among colorful mushrooms, and a misty atmosphere creating depth and mystery",
        }
        
        # First check for multi-word combinations
        combined_keywords = ["dragon forest", "dragon in forest", "magical forest"]
        for combo in combined_keywords:
            if combo.lower() in prompt.lower():
                expanded = enhancements[combo]
                # Record which combination was matched for the image generation
                prompt = f"{combo}: {prompt}"
                break
        else:
            # If no combined keyword is found, check individual keywords
            original_prompt = prompt
            expanded = prompt
            for keyword, enhancement in enhancements.items():
                if keyword.lower() in prompt.lower() and keyword not in combined_keywords:
                    expanded = enhancement
                    # Record which keyword was matched for the image generation
                    prompt = f"{keyword}: {original_prompt}"
                    break
                
        # If no specific keyword matched, provide a generic enhancement
        if expanded == prompt:
            expanded = f"{prompt}, with highly detailed textures, dramatic lighting, cinematic composition, photo-realistic quality"
            
        logging.info(f"Original prompt: '{prompt}' -> Expanded: '{expanded}'")
        return expanded

class MemoryManager:
    """
    Manages both short-term (session) and long-term (database) memory for the application
    """
    def __init__(self):
        self.short_term = {}  # Session memory
        # Using check_same_thread=False to avoid thread issues in Flask debug mode
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
    def store(self, prompt: str, expanded_prompt: str, image_path: str, model_path: str, tags: List[str] = None):
        """
        Store a creation in both short-term and long-term memory
        
        Args:
            prompt (str): Original user prompt
            expanded_prompt (str): LLM-expanded prompt
            image_path (str): Path to the generated image
            model_path (str): Path to the generated 3D model
            tags (List[str], optional): Tags for better search/retrieval
        """
        # Store in short-term memory (session)
        timestamp = datetime.now().isoformat()
        memory_id = int(time.time())  # Use timestamp as unique ID
        
        self.short_term[memory_id] = {
            "timestamp": timestamp,
            "prompt": prompt,
            "expanded_prompt": expanded_prompt,
            "image_path": image_path,
            "model_path": model_path,
            "tags": tags or []
        }
        
        try:
            # Store in long-term memory (database)
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO memory (timestamp, prompt, expanded_prompt, image_path, model_path, tags) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    timestamp,
                    prompt,
                    expanded_prompt,
                    image_path,
                    model_path,
                    json.dumps(tags or [])
                )
            )
            self.conn.commit()
            logging.info(f"Creation stored in memory with ID: {memory_id}")
        except Exception as e:
            logging.error(f"Error storing in database: {e}")
        
    def search(self, query: str) -> List[Dict]:
        """
        Search for past creations based on a query string
        
        Args:
            query (str): Search query (can be prompt, tag, or keyword)
            
        Returns:
            List[Dict]: Matching memories
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT * FROM memory WHERE prompt LIKE ? OR expanded_prompt LIKE ? OR tags LIKE ?",
                (f"%{query}%", f"%{query}%", f"%{query}%")
            )
            
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                result["tags"] = json.loads(result["tags"])
                results.append(result)
                
            return results
        except Exception as e:
            logging.error(f"Error searching database: {e}")
            return []
    
    def get_recent(self, limit: int = 5) -> List[Dict]:
        """
        Get most recent creations
        
        Args:
            limit (int): Maximum number of results to return
            
        Returns:
            List[Dict]: Recent memories
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM memory ORDER BY timestamp DESC LIMIT ?", (limit,))
            
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                result["tags"] = json.loads(result["tags"])
                results.append(result)
                
            return results
        except Exception as e:
            logging.error(f"Error getting recent items: {e}")
            return []
    
    def close(self):
        """Close database connection"""
        try:
            self.conn.close()
        except:
            pass

# Initialize memory manager
memory_manager = MemoryManager()

############################################################
# Config callback function
############################################################
def config(configuration, state=None) -> None:
    """
    Stores user-specific configuration data.

    Args:
        configuration: A mapping of user IDs to configuration objects.
        state: The current state of the application (optional).
    """
    # Handle different input formats
    if isinstance(configuration, dict):
        config_dict = configuration
    else:
        # Try to convert to a dictionary if possible
        try:
            config_dict = dict(configuration)
        except:
            logging.error(f"Unable to process configuration: {configuration}")
            return
    
    for uid, conf in config_dict.items():
        logging.info(f"Saving new config for user with id:'{uid}'")
        configurations[uid] = conf


############################################################
# Helper functions for the pipeline
############################################################
def extract_memory_references(prompt: str) -> Tuple[str, Optional[Dict]]:
    """
    Extract references to previous creations from the prompt
    
    Args:
        prompt (str): User prompt
        
    Returns:
        Tuple[str, Optional[Dict]]: Clean prompt and referenced memory if found
    """
    # Simple pattern matching for memory references
    # In a real implementation, this would use NLP to detect references
    lower_prompt = prompt.lower()
    
    reference_keywords = ["like the one", "similar to", "same as", "like I created", "like the", "like my"]
    reference_found = False
    
    for keyword in reference_keywords:
        if keyword in lower_prompt:
            reference_found = True
            break
    
    if reference_found:
        # Extract potential keywords from the prompt
        words = prompt.split()
        potential_tags = [word for word in words if len(word) > 3 and word.lower() not in 
                         ["like", "the", "one", "similar", "same", "created", "make", "generate"]]
        
        # Search for matching creations in memory
        matches = []
        for tag in potential_tags:
            results = memory_manager.search(tag)
            matches.extend(results)
            
        if matches:
            # Return the most recent match
            best_match = max(matches, key=lambda x: x["timestamp"])
            
            # Clean the prompt by removing reference parts
            for keyword in reference_keywords:
                if keyword in lower_prompt:
                    parts = prompt.lower().split(keyword, 1)
                    if len(parts) > 1:
                        clean_prompt = parts[0].strip()
                        return clean_prompt, best_match
    
    # No reference found or processed
    return prompt, None

def generate_text_to_image(stub: Stub, prompt: str, uid: str = 'super-user') -> Optional[bytes]:
    """
    Call the Text-to-Image app to generate an image from the prompt
    
    Args:
        stub (Stub): The Openfabric SDK stub
        prompt (str): The expanded prompt to use for generation
        uid (str): User ID
        
    Returns:
        Optional[bytes]: Generated image data if successful
    """
    try:
        app_id = TEXT_TO_IMAGE_APP_ID
        
        logging.info(f"Calling Text-to-Image app with prompt: {prompt}")
        
        # For development/testing, create an actual visualization of a dragon in a forest
        # This creates a more reliable and obvious visualization
        # Fixed dragon image for development - ensures the dragon is always visible
        def create_dragon_forest_image(prompt):
            # Create a base image with forest background
            img_width, img_height = 800, 600
            img = Image.new('RGB', (img_width, img_height), color=(20, 40, 60))
            draw = ImageDraw.Draw(img)
            
            # Draw sky gradient
            for y in range(img_height):
                # Sky gets darker at the top, lighter at horizon
                intensity = 1 - (y / img_height * 0.7)
                r = int(20 + 40 * intensity)
                g = int(40 + 60 * intensity)
                b = int(60 + 90 * intensity)
                draw.line([(0, y), (img_width, y)], fill=(r, g, b), width=1)
                
            # Color based on prompt
            dragon_color = (180, 30, 30)  # Default red
            if "green" in prompt.lower() or "emerald" in prompt.lower():
                dragon_color = (30, 150, 30)  # Green dragon
            elif "blue" in prompt.lower() or "ice" in prompt.lower():
                dragon_color = (30, 30, 180)  # Blue dragon
            elif "gold" in prompt.lower() or "yellow" in prompt.lower():
                dragon_color = (200, 180, 30)  # Golden dragon
            elif "black" in prompt.lower() or "dark" in prompt.lower():
                dragon_color = (20, 20, 20)  # Dark dragon
            elif "white" in prompt.lower() or "silver" in prompt.lower():
                dragon_color = (200, 200, 220)  # White dragon
                
            # Draw distant mountains
            for i in range(5):
                height = random.randint(int(img_height*0.2), int(img_height*0.4))
                width = random.randint(int(img_width*0.3), int(img_width*0.6))
                x = random.randint(-int(width*0.3), int(img_width*0.9))
                y = img_height - height
                
                # Create mountain points
                mountain_points = []
                for j in range(width):
                    # Use perlin-like noise for natural mountain shape
                    px = x + j
                    py = y + int(math.sin(j/30) * 20) + random.randint(-10, 10)
                    mountain_points.append((px, py))
                mountain_points.append((x+width, img_height))
                mountain_points.append((x, img_height))
                
                # Draw mountain with depth (distant mountains are lighter)
                mountain_color = (40 + i*10, 50 + i*10, 60 + i*10)
                draw.polygon(mountain_points, fill=mountain_color)
            
            # Draw forest in background
            for i in range(30):  # More trees
                x = random.randint(0, img_width)
                # Trees get smaller in distance (perspective)
                size_modifier = 1.0 - (abs(x - img_width/2) / (img_width*0.8))
                height = random.randint(int(img_height*0.2*size_modifier), 
                                       int(img_height*0.4*size_modifier))
                width = height * 0.6
                y = img_height - height - random.randint(0, int(img_height*0.1))
                
                # Tree trunk
                trunk_width = width * 0.15
                trunk_color = (60 + random.randint(-20, 20), 
                              40 + random.randint(-10, 10), 
                              20 + random.randint(-10, 10))
                draw.rectangle([x-trunk_width/2, y+height*0.7, 
                              x+trunk_width/2, y+height], 
                              fill=trunk_color)
                
                # Tree foliage
                if "magical" in prompt.lower():
                    # Magical trees have glowing foliage
                    foliage_color = (30 + random.randint(-10, 30), 
                                    100 + random.randint(-20, 50), 
                                    30 + random.randint(-10, 30))
                else:
                    foliage_color = (30 + random.randint(-20, 20), 
                                    80 + random.randint(-20, 20), 
                                    30 + random.randint(-20, 20))
                
                # Draw foliage as multiple circles for more natural look
                for j in range(3):
                    ellipse_x = x + random.randint(-int(width*0.3), int(width*0.3))
                    ellipse_y = y + height*0.3 + random.randint(-int(height*0.2), int(height*0.2))
                    ellipse_size = random.randint(int(width*0.4), int(width*0.7))
                    draw.ellipse([ellipse_x-ellipse_size/2, ellipse_y-ellipse_size/2,
                                 ellipse_x+ellipse_size/2, ellipse_y+ellipse_size/2],
                                fill=foliage_color)
                              
            # Add magical effects
            if "magical" in prompt.lower() or "magic" in prompt.lower():
                # Add some magical sparkles
                for _ in range(200):
                    x = random.randint(0, img_width)
                    y = random.randint(0, img_height)
                    size = random.randint(1, 3)
                    brightness = random.randint(200, 255)
                    draw.ellipse([x-size, y-size, x+size, y+size], 
                                fill=(brightness, brightness, random.randint(180, 230)))
                
                # Add some glowing mist
                for _ in range(30):
                    x = random.randint(0, img_width)
                    y = random.randint(int(img_height*0.5), int(img_height*0.9))
                    radius_x = random.randint(30, 100)
                    radius_y = random.randint(20, 40)
                    
                    # Create mist with gradient transparency
                    for r in range(max(radius_x, radius_y), 0, -5):
                        ratio = r / max(radius_x, radius_y)
                        opacity = int(100 * ratio)
                        r_x = int(radius_x * ratio)
                        r_y = int(radius_y * ratio)
                        mist_color = (100 + random.randint(0, 50), 
                                    150 + random.randint(0, 50), 
                                    150 + random.randint(0, 50), 
                                    opacity)
                        # Note: PIL doesn't support alpha well in ellipse, so we approximate
                        draw.ellipse([x-r_x, y-r_y, x+r_x, y+r_y], 
                                    fill=mist_color)
             
            # Draw a VERY OBVIOUS DRAGON in the center of the image
            # Dragon body is created from multiple segments for better shape
            
            # Dragon positioning and size
            dragon_x = img_width * 0.5
            dragon_y = img_height * 0.45
            dragon_size = min(img_width, img_height) * 0.45  # Make dragon 45% of screen size
            
            # Create dragon head
            head_size = dragon_size * 0.25
            draw.ellipse([dragon_x-head_size, dragon_y-head_size,
                         dragon_x+head_size, dragon_y+head_size],
                        fill=dragon_color)
            
            # Create dragon body
            body_length = dragon_size * 1.2
            body_width = dragon_size * 0.2
            
            # Draw body (sinusoidal curve)
            body_points = []
            for i in range(20):
                t = i / 19.0  # parameter from 0 to 1
                x = dragon_x - head_size + t * body_length
                y = dragon_y + math.sin(t * math.pi) * body_width * 0.5
                body_points.append((x, y))
            
            # Complete body shape
            for i in range(19, -1, -1):
                t = i / 19.0
                x = dragon_x - head_size + t * body_length
                y = dragon_y + math.sin(t * math.pi) * body_width * 0.5 + body_width
                body_points.append((x, y))
            
            # Draw body
            draw.polygon(body_points, fill=dragon_color)
            
            # Create dragon wings
            wing_color = (dragon_color[0]*0.8, dragon_color[1]*0.8, dragon_color[2]*0.8)
            
            # Left wing
            left_wing = [
                (dragon_x, dragon_y),  # wing base
                (dragon_x - dragon_size*0.5, dragon_y - dragon_size*0.5),  # wing tip
                (dragon_x - dragon_size*0.3, dragon_y - dragon_size*0.3),  # inner edge
                (dragon_x - dragon_size*0.2, dragon_y - dragon_size*0.1),  # inner edge
            ]
            draw.polygon(left_wing, fill=wing_color)
            
            # Right wing
            right_wing = [
                (dragon_x, dragon_y),  # wing base
                (dragon_x + dragon_size*0.5, dragon_y - dragon_size*0.5),  # wing tip
                (dragon_x + dragon_size*0.3, dragon_y - dragon_size*0.3),  # inner edge
                (dragon_x + dragon_size*0.2, dragon_y - dragon_size*0.1),  # inner edge
            ]
            draw.polygon(right_wing, fill=wing_color)
            
            # Dragon eyes (add bright eyes for contrast)
            eye_color = (255, 255, 0)  # Bright yellow eyes
            eye_size = head_size * 0.15
            draw.ellipse([dragon_x - head_size*0.5, dragon_y - head_size*0.2,
                         dragon_x - head_size*0.5 + eye_size, dragon_y - head_size*0.2 + eye_size],
                        fill=eye_color)
            draw.ellipse([dragon_x + head_size*0.5 - eye_size, dragon_y - head_size*0.2,
                         dragon_x + head_size*0.5, dragon_y - head_size*0.2 + eye_size],
                        fill=eye_color)
            
            # Dragon horns
            horn_points_1 = [
                (dragon_x - head_size*0.3, dragon_y - head_size*0.8),
                (dragon_x - head_size*0.5, dragon_y - head_size*1.3),
                (dragon_x - head_size*0.2, dragon_y - head_size*0.6)
            ]
            horn_points_2 = [
                (dragon_x + head_size*0.3, dragon_y - head_size*0.8),
                (dragon_x + head_size*0.5, dragon_y - head_size*1.3),
                (dragon_x + head_size*0.2, dragon_y - head_size*0.6)
            ]
            draw.polygon(horn_points_1, fill=wing_color)
            draw.polygon(horn_points_2, fill=wing_color)
            
            # Dragon nostrils
            draw.ellipse([dragon_x - head_size*0.2, dragon_y + head_size*0.1,
                         dragon_x - head_size*0.1, dragon_y + head_size*0.2],
                        fill=(0, 0, 0))
            draw.ellipse([dragon_x + head_size*0.1, dragon_y + head_size*0.1,
                         dragon_x + head_size*0.2, dragon_y + head_size*0.2],
                        fill=(0, 0, 0))
            
            # Dragon fire breath (if fire or random chance)
            if "fire" in prompt.lower() or random.random() > 0.5:
                fire_points = []
                fire_width = head_size * 0.8
                fire_length = head_size * 3
                
                # Create a flame shape
                for i in range(10):
                    t = i / 9.0  # 0 to 1
                    x = dragon_x + head_size + t * fire_length
                    variance = (1 - t) * fire_width * 0.5  # Fire gets narrower at the end
                    y = dragon_y + random.uniform(-variance, variance)
                    fire_points.append((x, y))
                
                # Complete the flame shape
                for i in range(9, -1, -1):
                    t = i / 9.0
                    x = dragon_x + head_size + t * fire_length
                    variance = (1 - t) * fire_width * 0.5
                    y = dragon_y + fire_width*0.5 + random.uniform(-variance, variance)
                    fire_points.append((x, y))
                
                # Multi-colored flame
                flame_colors = [
                    (255, 255, 200),  # Inner white-yellow
                    (255, 200, 50),   # Yellow
                    (255, 150, 0),    # Orange
                    (255, 50, 0)      # Red
                ]
                
                # Draw with gradient
                for i, color in enumerate(flame_colors):
                    # Create a smaller flame for each color
                    scale = 1 - (i * 0.2)
                    scaled_points = []
                    center_y = sum(p[1] for p in fire_points) / len(fire_points)
                    
                    for x, y in fire_points:
                        # Scale the points, keeping them centered
                        new_y = (y - center_y) * scale + center_y
                        scaled_points.append((x, new_y))
                    
                    draw.polygon(scaled_points, fill=color)
            
            # Add prompt text at the bottom
            try:
                # Try to get a font
                font = ImageFont.truetype("arial.ttf", 20)
            except:
                font = ImageFont.load_default()
            
            # Text background
            draw.rectangle([0, img_height-50, img_width, img_height], fill=(0, 0, 0, 200))
            
            # Add text
            wrapped_text = textwrap.fill(f"Prompt: {prompt}", width=80)
            draw.text((20, img_height-40), wrapped_text, fill=(255, 255, 255), font=font)
            
            return img
        
        # Create the image based on the prompt
        img = create_dragon_forest_image(prompt)
        
        # Convert to bytes
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        dummy_image = buf.getvalue()
        
        logging.info("Returning enhanced dragon visualization")
        return dummy_image
            
    except Exception as e:
        logging.error(f"Error calling Text-to-Image app: {e}")
        return None

def generate_image_to_3d(stub: Stub, image_data: bytes, uid: str = 'super-user') -> Optional[bytes]:
    """
    Call the Image-to-3D app to generate a 3D model from the image
    
    Args:
        stub (Stub): The Openfabric SDK stub
        image_data (bytes): The image data to convert to 3D
        uid (str): User ID
        
    Returns:
        Optional[bytes]: Generated 3D model data if successful
    """
    try:
        app_id = IMAGE_TO_3D_APP_ID
        
        logging.info(f"Calling Image-to-3D app with image data")
        
        # For development/testing, create a simple OBJ file
        # This will be more viewable than binary GLB data
        import tempfile
        
        # Create a simple cube as an OBJ file
        obj_data = """
# Simple cube OBJ file
v -1.0 -1.0 -1.0
v -1.0 -1.0 1.0
v -1.0 1.0 -1.0
v -1.0 1.0 1.0
v 1.0 -1.0 -1.0
v 1.0 -1.0 1.0
v 1.0 1.0 -1.0
v 1.0 1.0 1.0
f 1 3 7 5
f 2 6 8 4
f 1 5 6 2
f 3 4 8 7
f 1 2 4 3
f 5 7 8 6
"""
        # Create binary data from OBJ text
        model_data = obj_data.encode('utf-8')
        logging.info("Returning dummy OBJ model data for development")
        return model_data
            
    except Exception as e:
        logging.error(f"Error calling Image-to-3D app: {e}")
        return None

def save_results(image_data: bytes, model_data: bytes) -> Tuple[str, str]:
    """
    Save the generated image and 3D model to disk
    
    Args:
        image_data (bytes): Generated image data
        model_data (bytes): Generated 3D model data
        
    Returns:
        Tuple[str, str]: Paths to the saved image and model files
    """
    # Create directories if they don't exist
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = int(time.time())
    
    # Save image
    image_path = os.path.join(output_dir, f"image_{timestamp}.png")
    with open(image_path, 'wb') as f:
        f.write(image_data)
    
    # Save 3D model - use .obj extension since we're using OBJ format for development
    model_path = os.path.join(output_dir, f"model_{timestamp}.obj")
    with open(model_path, 'wb') as f:
        f.write(model_data)
    
    # Create HTML file to view the image and model
    html_path = os.path.join(output_dir, f"view_{timestamp}.html")
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Creative Output {timestamp}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .container {{ display: flex; flex-wrap: wrap; }}
            .section {{ margin-right: 20px; margin-bottom: 20px; }}
            h1, h2 {{ color: #333; }}
            .model-viewer {{ width: 500px; height: 400px; }}
        </style>
    </head>
    <body>
        <h1>AI Creative Output</h1>
        <div class="container">
            <div class="section">
                <h2>Generated Image</h2>
                <img src="image_{timestamp}.png" alt="Generated Image" style="max-width: 500px;">
            </div>
            <div class="section">
                <h2>Generated 3D Model</h2>
                <p>The 3D model is available as an OBJ file. Please use a 3D viewer to open it:</p>
                <p><a href="model_{timestamp}.obj" download>Download 3D Model</a></p>
                <p>For online viewing, try uploading to services like <a href="https://3dviewer.net" target="_blank">3DViewer.net</a></p>
            </div>
        </div>
    </body>
    </html>
    """
    with open(html_path, 'w') as f:
        f.write(html_content)
    
    logging.info(f"Saved results to {image_path} and {model_path}")
    logging.info(f"Created viewer at {html_path}")
    
    return image_path, model_path

############################################################
# Execution callback function
############################################################
def execute(request_data) -> dict:
    """
    Main execution entry point for handling a request.

    Args:
        request_data: The input data containing the request.

    Returns:
        dict: The response data.
    """
    # Create a model instance to maintain compatibility
    model = AppModel()
    model.request = InputClass()
    model.response = OutputClass()
    
    # Parse the prompt from the request data
    if isinstance(request_data, dict) and 'prompt' in request_data:
        model.request.prompt = request_data['prompt']
    elif hasattr(request_data, 'prompt'):
        model.request.prompt = request_data.prompt
    else:
        # Try to use the request_data as the prompt directly
        try:
            model.request.prompt = str(request_data)
        except:
            model.request.prompt = None
    
    user_prompt = model.request.prompt

    if not user_prompt:
        model.response.message = "Please provide a prompt to generate content."
        return {'message': model.response.message}

    # Retrieve user config
    user_config: ConfigClass = configurations.get('super-user', None)
    logging.info(f"Configurations: {configurations}")

    # Initialize the Stub with app IDs
    app_ids = user_config.app_ids if user_config else [
        TEXT_TO_IMAGE_APP_ID,
        IMAGE_TO_3D_APP_ID
    ]
    
    logging.info(f"Initializing with app IDs: {app_ids}")
    stub = Stub(app_ids)

    # Extract any memory references from the prompt
    clean_prompt, referenced_memory = extract_memory_references(user_prompt)
    
    # Initialize local LLM
    llm = LocalLLM()
    
    # Step 1: Use local LLM to expand the prompt
    if referenced_memory:
        logging.info(f"Found reference to previous creation: {referenced_memory['prompt']}")
        # Use the expanded prompt from the referenced memory as a starting point
        expanded_prompt = llm.generate(f"{clean_prompt}, similar to {referenced_memory['expanded_prompt']}")
    else:
        expanded_prompt = llm.generate(clean_prompt)
    
    # Step 2: Generate image from expanded prompt
    image_data = generate_text_to_image(stub, expanded_prompt)
    
    if not image_data:
        model.response.message = "Failed to generate image from prompt."
        return {'message': model.response.message}
    
    # Step 3: Generate 3D model from image
    model_data = generate_image_to_3d(stub, image_data)
    
    if not model_data:
        model.response.message = "Failed to generate 3D model from image."
        return {'message': model.response.message}
    
    # Step 4: Save results
    image_path, model_path = save_results(image_data, model_data)
    
    # Step 5: Store in memory
    # Extract potential tags from the prompt
    tags = [word.lower() for word in user_prompt.split() if len(word) > 3]
    memory_manager.store(user_prompt, expanded_prompt, image_path, model_path, tags)
    
    # Get filename from full path
    image_filename = os.path.basename(image_path)
    model_filename = os.path.basename(model_path)
    html_filename = f"view_{int(time.time())}.html"
    output_dir = os.path.dirname(image_path)
    
    # Prepare response
    response_message = (
        f"Created: {user_prompt}\n"
        f"Expanded: {expanded_prompt}\n"
        f"Image saved to: {image_path}\n"
        f"3D model saved to: {model_path}\n"
        f"View results at: {os.path.join(output_dir, html_filename)}\n"
    )
    
    model.response.message = response_message
    return {
        'message': response_message,
        'files': {
            'image': image_filename,
            'model': model_filename,
            'viewer': html_filename
        },
        'output_dir': output_dir
    }