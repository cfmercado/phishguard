# PhishGuard - Development Setup Guide

PhishGuard is a phishing detection system consisting of a Python/FastAPI backend and a Chrome extension frontend that integrates with Gmail.

## Project Structure

```
phishguard/
├── phishguard backend/
│   ├── main.py                              # FastAPI server
│   ├── train.py                             # Model training script
│   ├── requirements.txt                     # Python dependencies
│   ├── phishguard.cbm                       # Trained CatBoost model
│   └── meajor_cleaned_preprocessed.parquet.gzip  # Training data
└── phishguard frontend/
    ├── manifest.json                        # Chrome extension manifest (V3)
    ├── package.json                         # Node dependencies
    ├── background.js                        # Background service worker
    └── src/
        ├── extension.js                     # Main extension logic
        ├── extensionInjector.js             # Content script injector
        ├── gmailJsLoader.js                 # Gmail JS loader
        └── style.css                        # Extension styling
```

## Prerequisites

Before setting up the project, ensure you have the following installed:

### Backend Requirements
- **Python** 3.9+
- **pip** (Python package manager)

### Frontend Requirements
- **Node.js** 18+ (includes npm)
- **Chrome** or Chromium-based browser (for testing the extension)

### Verification

Run the following commands to verify installations:

```bash
# Check Python version
python --version

# Check pip version
pip --version

# Check Node.js version
node --version

# Check npm version
npm --version
```

---

## Backend Setup

### Step 1: Navigate to Backend Directory

```bash
cd "phishguard backend"
```

### Step 2: Install Python Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- **fastapi** 0.136.0 - Web framework
- **uvicorn** 0.45.0 - ASGI server
- **pydantic** 2.13.3 - Data validation
- **pandas** 3.0.2 - Data processing
- **catboost** 1.2.10 - Machine learning model

### Step 3: Configure Environment (Optional)

If you need to set custom environment variables, create a `.env` file in the backend directory:

```bash
# .env example
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
```

### Step 4: Verify Model File

Ensure the trained model file is present:
- `phishguard.cbm` (trained CatBoost model)
- `meajor_cleaned_preprocessed.parquet.gzip` (training/reference data)

---

## Frontend Setup

### Step 1: Navigate to Frontend Directory

```bash
cd "phishguard frontend"
```

### Step 2: Install Dependencies

```bash
npm install
```

This will install:
- **gmail-js** - Gmail DOM/API integration
- **jquery** - DOM manipulation

### Step 3: Build the Extension

```bash
npm run build
```

This creates a `dist/` directory with bundled extension files.

### Step 4: Optional - Set Backend URL

Edit `background.js` to configure the backend endpoint:

```javascript
// For local development:
const BACKEND_URL = 'http://localhost:8000/predict';

// For production:
// const BACKEND_URL = 'https://phishguard-backend-1qg5.onrender.com/predict';
```

### Step 5: Load Extension in Chrome

1. Open **Chrome** and navigate to `chrome://extensions`
2. Enable **Developer mode** (toggle in top-right corner)
3. Click **Load unpacked**
4. Select the `phishguard frontend` folder
5. The extension should now appear in your extensions list

---

## Running the Application

### Start the Backend Server

From the `phishguard backend` directory:

```bash
# Using uvicorn directly
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

The backend will be available at: `http://localhost:8000`

**API Endpoint:**
- `POST /predict` - Accepts email features and returns phishing prediction

### Test the Extension

1. Open **Gmail** in Chrome
2. You should see a "Scan for Phishing" button added to each email
3. Click the button to analyze the email for phishing
4. The extension will send the email features to the backend
5. A modal will display the phishing risk verdict

### Training the Model (Optional)

To retrain the CatBoost model with updated data:

```bash
cd "phishguard backend"
python train.py
```

This script:
- Loads training data from `meajor_cleaned_preprocessed.parquet.gzip`
- Trains a new CatBoost classifier
- Saves the model to `phishguard.cbm`