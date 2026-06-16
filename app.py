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

# Adaptive Retry Parameters
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

def compute_classical_simulation_fallback(matrix_list):
    """
    Fallback Classical Solver: Executes an exact eigen-decomposition 
    to calculate the ground state energy when the remote Oracle is rate-limiting.
    """
    try:
        H = np.array(matrix_list, dtype=np.float32)
        # Ensure Hermitian symmetry for physical eigenvalue stability
        H_hermitian = 0.5 * (H + H.T)
        eigenvalues = np.linalg.eigvalsh(H_hermitian)
        # Return the lowest eigenvalue (Ground State Energy approximation)
        return float(np.min(eigenvalues))
    except Exception:
        # Uniform color or stable baseline default
        return 0.0

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
    
    # Track if we need to drop back to classical processing
    trigger_fallback = False
    energy = None
    engine_source = "Remote Quantum Oracle"

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(
                QUANTUM_ORACLE_URL, 
                json=payload, 
                headers=headers, 
                timeout=TIMEOUT_LIMIT
            )
            
            if response.status_code == 429:
                if attempt < MAX_RETRIES - 1:
                    sleep_time = (BASE_DELAY ** attempt) + random.uniform(0.3, 1.0)
                    print(f"Rate limited (429). Retrying in {sleep_time:.2f}s...")
                    time.sleep(sleep_time)
                    continue  
                else:
                    print("Remote rate limits exhausted. Activating local classical co-processor fallback.")
                    trigger_fallback = True
                    break

            if response.status_code != 200:
                print(f"Oracle returned error code {response.status_code}. Failing over to simulation.")
                trigger_fallback = True
                break
                
            quantum_result = response.json()
            energy = quantum_result.get("energy") if quantum_result.get("energy") is not None else quantum_result.get("eigenvalue")
            if energy is not None:
                break
                
        except (requests.exceptions.RequestException, Exception) as e:
            print(f"Transport layer error: {str(e)}. Swapping to simulation engine.")
            trigger_fallback = True
            break

    # Execute classical math simulation if the external node is down or congested
    if trigger_fallback or energy === None:
        energy = compute_classical_simulation_fallback(hamiltonian_matrix)
        engine_source = "Local Sim Co-Processor (Fallback Mode)"

    prediction = f"TREE DETECTED 🌲 ({engine_source})" if energy < 0.0 else f"NOT A TREE ❌ ({engine_source})"
    
    return jsonify({
        "status": "success",
        "prediction": prediction,
        "ground_state_energy": float(energy),
        "compressed_feature_payload": hamiltonian_matrix
    }), 200

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "limits": "512MB RAM constraint active"}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
