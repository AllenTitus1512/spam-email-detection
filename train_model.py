from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "model"
MODEL_PATH = MODEL_DIR / "phishing_email_model.joblib"


TEXT_COLUMN_CANDIDATES = [
    "email_text",
    "text",
    "body",
    "message",
    "Email Text",
    "EmailText",
    "content",
]

LABEL_COLUMN_CANDIDATES = [
    "label",
    "class",
    "target",
    "Email Type",
    "EmailType",
    "type",
    "category",
]


def find_column(columns, candidates):
    normalized = {column.lower().replace(" ", "").replace("_", ""): column for column in columns}
    for candidate in candidates:
        key = candidate.lower().replace(" ", "").replace("_", "")
        if key in normalized:
            return normalized[key]
    return None


def normalize_label(value):
    text = str(value).strip().lower()
    phishing_words = ["phishing", "spam", "fraud", "malicious", "bad", "1"]
    legitimate_words = ["legitimate", "ham", "safe", "normal", "benign", "0"]

    if any(word in text for word in phishing_words):
        return "phishing"
    if any(word in text for word in legitimate_words):
        return "legitimate"
    return text


def load_dataset():
    csv_files = sorted(DATA_DIR.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError("No CSV file found in the data folder.")

    dataset_path = csv_files[0]
    df = pd.read_csv(dataset_path)

    text_column = find_column(df.columns, TEXT_COLUMN_CANDIDATES)
    label_column = find_column(df.columns, LABEL_COLUMN_CANDIDATES)

    if text_column is None or label_column is None:
        raise ValueError(
            "Could not find text and label columns. Rename your CSV columns to "
            "'email_text' and 'label', or update train_model.py column candidates."
        )

    df = df[[text_column, label_column]].dropna()
    df.columns = ["email_text", "label"]
    df["email_text"] = df["email_text"].astype(str)
    df["label"] = df["label"].apply(normalize_label)
    df = df[df["label"].isin(["phishing", "legitimate"])]

    if df.empty:
        raise ValueError("Dataset has no usable phishing or legitimate rows after cleaning.")

    return df


def train_model():
    MODEL_DIR.mkdir(exist_ok=True)
    df = load_dataset()

    stratify = df["label"] if df["label"].nunique() == 2 and len(df) >= 10 else None
    x_train, x_test, y_train, y_test = train_test_split(
        df["email_text"],
        df["label"],
        test_size=0.2,
        random_state=42,
        stratify=stratify,
    )

    model = Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    stop_words="english",
                    max_features=5000,
                    ngram_range=(1, 2),
                ),
            ),
            ("classifier", LogisticRegression(max_iter=1000)),
        ]
    )

    model.fit(x_train, y_train)
    predictions = model.predict(x_test)

    print("Model trained successfully")
    print(f"Rows used: {len(df)}")
    print(f"Accuracy: {accuracy_score(y_test, predictions):.2f}")
    print(classification_report(y_test, predictions, zero_division=0))

    joblib.dump(model, MODEL_PATH)
    print(f"Saved model to: {MODEL_PATH}")
    return model


if __name__ == "__main__":
    train_model()
