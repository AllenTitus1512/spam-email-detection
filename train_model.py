from pathlib import Path
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
import joblib

# ================== CONFIG ==================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "model"
MODEL_PATH = MODEL_DIR / "phishing_email_model.joblib"

TEXT_COLUMN_CANDIDATES = ["email_text", "text", "body", "message", "content", "emails"]
LABEL_COLUMN_CANDIDATES = ["label", "labels", "target", "class", "category", "is_phishing", "spam"]

# ===========================================

def find_column(columns, candidates):
    normalized = {col.lower().replace(" ", "").replace("_", ""): col for col in columns}
    for candidate in candidates:
        key = candidate.lower().replace(" ", "").replace("_", "")
        if key in normalized:
            return normalized[key]
    return None


def normalize_label(value):
    """Normalize labels to 'phishing' or 'legitimate' format."""
    # Handle numeric labels (0 = legitimate, 1 = phishing)
    if isinstance(value, (int, float)):
        return "phishing" if value == 1 else "legitimate"
    
    text = str(value).strip().lower()
    if any(word in text for word in ["phishing", "spam", "fraud", "malicious", "1", "bad"]):
        return "phishing"
    if any(word in text for word in ["legitimate", "ham", "safe", "normal", "benign", "0", "good"]):
        return "legitimate"
    return text


def load_dataset():
    # Prefer merged dataset if it exists
    merged_path = DATA_DIR / "merged_dataset.csv"
    if merged_path.exists():
        dataset_path = merged_path
    else:
        csv_files = sorted(list(DATA_DIR.glob("*.csv")), key=lambda x: x.stat().st_size, reverse=True)
        if not csv_files:
            raise FileNotFoundError("ERROR: No CSV file found in the 'data' folder!")
        # Use the largest CSV file
        dataset_path = csv_files[0]
    
    print(f"[INFO] Loading dataset: {dataset_path.name} (Size: {dataset_path.stat().st_size / (1024*1024):.2f} MB)")
    
    df = pd.read_csv(dataset_path)
    print(f"[INFO] Initial rows: {len(df)}")

    text_column = find_column(df.columns, TEXT_COLUMN_CANDIDATES)
    label_column = find_column(df.columns, LABEL_COLUMN_CANDIDATES)

    if text_column is None or label_column is None:
        raise ValueError(
            f"Could not auto-detect columns.\n"
            f"Found columns: {list(df.columns)}\n"
            f"Please rename your columns to 'email_text' and 'label'"
        )

    df = df[[text_column, label_column]].dropna()
    df.columns = ["email_text", "label"]
    df["email_text"] = df["email_text"].astype(str)
    df["label"] = df["label"].apply(normalize_label)
    df = df[df["label"].isin(["phishing", "legitimate"])]

    # Remove duplicates
    df = df.drop_duplicates(subset=["email_text"])
    
    print(f"[SUCCESS] Loaded {len(df)} unique emails ({df['label'].value_counts().to_dict()})")
    return df


def train_model():
    MODEL_DIR.mkdir(exist_ok=True)
    
    df = load_dataset()

    # Split data with stratification
    x_train, x_test, y_train, y_test = train_test_split(
        df["email_text"], df["label"], test_size=0.2, random_state=42, stratify=df["label"]
    )

    print(f"\n[INFO] Training set: {len(x_train)} emails")
    print(f"[INFO] Test set: {len(x_test)} emails")

    # Enhanced model pipeline
    model = Pipeline([
        ("tfidf", TfidfVectorizer(
            lowercase=True, 
            stop_words="english", 
            max_features=8000,  # Increased from 5000
            ngram_range=(1, 3),  # Include trigrams for better context
            min_df=2,  # Ignore terms appearing in < 2 docs
            max_df=0.9,  # Ignore terms appearing in > 90% of docs
            sublinear_tf=True,  # Sublinear TF scaling
        )),
        ("classifier", LogisticRegression(
            max_iter=1000, 
            C=0.5,  # Stronger regularization
            class_weight='balanced',  # Handle class imbalance
            solver='lbfgs'
        ))
    ])

    print("\n[INFO] Training model with enhanced parameters...")
    model.fit(x_train, y_train)
    
    # Evaluate
    y_pred = model.predict(x_test)
    print("\n[INFO] Model Performance:")
    print("Accuracy:", round(accuracy_score(y_test, y_pred), 4))
    print(classification_report(y_test, y_pred))

    # Save model
    joblib.dump(model, MODEL_PATH)
    print(f"\n[SUCCESS] Model successfully saved at: {MODEL_PATH}")
    print(f"[INFO] Model is ready to detect phishing emails with ~{round(accuracy_score(y_test, y_pred)*100, 1)}% accuracy")


if __name__ == "__main__":
    train_model()