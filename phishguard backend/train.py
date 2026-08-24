import pandas as pd
from catboost import CatBoostClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, precision_score, recall_score, f1_score, confusion_matrix, accuracy_score
import numpy as np

# Load the Dataset
print("Loading Parquet dataset...")
df = pd.read_parquet('meajor_cleaned_preprocessed.parquet.gzip')

# Filter for Features and Target
features = [
    'subject', 'body', 'url_count', 
    'url_length_max', 'url_length_avg', 
    'url_subdom_max', 'url_subdom_avg', 
    'attachment_count', 'has_attachments', 'attachment_types'
]
target = 'label'

df = df[features + [target]].copy()

# Handle Missing Values
print("Preprocessing data...")
df['subject'] = df['subject'].fillna('no subject')
df['body'] = df['body'].fillna('no body')
df['url_count'] = df['url_count'].fillna(0).astype(int)
df['url_length_max'] = df['url_length_max'].fillna(0).astype(int)
df['url_length_avg'] = df['url_length_avg'].fillna(0.0).astype(float)
df['url_subdom_max'] = df['url_subdom_max'].fillna(0).astype(int)
df['url_subdom_avg'] = df['url_subdom_avg'].fillna(0.0).astype(float)
df['attachment_count'] = df['attachment_count'].fillna(0).astype(int)
df['has_attachments'] = df['has_attachments'].fillna(False).astype(bool)
df['attachment_types'] = df['attachment_types'].fillna('none')

# Map the training MIME types to the exact extensions your JS will extract
mime_mapping = {
    # 1. Documents & Spreadsheets
    'application/msword': 'docx',
    'application/vnd.ms-excel': 'xlsx',
    'application/msexcel': 'xlsx',
    'application/x-msexcel': 'xlsx',
    'application/x-ms-excel': 'xlsx',
    'application/mxexcel': 'xlsx',         # Likely a typo in the raw data, but maps to Excel
    'application/vnd.ms-powerpoint': 'pptx',
    'application/mspowerpoint': 'pptx',
    'application/x-mspowerpoint': 'pptx',
    'application/pdf': 'pdf',
    'application/rtf': 'rtf',
    'text/richtext': 'rtx',
    'application/x-wordperfect6.1': 'wpd',
    'application/x-wordperfect6': 'wpd',
    
    # 2. Text & Web
    'text/html': 'html',
    'text/plain': 'txt',
    'text/x-vcard': 'vcf',
    
    # 3. Images
    'image/jpeg': 'jpg',
    'image/pjpeg': 'jpg',
    'image/png': 'png',
    'image/gif': 'gif',
    'image/bmp': 'bmp',
    'image/tiff': 'tiff',
    
    # 4. Audio, Video & Flash
    'audio/mpeg': 'mp3',
    'audio/mp3': 'mp3',
    'video/mpeg': 'mpg',
    'video/x-ms-asf': 'wmv',
    'application/x-shockwave-flash': 'swf',
    
    # 5. Archives & Binaries
    'application/zip': 'zip',
    'application/x-zip-compressed': 'zip',
    'application/x-bzip': 'bz2',
    'application/octet-stream': 'bin',
    'application/applefile': 'applefile',
    'application/ms-tnef': 'dat',
    
    # 6. Signatures & Email Routing
    'application/pgp-signature': 'sig',
    'application/pkcs7-signature': 'p7s',
    'application/x-pkcs7-signature': 'p7s',
    'message/rfc822': 'eml',
    'message/delivery-status': 'dsn',
    
    # 7. Code, Logs & formatting
    'text/x-csrc': 'c',
    'text/x-objcsrc': 'm',
    'application/x-perl': 'pl',
    'text/x-diff': 'diff',
    'text/x-patch': 'patch',
    'text/x-log': 'log',
    'text/troff': 'tr',
    'application/x-dvi': 'dvi',
    'application/postscript': 'ps'
}

# Define the cleaning function
def clean_attachments(mime_string):
    # Catch the 'none' baseline
    if mime_string == 'none':
        return 'none'
    
    # Split multiple attachments
    mimes = mime_string.split(';')
    
    # Map them using our exhaustive dictionary
    extensions = [mime_mapping.get(m.strip(), 'unknown') for m in mimes]
    
    # Remove any stray empty strings
    extensions = [ext for ext in extensions if ext]
    
    # Join with spaces to match your JavaScript exactly
    return ' '.join(extensions)

# Apply the cleaning function to the attachment_types column
df['attachment_types'] = df['attachment_types'].apply(clean_attachments)

# Remove rows where the label is missing
df = df.dropna(subset=['label']) 
df['label'] = df['label'].astype(int)

# Split into Training and Testing Sets
X = df[features]
y = df[target]

