from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from catboost import CatBoostClassifier, Pool
import pandas as pd

app = FastAPI()

extension_id = "pphgcdgnccbnedonflhalbjaoffganmb"

# Allow Chrome extension to talk to the server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[f"chrome-extension://{extension_id}"],
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)

# Load trained model
model = CatBoostClassifier()
try:
    model.load_model('phishguard.cbm')
    print("✅ Model loaded successfully.")
except Exception as e:
    print(f"Warning: Model not found. Train your model first! Error: {e}")

# Define the expected JSON payload from the extension
class EmailData(BaseModel):
    subject: str
    body: str
    url_count: int
    url_length_max: int
    url_length_avg: float
    url_subdom_max: int
    url_subdom_avg: float
    attachment_count: int
    has_attachments: bool
    attachment_types: str

# A dictionary to translate model feature names into human-readable warnings
REASON_MAPPING = {
    'url_count': 'High number of links',
    'url_length_max': 'Suspiciously long links',
    'url_length_avg': 'Suspiciously long links',
    'url_subdom_max': 'Complex URL subdomains',
    'url_subdom_avg': 'Complex URL subdomains',
    'subject': 'Suspicious subject line',
    'body': 'Suspicious email content',
    'attachment_count': 'Unexpected number of attachments',
    'has_attachments': 'Contains attachments',
    'attachment_types': 'Suspicious attachment type'
}

# Health check endpoint to verify server is running
@app.get("/")
async def root():
    return {"status": "PhishGuard API is running online!"}

@app.post("/predict")
async def predict_phishing(email: EmailData):
    # Print the incoming payload to your terminal for live debugging
    # print("\n--- INCOMING PAYLOAD ---")
    # print(f"Subject: {email.subject}")
    # print(f"URL Count: {email.url_count} | Max Len: {email.url_length_max} | Avg Subdom: {email.url_subdom_avg:.2f}")
    # print(f"Attachments: {email.attachment_count} | Types: {email.attachment_types}")
    # print("------------------------\n")

    # Format the incoming data into a single-row DataFrame
    data = pd.DataFrame([{
        'subject': email.subject,
        'body': email.body,
        'url_count': email.url_count,
        'url_length_max': email.url_length_max,
        'url_length_avg': email.url_length_avg,
        'url_subdom_max': email.url_subdom_max,
        'url_subdom_avg': email.url_subdom_avg,
        'attachment_count': email.attachment_count,
        'has_attachments': email.has_attachments,
        'attachment_types': email.attachment_types
    }])

    # Run the prediction
    try:
        # predict_proba returns an array like [probability_benign, probability_phishing]
        probabilities = model.predict_proba(data)[0]
        phishing_confidence = probabilities[1] # Index 1 is the probability of class 1 (phishing)
        
        # Only flag if it is > 85% confident
        if phishing_confidence > 0.85:
            status = "phishing"

            # SHAP values will help us understand which features contributed most to the phishing prediction
            # Wrap data in a Pool, specifying the categorical and text features
            cat_features = ['has_attachments']
            text_features = ['subject', 'body', 'attachment_types']
            pool = Pool(
                data, 
                cat_features=cat_features,
                text_features=text_features
            )
            
            # Get SHAP values. The array includes the base value at the end, so we slice it [:-1]
            shap_values = model.get_feature_importance(pool, type='ShapValues')[0][:-1]
            
            # Zip feature names with their SHAP values
            contributions = list(zip(model.feature_names_, shap_values))
            
            # Sort by highest POSITIVE contribution (pushes prediction toward phishing)
            contributions.sort(key=lambda x: x[1], reverse=True)
            
            # Extract the top 2 features and map to human-readable strings
            top_features = [feat for feat, val in contributions if val > 0][:2]
            reasons = [REASON_MAPPING.get(feat, feat) for feat in top_features]

        else:
            status = "safe"
            reasons = []
        
        print(f"Returning status: {status} with confidence: {phishing_confidence:.2f}")
        if reasons:
            print(f"Top reasons: {', '.join(reasons)}")
            
        return {
            "status": status, 
            "confidence": round(phishing_confidence * 100, 2),
            "reasons": reasons
        }
        
    except Exception as e:
        print(f"Backend Error: {e}")
        return {"status": "error", "message": str(e)}