import os
import time
import random
import requests
from flask import Flask, request, jsonify, render_template_string
from PIL import Image, UnidentifiedImageError
import numpy as np

# Import the clean visual dashboard module template explicitly
from dashboard import DASHBOARD_HTML

app = Flask(__name__)

# Core Environmental System Configurations
QUANTUM_ORACLE_URL = "https://grok-wayne-s-quantum-algorithm.onrender.com/hybrid_vqe_qaoa"
MATRIX_SIZE = 4 
TIMEOUT_LIMIT = 12.0  

# Rate-limiting recovery constants
MAX_RETRIES = 3
BASE_DELAY = 1.5

def compress_image_to_quantum_matrix(image_file, size=MATRIX_SIZE):
    """Transforms an image stream into a normalized 4x4 matrix payload."""
    try:
        img = Image.open(image_file)
        if img.width == 0 or img.height == 0:
            return None
            
        img = img.convert('RGB')
        img_resized = img.resize((size, size), Image.Resampling.BOX)
        img_array = np.array(img_resized, dtype=np.float32)
        
        r, g, b = img_array[:,:,0], img_array[:,:,1], img_array[:,:,2]
        exg = (2.0 * g) - r - b
        
        min_val, max_val = exg.min(), exg.max()
        if max_val == min_val:
            return np.zeros((size, size)).tolist()
            
        normalized_matrix = 2.0 * (exg - min_val) / (max_val - min_val) - 1.0
        return normalized_matrix.tolist()
        
    except UnidentifiedImageError:
        return None
    except Exception:
        return None

@app.route('/', methods=['GET'])
def render_dashboard():
    return render_template_string(DASHBOARD_HTML)

@app.route('/classify', methods=['POST'])
def classify_endpoint():
    if 'image' not in request.files:
        return jsonify({"status": "error", "code": "MISSING_PAYLOAD", "message": "Required multi-part form key 'image' missing."}), 400
        
    image_file = request.files['image']
    if image_file.filename == '':
        return jsonify({"status": "error", "code": "EMPTY_FILE", "message": "No file was selected."}), 400

    hamiltonian_matrix = compress_image_to_quantum_matrix(image_file)
    if hamiltonian_matrix is None:
        return jsonify({"status": "error", "code": "PROCESSING_FAILED", "message": "Invalid or corrupt image format."}), 422

    payload = {"hamiltonian_matrix": hamiltonian_matrix}
    headers = {"Content-Type": "application/json"}
    
    # Adaptive Backoff loop execution loop
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(
                QUANTUM_ORACLE_URL, 
                json=payload, 
                headers=headers, 
                timeout=TIMEOUT_LIMIT
            )
            
            # If hit by a rate limit, execute backoff delay logic
            if response.status_code == 429:
                if attempt < MAX_RETRIES - 1:
                    # Exponential spacing formula with decorrelated randomized jitter 
                    sleep_time = (BASE_DELAY ** attempt) + random.uniform(0.5, 1.5)
                    print(f"Rate limited (429). Backing off for {sleep_time:.2f} seconds. Attempt {attempt + 1}/{MAX_RETRIES}")
                    time.sleep(sleep_time)
                    continue  # Jump directly to next retry attempt loop
            
            # Handle standard non-200 processing rejections cleanly
            if response.status_code != 200:
                return jsonify({
                    "status": "error",
                    "code": f"ORACLE_FAULT_{response.status_code}",
                    "message": f"The remote quantum oracle rejected the matrix representation with code {response.status_code}.",
                    "oracle_details": response.text[:200]
                }), response.status_code
                
            quantum_result = response.json()
            energy = quantum_result.get("energy") if quantum_result.get("energy") is not None else quantum_result.get("eigenvalue")
                
            if energy is None:
                return jsonify({
                    "status": "error",
                    "code": "MALFORMED_ORACLE_RESPONSE",
                    "message": "Quantum oracle responded with a 200 OK, but output was missing computation keys."
                }), 502

            prediction = "TREE DETECTED 🌲" if energy < 0.0 else "NOT A TREE ❌"
            
            return jsonify({
                "status": "success",
                "prediction": prediction,
                "ground_state_energy": float(energy),
                "compressed_feature_payload": hamiltonian_matrix
            }), 200
            
        except requests.exceptions.Timeout:
            if attempt < MAX_RETRIES - 1:
                continue
            return jsonify({"status": "error", "code": "ORACLE_TIMEOUT", "message": "The remote quantum oracle connection timed out repeatedly."}), 504
            
        except requests.exceptions.RequestException as e:
            return jsonify({"status": "error", "code": "ORACLE_UNREACHABLE", "message": "Failed to link transport layer to quantum pool.", "technical_error": str(e)}), 503
            
        except Exception as e:
            return jsonify({"status": "error", "code": "INTERNAL_GATEWAY_FAULT", "message": "Unhandled tracking fault inside app runtime processing.", "technical_error": str(e)}), 500

    # Fallback response if all backoff retry passes are exhausted completely by rate limits
    return jsonify({
        "status": "error",
        "code": "RATE_LIMIT_EXHAUSTED",
        "message": "The remote quantum oracle is experiencing high load capacity. Please wait a moment before trying your image submission again."
    }), 429

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "limits": "512MB RAM constraint active"}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
