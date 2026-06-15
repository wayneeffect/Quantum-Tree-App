# dashboard.py

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quantum Tree Classifier Dashboard</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: #0f172a;
            color: #f8fafc;
            margin: 0;
            padding: 2rem;
            display: flex;
            justify-content: center;
        }
        .container {
            max-width: 800px;
            width: 100%;
            background: #1e293b;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
        }
        h1 { color: #38bdf8; margin-top: 0; border-bottom: 2px solid #334155; padding-bottom: 0.5rem; }
        .upload-box {
            border: 2px dashed #475569;
            padding: 2rem;
            text-align: center;
            border-radius: 8px;
            cursor: pointer;
            background: #0f172a;
            transition: border 0.2s;
        }
        .upload-box:hover { border-color: #38bdf8; }
        input[type="file"] { display: none; }
        button {
            background: #0284c7;
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            font-size: 1rem;
            border-radius: 6px;
            cursor: pointer;
            margin-top: 1rem;
            width: 100%;
            font-weight: bold;
        }
        button:hover { background: #0369a1; }
        .preview-img {
            max-width: 100%;
            max-height: 250px;
            margin-top: 1rem;
            border-radius: 6px;
            display: none;
        }
        .result-card {
            margin-top: 1.5rem;
            padding: 1.5rem;
            border-radius: 8px;
            background: #0f172a;
            display: none;
            border-left: 5px solid #64748b;
        }
        .matrix-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 5px;
            max-width: 200px;
            margin-top: 0.5rem;
        }
        .matrix-cell {
            background: #334155;
            padding: 5px;
            font-family: monospace;
            text-align: center;
            font-size: 0.85rem;
            border-radius: 4px;
        }
        .loading { display: none; color: #e2e8f0; font-style: italic; margin-top: 1rem; text-align: center;}
    </style>
</head>
<body>
    <div class="container">
        <h1>🌲 Quantum Tree Classifier Dashboard</h1>
        <p>Prototyped via Vibe Coding. Extracts 4x4 organic structural features ($2G-R-B$) and evaluates ground-state energies through a remote hybrid VQE/QAOA quantum oracle.</p>
        
        <form id="uploadForm">
            <div class="upload-box" onclick="document.getElementById('imageInput').click()">
                <p id="uploadText">📸 Click to upload or drag an image here</p>
                <input type="file" id="imageInput" name="image" accept="image/*" onchange="previewFile()">
                <img id="preview" class="preview-img" alt="Preview">
            </div>
            <button type="submit">Execute Quantum Classification</button>
        </form>

        <div id="loading" class="loading">⚡ Simulating Hamiltonian and waiting for Quantum Oracle Response...</div>

        <div id="resultCard" class="result-card">
            <h3>Prediction Outcome: <span id="predictionText"></span></h3>
            <p><strong>Ground State Expectation Energy:</strong> <span id="energyText"></span></p>
            <p><strong>Downsampled 4x4 Feature Matrix Mapping:</strong></p>
            <div id="matrixContainer" class="matrix-grid"></div>
        </div>
    </div>

    <script>
        function previewFile() {
            const preview = document.getElementById('preview');
            const file = document.getElementById('imageInput').files[0];
            const reader = new FileReader();

            reader.addEventListener("load", function () {
                preview.src = reader.result;
                preview.style.display = "block";
                document.getElementById('uploadText').style.display = "none";
            }, false);

            if (file) { reader.readAsDataURL(file); }
        }

        document.getElementById('uploadForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const fileInput = document.getElementById('imageInput');
            if (!fileInput.files[0]) { alert('Please select an image first.'); return; }

            const formData = new FormData();
            formData.append('image', fileInput.files[0]);

            document.getElementById('loading').style.display = 'block';
            document.getElementById('resultCard').style.display = 'none';

            try {
                const response = await fetch('/classify', { method: 'POST', body: formData });
                const data = await response.json();
                
                document.getElementById('loading').style.display = 'none';
                const card = document.getElementById('resultCard');
                card.style.display = 'block';

                if (data.status === 'success') {
                    document.getElementById('predictionText').innerText = data.prediction;
                    document.getElementById('energyText').innerText = data.ground_state_energy.toFixed(4);
                    
                    card.style.borderColor = data.prediction.includes('🌲') ? '#22c55e' : '#ef4444';

                    const matrixBox = document.getElementById('matrixContainer');
                    matrixBox.innerHTML = '';
                    data.compressed_feature_payload.forEach(row => {
                        row.forEach(val => {
                            const cell = document.createElement('div');
                            cell.className = 'matrix-cell';
                            cell.innerText = val.toFixed(2);
                            matrixBox.appendChild(cell);
                        });
                    });
                } else {
                    document.getElementById('predictionText').innerText = 'Error Mapping Execution';
                    document.getElementById('energyText').innerText = data.message || 'Unknown fault.';
                    card.style.borderColor = '#ef4444';
                }
            } catch (err) {
                document.getElementById('loading').style.display = 'none';
                alert('Network execution failure reaching local gateway handler.');
            }
        });
    </script>
</body>
</html>
"""
