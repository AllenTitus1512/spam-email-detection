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
    text = str(value).strip().lower()
    if any(word in text for word in ["phishing", "spam", "fraud", "malicious", "1", "bad"]):
        return "phishing"
    if any(word in text for word in ["legitimate", "ham", "safe", "normal", "benign", "0", "good"]):
        return "legitimate"
    return text


def load_dataset():
    csv_files = list(DATA_DIR.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError("ERROR: No CSV file found in the 'data' folder!")

    dataset_path = csv_files[0]
    print(f"[INFO] Loading dataset: {dataset_path.name}")
    
    df = pd.read_csv(dataset_path)

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

    print(f"[SUCCESS] Loaded {len(df)} emails ({df['label'].value_counts().to_dict()})")
    return df


def train_model():
    MODEL_DIR.mkdir(exist_ok=True)
    
    df = load_dataset()

    # Split data
    x_train, x_test, y_train, y_test = train_test_split(
        df["email_text"], df["label"], test_size=0.2, random_state=42, stratify=df["label"]
    )

    # Create and train model
    model = Pipeline([
        ("tfidf", TfidfVectorizer(
            lowercase=True, 
            stop_words="english", 
            max_features=5000, 
            ngram_range=(1, 2)
        )),
        ("classifier", LogisticRegression(max_iter=1000, C=1.0))
    ])

    model.fit(x_train, y_train)
    
    # Evaluate
    y_pred = model.predict(x_test)
    print("\n[INFO] Model Performance:")
    print("Accuracy:", round(accuracy_score(y_test, y_pred), 4))
    print(classification_report(y_test, y_pred))

    # Save model
    joblib.dump(model, MODEL_PATH)
    print(f"\n[SUCCESS] Model successfully saved at: {MODEL_PATH}")


if __name__ == "__main__":
    train_model()