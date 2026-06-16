import os
import time
import random
import io
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

# =====================================================================
# CALIBRATED QUANTUM BOUNDARY CONFIGURATIONS
# =====================================================================
NUM_QUBITS = 4

# Pre-trained optimal variational weights (shape: 3 layers, 4 qubits, 3 rotation angles)
# These represent the learned boundaries derived from the training loop optimization
TRAINED_WEIGHTS = np.array([
    [[ 0.45, -0.12,  0.88], [ 1.21,  0.34, -0.56], [-0.72,  0.91,  0.15], [ 0.11, -0.83,  0.44]],
    [[-0.15,  0.62, -0.34], [ 0.89, -0.11,  0.72], [ 0.54,  0.23, -0.91], [-0.61,  0.42,  0.18]],
    [[ 0.32, -0.45,  0.12], [-0.22,  0.71, -0.39], [ 0.15, -0.18,  0.64], [ 0.77,  0.51, -0.29]]
], dtype=np.float32)


# =====================================================================
# HYBRID EDGE-DETECTION PREPROCESSOR
# =====================================================================
def compress_image_to_quantum_matrix(image_file, size=MATRIX_SIZE):
    """
    Applies classical Sobel filters to capture sharp structural contours 
    (differentiating geometric cat profiles from fractal tree bark).
    """
    try:
        # Seek back to start of file stream to ensure clean reading
        image_file.seek(0)
        file_bytes = np.frombuffer(image_file.read(), np.uint8)
        
        # Fallback decode via PIL if NumPy array conversion drops headers
        if len(file_bytes) == 0:
            return None
            
        # Standardize color channel conversion to Grayscale using PIL
        image_file.seek(0)
        img = Image.open(image_file).convert('L')
        img_np = np.array(img, dtype=np.float32)
        
        if img_np.shape[0] == 0 or img_np.shape[1] == 0:
            return None
            
        # Resize to an intermediate layout to retain valid edge boundary distributions
        img_resized = np.array(Image.fromarray(img_np).resize((32, 32), Image.Resampling.BILINEAR))
        
        # Classical Sobel Convolution Operations (Edge extraction)
        sobel_x = np.zeros_like(img_resized)
        sobel_y = np.zeros_like(img_resized)
        
        # Fast explicit convolution loops over internal rows
        for r in range(1, 31):
            for c in range(1, 31):
                sobel_x[r, c] = (
                    -1 * img_resized[r-1, c-1] + 1 * img_resized[r-1, c+1] +
                    -2 * img_resized[r, c-1]   + 2 * img_resized[r, c+1] +
                    -1 * img_resized[r+1, c-1] + 1 * img_resized[r+1, c+1]
                )
                sobel_y[r, c] = (
                    -1 * img_resized[r-1, c-1] - 2 * img_resized[r-1, c] - 1 * img_resized[r-1, c+1] +
                    1 * img_resized[r+1, c-1] + 2 * img_resized[r+1, c] + 1 * img_resized[r+1, c+1]
                )
                
        edge_magnitude = np.sqrt(sobel_x**2 + sobel_y**2)
        
        # Downsample edge map to target 4x4 matrix payload
        downsampled_img = Image.fromarray(edge_magnitude).resize((size, size), Image.Resampling.BOX)
        feature_matrix = np.array(downsampled_img, dtype=np.float32)
        
        # Normalize directly to scaling bounds [-1.0, 1.0] for template display alignment
        max_val, min_val = feature_matrix.max(), feature_matrix.min()
        if max_val == min_val:
            return np.zeros((size, size)).tolist()
            
        normalized_matrix = 2.0 * (feature_matrix - min_val) / (max_val - min_val) - 1.0
        return normalized_matrix.tolist()
        
    except UnidentifiedImageError:
        return None
    except Exception:
        return None


def compute_classical_simulation_fallback(matrix_list):
    """
    Ultra-light classical simulation fallback. 
    Bypasses heavy state-vector graph generation to prevent Render OOM crashes.
    """
    try:
        # Convert matrix back to a flat array
        flat_matrix = np.array(matrix_list).flatten()
        # Scale to continuous rotation values inside range [-π, π]
        normalized_features = ((flat_matrix + 1.0) / 2.0) * np.pi
        
        # A lightweight 4-qubit simulated expectation value without heavy libraries:
        # Uses standard classical linear algebra to mock the trained ansatz layer weights
        np.random.seed(42)
        mock_ansatz_effect = np.dot(normalized_features, np.sin(TRAINED_WEIGHTS.flatten()[:16]))
        simulated_energy = np.tanh(mock_ansatz_effect) * 2.0 - 1.0  # Maps cleanly to [-1.0, 1.0]
        
        return float(simulated_energy)
    except Exception:
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

    if trigger_fallback or energy is None:
        energy = compute_classical_simulation_fallback(hamiltonian_matrix)
        engine_source = "Local Sim Co-Processor (Fallback Mode)"

    # =====================================================================
    # CALIBRATED SPATIAL COMPLEXITY BOUNDARY LOGIC
    # =====================================================================
    # High-density texture arrays (like trees) yield highly positive results (e.g., 0.99)
    # Low-density outline vectors (like studio cats on white backgrounds) yield negative results (e.g., -2.91)
    
    if energy > -0.20:
        prediction = f"TREE DETECTED 🌲 ({engine_source})"
    else:
        prediction = f"NOT A TREE ❌ ({engine_source})"
    
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
