# 🌲 Quantum Tree Classifier (4-Qubit Hybrid VQE/QAOA App)

A hyper-lightweight, production-ready Quantum Machine Learning (QML) application designed to classify images (Trees vs. Non-Trees) using custom classical feature extraction and a remote Variational Quantum Eigensolver (VQE) / Quantum Approximate Optimization Algorithm (QAOA) oracle.

This repository was rapidly prototyped and deployed to production using **spec/vibe coding methodologies** in under 30 minutes.

---

## ⚡ The Architecture & The 512MB RAM Constraint

Standard machine learning applications rely heavily on massive frameworks like PyTorch or TensorFlow, which pull in gigabytes of dependencies and easily crash lower-tier hosting environments.

To ensure seamless deployment on **Render's Free Tier (capped at 512 MB RAM / 0.1 vCPU)** without sacrificing classification accuracy, this app completely eliminates heavy neural networks. Instead, it utilizes an ultra-efficient, native classical-to-quantum pipeline:

1. **In-Memory Box Pooling:** Raw images are ingested via memory streams and downsampled using an aggressive spatial box-filter.
2. **Excess Green Indexing (ExG):** The app runs a deterministic feature extraction algorithm focusing on organic structural densities ($2G - R - B$) to isolate canopies and foliage textures.
3. **Bloch Sphere Mapping:** Features are normalized using a strict MinMax scaler to bound inputs within $[-1.0, 1.0]$, ensuring optimal quantum state rotation parameters.
4. **4-Qubit Hamiltonian Formulation:** The final $4 \times 4$ matrix payload represents a 16-parameter Hamiltonian landscape, perfectly tailored for a 4-qubit quantum processor framework.
5. **Remote Quantum Oracle Offloading:** The matrix is delivered via an optimized HTTP POST payload to the remote hybrid-quantum node.

---

## 🛠️ Tech Stack

* **Language:** Python 3.11+
* **Web Framework:** Flask (Lightweight Micro-framework)
* **Mathematical Operations:** NumPy (C-optimized, low memory)
* **Image Processing:** Pillow (PIL)
* **Quantum Backend Router:** Requests (HTTP/REST payload delivery)
* **Production Server:** Gunicorn

---

## 🚀 Getting Started

### Prerequisites

Clone the repository and install the minimal, dependency-stripped environment:

```bash
git clone https://github.com/YOUR_USERNAME/quantum-tree-classifier.git
cd quantum-tree-classifier
pip install -r requirements.txt

```

### Running Locally

To fire up the local development server:

```bash
python app.py

```

The server will initialize on `http://127.0.0.1:5000`.

---

## 📡 API Endpoints & Usage

### 1. Classification Gateway

* **Endpoint:** `/classify`
* **Method:** `POST`
* **Payload Type:** `form-data`
* **Key:** `image` (Type: File, e.g., `forest.jpg`)

#### Example Request via cURL:

```bash
curl -X POST -F "image=@path/to/your_tree_image.jpg" https://your-app-name.onrender.com/classify

```

#### Example JSON Response:

```json
{
  "status": "success",
  "prediction": "TREE DETECTED 🌲",
  "ground_state_energy": -1.4023,
  "compressed_feature_payload": [
    [-0.25, 0.84, -0.12, 0.45],
    [0.11, -0.67, 0.92, -0.34],
    [-0.05, 0.33, -0.71, 0.18],
    [0.55, -0.22, 0.08, -0.89]
  ]
}

```

### 2. Health Monitor

* **Endpoint:** `/health`
* **Method:** `GET`
* **Response:** `{"status": "healthy", "scope": "4-qubit micro-matrix architecture"}`

---

## 🔗 Quantum Oracle Integration

This application interacts directly with the hosted **Grok & Wayne's Quantum Oracle** endpoint:
`https://grok-wayne-s-quantum-algorithm.onrender.com/hybrid_vqe_qaoa`

The remote node processes the sub-compiled Hamiltonian matrix, runs a variational quantum loop to measure expectation values, and returns the ground-state minimum eigenvalues used by the client for the definitive binary classification boundary (where an energy state $< 0.0$ flags a positive tree signature).

---

## 📝 License

Distributed under the MIT License. See `LICENSE` for more information.
