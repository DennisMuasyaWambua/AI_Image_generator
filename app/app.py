import argparse
import logging
import sys
from flask import Flask, request, jsonify

from main import execute, config
from ontology_dc8f06af066e4a7880a5938933236037.config import ConfigClass

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Create Flask app
app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "ok",
        "message": "AI Creative Partner API is running. Use POST /generate to create content."
    })

@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.json
        if not data or 'prompt' not in data:
            return jsonify({"error": "Missing 'prompt' in request"}), 400
        
        result = execute(data)
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error processing request: {e}")
        return jsonify({"error": str(e)}), 500

def initialize_app():
    """Initialize the app with default configuration"""
    default_config = {
        'super-user': ConfigClass()
    }
    default_config['super-user'].app_ids = [
        "f0997a01-d6d3-a5fe-53d8-561300318557.openfabric.network",
        "69543f29-4d41-4afc-7f29-3d51591f11eb.openfabric.network"
    ]
    config(default_config)
    logging.info("Application initialized with default configuration")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='AI Creative Partner')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to run the API on')
    parser.add_argument('--port', type=int, default=8888, help='Port to run the API on')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    
    args = parser.parse_args()
    
    # Initialize the app
    initialize_app()
    
    logging.info(f"Starting AI Creative Partner on {args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=args.debug)