print("Splitting data (80% Train, 20% Test)...")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, 
    test_size=0.2, 
    random_state=42, 
    stratify=y
)

# Define the exact feature subsets
feature_sets = {
    "Text Only": 
        ['subject', 'body'],
    "Text + URL": 
        ['subject', 'body', 'url_count', 'url_length_max', 'url_length_avg', 'url_subdom_max', 'url_subdom_avg'],
    "Text + Attachment": 
        ['subject', 'body', 'attachment_count', 'has_attachments', 'attachment_types'],
    "Text + URL + Attachment": 
        ['subject', 'body', 'url_count', 'url_length_max', 'url_length_avg', 'url_subdom_max', 'url_subdom_avg', 'attachment_count', 'has_attachments', 'attachment_types']
}

print("\n--- Feature Set Ablation Tests (Baseline 0.50 Threshold) ---")
print(f"{'Feature Set':<25} | {'Accuracy':<8} | {'Precision':<9} | {'Recall':<8} | {'F1-Score':<8}")
print("-" * 70)

for set_name, features in feature_sets.items():
    # Dynamically determine the text and categorical features for this specific subset
    # This prevents CatBoost from crashing if 'attachment_types' isn't in the 'Text Only' set
    current_text_features = [f for f in ['subject', 'body', 'attachment_types'] if f in features]
    current_cat_features = [f for f in ['has_attachments'] if f in features]
    
    # Filter the training and testing data
    X_train_sub = X_train[features]
    X_test_sub = X_test[features]
    
    # Initialize a fresh model for a fair test
    model_ablation = CatBoostClassifier(
        iterations=2000, # Use 500 or 1000 depending on your usual config
        loss_function='Logloss',
        eval_metric='F1',
        task_type="GPU",
        text_features=current_text_features,
        cat_features=current_cat_features,
        verbose=False,
        random_seed=42
    )
    
    # Train the model
    model_ablation.fit(
        X_train_sub, y_train,
        eval_set=(X_test_sub, y_test),
        early_stopping_rounds=50
    )
    
    # Predict using the baseline 0.50 threshold to compare raw algorithmic power
    preds = model_ablation.predict(X_test_sub)
    
    # Calculate metrics
    acc = accuracy_score(y_test, preds)
    prec = precision_score(y_test, preds)
    rec = recall_score(y_test, preds)
    f1 = f1_score(y_test, preds)
    
    # Print the row for the table
    print(f"{set_name:<25} | {acc:.4f}   | {prec:.4f}    | {rec:.4f}   | {f1:.4f}")

print("-" * 70)

# Configure and Train the CatBoost Model
print("Initializing CatBoost...")
model = CatBoostClassifier(
    iterations=2000,
    loss_function='Logloss',
    eval_metric='F1',
    task_type="GPU",
    random_seed=42,
    text_features=['subject', 'body', 'attachment_types'],
    cat_features=['has_attachments']
)

print("Starting training...")
model.fit(
    X_train, y_train,
    eval_set=(X_test, y_test),
    early_stopping_rounds=50,
    verbose=100
)

# Get the raw probabilities for the test set
probabilities = model.predict_proba(X_test)[:, 1]

print("\n--- Threshold Analysis Matrix ---")
for threshold in [0.50, 0.60, 0.70, 0.80, 0.85, 0.90, 0.95]:
    custom_preds = (probabilities >= threshold).astype(int)
    precision = precision_score(y_test, custom_preds)
    recall = recall_score(y_test, custom_preds)
    f1 = f1_score(y_test, custom_preds)
    print(f"Threshold: {threshold:.2f} | Precision: {precision:.4f} | Recall: {recall:.4f} | F1: {f1:.4f}")

print("\n--- Optimized Confusion Matrix (Threshold 0.85) ---")
final_preds = (probabilities >= 0.85).astype(int)
cm = confusion_matrix(y_test, final_preds)
print(f"True Negatives (TN): {cm[0][0]}")
print(f"False Positives (FP): {cm[0][1]}")
print(f"False Negatives (FN): {cm[1][0]}")
print(f"True Positives (TP): {cm[1][1]}")

# Evaluate and Save
print("\n--- Final Model Evaluation (Threshold 0.50) ---")
predictions = model.predict(X_test)
print(classification_report(y_test, predictions, target_names=['Benign (0)', 'Phishing (1)'], digits=4))

print("\n--- Final Model Evaluation (Threshold 0.85) ---")
print(classification_report(y_test, final_preds, target_names=['Benign (0)', 'Phishing (1)'], digits=4))

print("\nSaving model...")
model.save_model('phishguard.cbm')
print("✅ Model successfully saved as 'phishguard.cbm'.")
print("You can now boot up your FastAPI server!")