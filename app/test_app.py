import logging
import os
import base64
from typing import Dict, List
import time
import io
from PIL import Image, ImageDraw, ImageFont
import math
import random

from flask import Flask, request, jsonify, send_from_directory

# Import our ChromaDB memory manager
from datastore.chroma_memory import ChromaMemoryManager

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Create Flask app
app = Flask(__name__)

# Create directories if they don't exist
output_dir = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(output_dir, exist_ok=True)

# Initialize ChromaDB memory manager
memory_manager = ChromaMemoryManager()

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "ok",
        "message": "AI Image Generator API is running. Use POST /generate to create content.",
        "examples": [
            {"prompt": "A green dragon in a magical forest"},
            {"prompt": "A blue robot with glowing eyes"},
            {"prompt": "A futuristic city at night with neon lights"},
            {"prompt": "A ringed planet in space with stars"}
        ],
        "supported_types": ["dragon", "robot", "city", "space", "landscape"]
    })

@app.route('/output/<path:filename>', methods=['GET'])
def serve_output_file(filename):
    return send_from_directory(output_dir, filename, as_attachment=False)

@app.route('/similar', methods=['POST'])
def find_similar_images():
    """API endpoint to find images similar to a given prompt using ChromaDB"""
    try:
        data = request.json
        if not data or 'prompt' not in data:
            return jsonify({"error": "Missing 'prompt' in request"}), 400
            
        prompt = data['prompt']
        limit = data.get('limit', 5)  # Default to 5 results
        
        # Search for similar images
        similar_images = memory_manager.search_similar(prompt, limit)
        
        return jsonify({
            "message": f"Found {len(similar_images)} similar images",
            "results": similar_images
        })
    except Exception as e:
        logging.error(f"Error finding similar images: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
        
@app.route('/recent', methods=['GET'])
def get_recent_images():
    """API endpoint to get recent images"""
    try:
        limit = request.args.get('limit', 5, type=int)
        
        # Get recent images
        recent_images = memory_manager.get_recent(limit)
        
        return jsonify({
            "message": f"Found {len(recent_images)} recent images",
            "results": recent_images
        })
    except Exception as e:
        logging.error(f"Error getting recent images: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
        
@app.route('/keyword', methods=['POST'])
def search_by_keyword():
    """API endpoint to search images by keyword"""
    try:
        data = request.json
        if not data or 'keyword' not in data:
            return jsonify({"error": "Missing 'keyword' in request"}), 400
            
        keyword = data['keyword']
        limit = data.get('limit', 5)  # Default to 5 results
        
        # Search for images by keyword
        matching_images = memory_manager.keyword_search(keyword, limit)
        
        return jsonify({
            "message": f"Found {len(matching_images)} matching images",
            "results": matching_images
        })
    except Exception as e:
        logging.error(f"Error searching by keyword: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.json
        if not data or 'prompt' not in data:
            return jsonify({"error": "Missing 'prompt' in request"}), 400
            
        prompt = data['prompt']
        logging.info(f"Received prompt: {prompt}")
        
        # Generate the image
        image = create_ai_image(prompt)
        
        # Save the images
        timestamp = int(time.time())
        
        # Save image
        image_filename = f"image_{timestamp}.png"
        image_path = os.path.join(output_dir, image_filename)
        image.save(image_path, format='PNG')
        
        # Create dummy 3D model file
        model_filename = f"model_{timestamp}.obj"
        model_path = os.path.join(output_dir, model_filename)
        
        with open(model_path, 'w') as f:
            f.write("""# Simple cube OBJ file
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
f 5 7 8 6""")
        
        # Determine image type for title
        prompt_lower = prompt.lower()
        image_type_label = "Image"
        if "dragon" in prompt_lower:
            image_type_label = "Dragon"
        elif "robot" in prompt_lower:
            image_type_label = "Robot"
        elif "city" in prompt_lower:
            image_type_label = "City"
        elif "space" in prompt_lower:
            image_type_label = "Space"
        
        # Create HTML viewer
        html_filename = f"view_{timestamp}.html"
        html_path = os.path.join(output_dir, html_filename)
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>AI Image Generator Output {timestamp}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                .container {{ display: flex; flex-wrap: wrap; }}
                .section {{ margin-right: 20px; margin-bottom: 20px; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                h1, h2 {{ color: #333; }}
                .prompt {{ background-color: #f0f0f0; padding: 10px; border-radius: 4px; margin-bottom: 20px; font-style: italic; }}
                img {{ max-width: 100%; border-radius: 4px; }}
                a {{ color: #0066cc; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
                .button {{ display: inline-block; background-color: #0066cc; color: white; padding: 8px 16px; border-radius: 4px; margin-top: 10px; }}
                .button:hover {{ background-color: #0055aa; }}
            </style>
        </head>
        <body>
            <h1>AI Image Generator</h1>
            <div class="prompt">
                <p><strong>Prompt:</strong> {prompt}</p>
            </div>
            <div class="container">
                <div class="section">
                    <h2>Generated {image_type_label}</h2>
                    <img src="/output/{image_filename}" alt="Generated Image" style="max-width: 800px;">
                </div>
                <div class="section">
                    <h2>3D Model</h2>
                    <p>A 3D model representation is available as an OBJ file:</p>
                    <p><a href="/output/{model_filename}" download class="button">Download 3D Model</a></p>
                    <p>Use the 3D Model Browser in the app to view this model interactively.</p>
                </div>
            </div>
            <div style="margin-top: 20px; text-align: center; color: #666; font-size: 0.8em;">
                Generated on {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))}
            </div>
        </body>
        </html>
        """
        
        with open(html_path, 'w') as f:
            f.write(html_content)
        
        # Store in ChromaDB for memory and similarity search
        # Extract potential tags from the prompt
        tags = [word.lower() for word in prompt.split() if len(word) > 3]
        memory_manager.store(prompt, prompt, image_path, model_path, tags)
        
        # Prepare response
        response = {
            'message': f"Created image from prompt: {prompt}",
            'files': {
                'image': f"/output/{image_filename}",
                'model': f"/output/{model_filename}",
                'viewer': f"/output/{html_filename}"
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        logging.error(f"Error processing request: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

# AI image creation function
def create_ai_image(prompt):
    # Create a more lifelike image with enhanced details
    img_width, img_height = 800, 600
    # Start with a gradient background for more depth
    img = Image.new('RGB', (img_width, img_height), color=(20, 40, 60))
    draw = ImageDraw.Draw(img)
    
    # Determine image type based on prompt
    prompt_lower = prompt.lower()
    image_type = "landscape"  # Default
    
    if any(keyword in prompt_lower for keyword in ["dragon", "drake", "wyvern", "serpent"]):
        image_type = "dragon"
    elif any(keyword in prompt_lower for keyword in ["robot", "mech", "android", "machine"]):
        image_type = "robot"
    elif any(keyword in prompt_lower for keyword in ["city", "urban", "metropolis", "building"]):
        image_type = "city"
    elif any(keyword in prompt_lower for keyword in ["space", "galaxy", "planet", "star"]):
        image_type = "space"
    
    logging.info(f"Detected image type: {image_type}")
    
    # Draw sky gradient based on image type
    for y in range(img_height):
        # Sky gets darker at the top, lighter at horizon
        intensity = 1 - (y / img_height * 0.7)
        
        if image_type == "space":
            # Dark space background with stars
            r = int(10 + 10 * intensity)
            g = int(10 + 15 * intensity)
            b = int(30 + 40 * intensity)
        elif image_type == "city":
            # Urban sky with pollution haze
            r = int(60 + 20 * intensity)
            g = int(60 + 15 * intensity)
            b = int(80 + 30 * intensity)
        else:
            # Standard sky gradient
            r = int(20 + 40 * intensity)
            g = int(40 + 60 * intensity)
            b = int(60 + 90 * intensity)
            
        draw.line([(0, y), (img_width, y)], fill=(r, g, b), width=1)
    
    # Color based on prompt
    main_color = (180, 30, 30)  # Default red
    if "green" in prompt_lower or "emerald" in prompt_lower:
        main_color = (30, 150, 30)  # Green
    elif "blue" in prompt_lower or "sapphire" in prompt_lower or "ice" in prompt_lower:
        main_color = (30, 30, 180)  # Blue
    elif "gold" in prompt_lower or "yellow" in prompt_lower:
        main_color = (200, 180, 30)  # Golden
    elif "black" in prompt_lower or "dark" in prompt_lower:
        main_color = (20, 20, 20)  # Dark
    elif "white" in prompt_lower or "silver" in prompt_lower:
        main_color = (200, 200, 220)  # White
    elif "purple" in prompt_lower or "violet" in prompt_lower or "amethyst" in prompt_lower:
        main_color = (120, 30, 160)  # Purple
    elif "orange" in prompt_lower or "amber" in prompt_lower:
        main_color = (220, 120, 30)  # Orange
    elif "pink" in prompt_lower or "rose" in prompt_lower:
        main_color = (220, 120, 180)  # Pink
    
    # For backward compatibility with dragon colors
    dragon_color = main_color
        
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
    
    # Draw more realistic forest in background
    # First layer - distant trees (more blue/hazy for atmospheric perspective)
    for i in range(40):  # More trees for denser forest
        x = random.randint(0, img_width)
        # Trees get smaller in distance (perspective)
        distance_from_center = abs(x - img_width/2) / (img_width*0.8)
        size_modifier = 1.0 - distance_from_center
        height = random.randint(int(img_height*0.2*size_modifier), 
                               int(img_height*0.4*size_modifier))
        width = height * 0.6
        y = img_height - height - random.randint(0, int(img_height*0.1))
        
        # Add atmospheric perspective (more blue/hazy with distance)
        distance_factor = distance_from_center * 0.7  # How hazy it gets
        
        # Tree trunk with texture suggestion
        trunk_width = width * 0.15
        trunk_base_color = (60, 40, 20)  # Base brown
        # Add atmospheric blue to distant trees
        trunk_color = (
            int(trunk_base_color[0] * (1-distance_factor) + 100 * distance_factor), 
            int(trunk_base_color[1] * (1-distance_factor) + 120 * distance_factor),
            int(trunk_base_color[2] * (1-distance_factor) + 140 * distance_factor)
        )
        
        # Draw trunk with slight random variations for texture
        draw.rectangle([x-trunk_width/2, y+height*0.7, 
                      x+trunk_width/2, y+height], 
                      fill=trunk_color)
        
        # Tree foliage with enhanced colors 
        if "magical" in prompt.lower():
            # Magical trees have glowing foliage with more variation
            base_green = 100 + random.randint(-10, 30)
            glow_factor = random.randint(30, 80)
            foliage_color = (
                30 + glow_factor//3,  # Some red
                base_green,           # Strong green
                30 + glow_factor      # Blue glow for magical effect
            )
        else:
            # Natural trees with more realistic coloring
            season_variation = random.randint(-20, 20)
            foliage_color = (
                30 + season_variation,             # Red/brown component
                80 + random.randint(-10, 30),      # Green component
                30 + int(distance_factor * 100)    # Blue increases with distance
            )
            
        # Create more natural tree shapes with multiple overlapping circles
        for j in range(5):  # More circles for more complex shape
            ellipse_x = x + random.randint(-int(width*0.4), int(width*0.4))
            ellipse_y = y + height*0.3 + random.randint(-int(height*0.25), int(height*0.25))
            ellipse_size = random.randint(int(width*0.4), int(width*0.7))
            
            # Slightly vary colors for more natural look
            color_variation = random.randint(-15, 15)
            varied_color = (
                max(0, min(255, foliage_color[0] + color_variation)),
                max(0, min(255, foliage_color[1] + color_variation)),
                max(0, min(255, foliage_color[2] + color_variation))
            )
            
            draw.ellipse([ellipse_x-ellipse_size/2, ellipse_y-ellipse_size/2,
                         ellipse_x+ellipse_size/2, ellipse_y+ellipse_size/2],
                        fill=varied_color)
                      
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
    
    # Create more detailed lifelike dragon
    
    # Create dragon head with more realistic shape
    head_size = dragon_size * 0.25
    # Create elongated head shape for more reptilian look
    head_length = head_size * 1.4
    head_width = head_size * 0.9
    
    # Head base - slightly elongated ellipse
    draw.ellipse([
        dragon_x - head_width,
        dragon_y - head_width,
        dragon_x + head_length,
        dragon_y + head_width
    ], fill=dragon_color)
    
    # Add snout extension
    snout_points = [
        (dragon_x + head_length - head_width*0.3, dragon_y - head_width*0.4),  # Top corner
        (dragon_x + head_length + head_width*0.3, dragon_y),                  # Tip of snout
        (dragon_x + head_length - head_width*0.3, dragon_y + head_width*0.4),  # Bottom corner
        (dragon_x + head_length - head_width*0.5, dragon_y)                   # Connection back to head
    ]
    draw.polygon(snout_points, fill=dragon_color)
    
    # Create more detailed dragon body with scales suggestion
    body_length = dragon_size * 1.2
    body_width = dragon_size * 0.22
    
    # Draw main body curved shape
    body_points = []
    # Use more points for smoother curve
    for i in range(30):
        t = i / 29.0  # parameter from 0 to 1
        x = dragon_x - head_width + t * body_length
        # Use double sin wave for more organic snake-like shape
        y = dragon_y + math.sin(t * math.pi) * body_width * 0.5 + math.sin(t * math.pi * 3) * body_width * 0.1
        body_points.append((x, y))
    
    # Complete body shape
    for i in range(29, -1, -1):
        t = i / 29.0
        x = dragon_x - head_width + t * body_length
        # Bottom curve has slight difference for more natural organic shape
        y = dragon_y + math.sin(t * math.pi) * body_width * 0.5 + math.sin(t * math.pi * 2.5) * body_width * 0.15 + body_width * 0.9
        body_points.append((x, y))
    
    # Draw main body
    draw.polygon(body_points, fill=dragon_color)
    
    # Add scale texture suggestion
    scale_color = (
        int(max(0, dragon_color[0] * 0.85)),
        int(max(0, dragon_color[1] * 0.85)),
        int(max(0, dragon_color[2] * 0.85))
    )
    
    # Add scale pattern along spine (simple suggestion of scales)
    spine_x = dragon_x + body_length * 0.5
    spine_y = dragon_y - body_width * 0.1
    
    for i in range(10): 
        scale_x = dragon_x + i * (body_length * 0.1)
        scale_size = body_width * 0.15
        # Zigzag pattern up and down spine
        offset = (i % 2) * scale_size * 0.4
        
        draw.ellipse([
            scale_x - scale_size,
            spine_y - scale_size + offset,
            scale_x + scale_size,
            spine_y + scale_size + offset
        ], outline=scale_color)
    
    # Create more realistic dragon wings with bone/membrane structure
    # Base wing colors
    wing_color = (int(dragon_color[0]*0.8), int(dragon_color[1]*0.8), int(dragon_color[2]*0.8))
    membrane_color = (int(dragon_color[0]*0.6), int(dragon_color[1]*0.6), int(dragon_color[2]*0.6))
    bone_color = (min(255, int(dragon_color[0]*1.2)), 
                  min(255, int(dragon_color[1]*1.2)), 
                  min(255, int(dragon_color[2]*1.2)))
    
    # Wing attachment points on body
    wing_base_y = dragon_y - body_width * 0.3
    
    # Left wing - main shape
    left_wing_base_x = dragon_x - body_width * 0.5
    
    # Wing bone structure points
    wing_length = dragon_size * 0.8
    wing_height = dragon_size * 0.6
    
    # Main supporting bones
    left_bone1 = [
        (left_wing_base_x, wing_base_y),  # Attachment to body
        (left_wing_base_x - wing_length * 0.9, wing_base_y - wing_height * 0.9)  # Tip of wing
    ]
    
    left_bone2 = [
        (left_wing_base_x, wing_base_y),  # Attachment to body
        (left_wing_base_x - wing_length * 0.8, wing_base_y - wing_height * 0.5)  # Middle bone
    ]
    
    left_bone3 = [
        (left_wing_base_x, wing_base_y),  # Attachment to body
        (left_wing_base_x - wing_length * 0.7, wing_base_y - wing_height * 0.2)  # Lower bone
    ]
    
    # Draw left wing membrane (filled polygon)
    left_wing = [
        left_wing_base_x, wing_base_y,  # Wing base
        left_bone1[1][0], left_bone1[1][1],  # Main tip
        left_bone1[1][0] + wing_length * 0.1, left_bone1[1][1] + wing_height * 0.1,  # Curve
        left_bone2[1][0], left_bone2[1][1],  # Middle point
        left_bone2[1][0] + wing_length * 0.1, left_bone2[1][1] + wing_height * 0.1,  # Curve
        left_bone3[1][0], left_bone3[1][1],  # Lower point
        left_bone3[1][0] + wing_length * 0.1, left_bone3[1][1] + wing_height * 0.2,  # Lower curve
        left_wing_base_x - wing_length * 0.3, wing_base_y + wing_height * 0.1,  # Bottom edge
    ]
    draw.polygon(left_wing, fill=membrane_color)
    
    # Draw wing bones - thicker lines for more visibility
    for bone in [left_bone1, left_bone2, left_bone3]:
        for width in range(3):  # Multiple lines for thickness
            offset = width - 1
            draw.line([
                (bone[0][0], bone[0][1] + offset), 
                (bone[1][0], bone[1][1] + offset)
            ], fill=bone_color, width=2)
    
    # Right wing - mirror of left wing
    right_wing_base_x = dragon_x + body_width * 0.5
    
    # Right wing bones
    right_bone1 = [
        (right_wing_base_x, wing_base_y),  # Attachment to body
        (right_wing_base_x + wing_length * 0.9, wing_base_y - wing_height * 0.9)  # Tip of wing
    ]
    
    right_bone2 = [
        (right_wing_base_x, wing_base_y),  # Attachment to body
        (right_wing_base_x + wing_length * 0.8, wing_base_y - wing_height * 0.5)  # Middle bone
    ]
    
    right_bone3 = [
        (right_wing_base_x, wing_base_y),  # Attachment to body
        (right_wing_base_x + wing_length * 0.7, wing_base_y - wing_height * 0.2)  # Lower bone
    ]
    
    # Draw right wing membrane
    right_wing = [
        right_wing_base_x, wing_base_y,  # Wing base
        right_bone1[1][0], right_bone1[1][1],  # Main tip
        right_bone1[1][0] - wing_length * 0.1, right_bone1[1][1] + wing_height * 0.1,  # Curve
        right_bone2[1][0], right_bone2[1][1],  # Middle point
        right_bone2[1][0] - wing_length * 0.1, right_bone2[1][1] + wing_height * 0.1,  # Curve
        right_bone3[1][0], right_bone3[1][1],  # Lower point
        right_bone3[1][0] - wing_length * 0.1, right_bone3[1][1] + wing_height * 0.2,  # Lower curve
        right_wing_base_x + wing_length * 0.3, wing_base_y + wing_height * 0.1,  # Bottom edge
    ]
    draw.polygon(right_wing, fill=membrane_color)
    
    # Draw right wing bones
    for bone in [right_bone1, right_bone2, right_bone3]:
        for width in range(3):  # Multiple lines for thickness
            offset = width - 1
            draw.line([
                (bone[0][0], bone[0][1] + offset), 
                (bone[1][0], bone[1][1] + offset)
            ], fill=bone_color, width=2)
    
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
    
    # Draw additional elements based on image type
    if image_type == "space" and "dragon" not in prompt_lower:
        # Add stars
        for _ in range(500):
            x = random.randint(0, img_width)
            y = random.randint(0, int(img_height * 0.8))
            size = random.random() * 2
            brightness = random.randint(180, 255)
            draw.ellipse([x-size, y-size, x+size, y+size], 
                        fill=(brightness, brightness, brightness))
        
        # Add a planet
        planet_x = random.randint(int(img_width*0.2), int(img_width*0.8))
        planet_y = random.randint(int(img_height*0.2), int(img_height*0.5))
        planet_size = random.randint(50, 120)
        
        # Planet color based on main_color
        planet_color = (main_color[0], main_color[1], main_color[2])
        
        # Draw planet
        draw.ellipse([planet_x-planet_size, planet_y-planet_size, 
                      planet_x+planet_size, planet_y+planet_size], 
                    fill=planet_color)
        
        # Add rings if mentioned in prompt
        if "ring" in prompt_lower or "saturn" in prompt_lower:
            # Draw elliptical rings
            for ring_size in range(planet_size+10, planet_size+40, 5):
                ring_color = (planet_color[0]//2 + 50, planet_color[1]//2 + 50, planet_color[2]//2 + 50)
                draw.arc([planet_x-ring_size, planet_y-ring_size//3, 
                          planet_x+ring_size, planet_y+ring_size//3], 
                         0, 360, fill=ring_color, width=3)
    
    elif image_type == "city" and "dragon" not in prompt_lower:
        # Draw cityscape silhouette
        skyline_height = int(img_height * 0.7)
        base_y = skyline_height
        
        # Generate buildings
        for x in range(0, img_width, random.randint(10, 40)):
            building_width = random.randint(20, 60)
            building_height = random.randint(50, 250)
            building_color = (
                random.randint(20, 50),
                random.randint(20, 50),
                random.randint(30, 60)
            )
            
            # Draw building
            draw.rectangle([x, base_y-building_height, x+building_width, base_y], 
                          fill=building_color, outline=(60, 60, 70))
            
            # Add windows
            window_color = (200, 200, 100)
            if "night" in prompt_lower:
                for wy in range(base_y-building_height+10, base_y-10, 20):
                    for wx in range(x+5, x+building_width-5, 10):
                        if random.random() > 0.3:  # Some windows are dark
                            window_size = 5
                            draw.rectangle([wx, wy, wx+window_size, wy+window_size], 
                                          fill=window_color)
            
        # Add road in foreground
        road_y = int(img_height * 0.7)
        draw.rectangle([0, road_y, img_width, img_height], fill=(40, 40, 40))
        
        # Road markings
        line_y = road_y + (img_height - road_y) // 2
        for x in range(0, img_width, 40):
            draw.rectangle([x, line_y, x+20, line_y+5], fill=(200, 200, 200))
            
        # Add a few lights/cars
        for _ in range(10):
            light_x = random.randint(0, img_width)
            light_y = random.randint(road_y+10, img_height-10)
            light_size = random.randint(2, 6)
            light_color = (255, 200, 0) if random.random() > 0.5 else (255, 0, 0)
            
            draw.ellipse([light_x-light_size, light_y-light_size, 
                          light_x+light_size, light_y+light_size], 
                        fill=light_color)
    
    elif image_type == "robot" and "dragon" not in prompt_lower:
        # Draw a robot in the center
        robot_x = img_width // 2
        robot_y = img_height // 2
        robot_width = int(img_width * 0.3)
        robot_height = int(img_height * 0.5)
        
        # Robot head
        head_size = robot_width // 2
        head_color = main_color
        draw.rectangle([robot_x-head_size, robot_y-robot_height//2-head_size, 
                       robot_x+head_size, robot_y-robot_height//2+head_size], 
                      fill=head_color, outline=(50, 50, 50), width=3)
        
        # Robot eyes
        eye_color = (0, 200, 255)
        eye_size = head_size // 4
        draw.rectangle([robot_x-head_size//2-eye_size//2, robot_y-robot_height//2-eye_size, 
                       robot_x-head_size//2+eye_size//2, robot_y-robot_height//2], 
                      fill=eye_color)
        draw.rectangle([robot_x+head_size//2-eye_size//2, robot_y-robot_height//2-eye_size, 
                       robot_x+head_size//2+eye_size//2, robot_y-robot_height//2], 
                      fill=eye_color)
        
        # Robot body
        body_color = (head_color[0]//2, head_color[1]//2, head_color[2]//2)
        draw.rectangle([robot_x-robot_width//2, robot_y-robot_height//2+head_size, 
                       robot_x+robot_width//2, robot_y+robot_height//2], 
                      fill=body_color, outline=(50, 50, 50), width=3)
        
        # Robot limbs
        limb_color = (80, 80, 80)
        # Arms
        arm_width = robot_width // 6
        draw.rectangle([robot_x-robot_width//2-arm_width, robot_y-robot_height//4, 
                       robot_x-robot_width//2, robot_y+robot_height//4], 
                      fill=limb_color)
        draw.rectangle([robot_x+robot_width//2, robot_y-robot_height//4, 
                       robot_x+robot_width//2+arm_width, robot_y+robot_height//4], 
                      fill=limb_color)
        
        # Legs
        leg_width = robot_width // 4
        draw.rectangle([robot_x-robot_width//3, robot_y+robot_height//2, 
                       robot_x-robot_width//6, robot_y+robot_height//2+robot_height//3], 
                      fill=limb_color)
        draw.rectangle([robot_x+robot_width//6, robot_y+robot_height//2, 
                       robot_x+robot_width//3, robot_y+robot_height//2+robot_height//3], 
                      fill=limb_color)
        
        # Add tech details
        for _ in range(5):
            detail_x = random.randint(robot_x-robot_width//2+10, robot_x+robot_width//2-10)
            detail_y = random.randint(robot_y-robot_height//2+head_size+10, robot_y+robot_height//2-10)
            detail_size = random.randint(5, 15)
            detail_color = (0, 200, 255) if random.random() > 0.5 else (255, 50, 50)
            
            if random.random() > 0.5:
                draw.rectangle([detail_x-detail_size, detail_y-detail_size//2, 
                              detail_x+detail_size, detail_y+detail_size//2], 
                             fill=detail_color)
            else:
                draw.ellipse([detail_x-detail_size, detail_y-detail_size, 
                            detail_x+detail_size, detail_y+detail_size], 
                           fill=detail_color)
    
    # Add prompt text at the bottom
    try:
        # Try to get a font
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()
    
    # Text background
    draw.rectangle([0, img_height-50, img_width, img_height], fill=(0, 0, 0))
    
    # Add text
    draw.text((20, img_height-40), f"Prompt: {prompt}", fill=(255, 255, 255), font=font)
    
    return img

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888, debug=True)
