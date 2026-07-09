import pandas as pd
import os
from pathlib import Path

# ================== CONFIG ==================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MERGED_FILE = DATA_DIR / "merged_dataset.csv"

print("[INFO] Starting dataset merge...\n")

# Load each dataset with only the rows we need
datasets = []

# 1. AVN_Corpus.csv - contains both phishing (1.0) and legitimate (0.0)
print("[1/3] Loading AVN_Corpus.csv...")
try:
    df_corpus = pd.read_csv(DATA_DIR / "AVN_Corpus.csv")
    df_corpus = df_corpus[['body', 'label']].rename(columns={'body': 'email_text'})
    df_corpus = df_corpus.dropna()
    df_corpus['source'] = 'AVN_Corpus'
    print(f"     Loaded {len(df_corpus)} rows | Labels: {df_corpus['label'].value_counts().to_dict()}")
    datasets.append(df_corpus)
except Exception as e:
    print(f"     ❌ Error: {e}")

# 2. AVN_Basic.csv - has labels 0, 1, 2 (2 might be neutral, skip it)
print("[2/3] Loading AVN_Basic.csv...")
try:
    df_basic = pd.read_csv(DATA_DIR / "AVN_Basic.csv")
    df_basic = df_basic[df_basic['label'].isin([0, 1])]  # Filter out label 2
    df_basic = df_basic[['body', 'label']].rename(columns={'body': 'email_text'})
    df_basic = df_basic.dropna()
    df_basic['source'] = 'AVN_Basic'
    print(f"     Loaded {len(df_basic)} rows | Labels: {df_basic['label'].value_counts().to_dict()}")
    datasets.append(df_basic)
except Exception as e:
    print(f"     ❌ Error: {e}")

# 3. phishing__dataset.csv - already good quality
print("[3/3] Loading phishing__dataset.csv...")
try:
    df_phishing = pd.read_csv(DATA_DIR / "phishing__dataset.csv")
    df_phishing = df_phishing[['text', 'label']].rename(columns={'text': 'email_text'})
    df_phishing = df_phishing.dropna()
    df_phishing['source'] = 'phishing_dataset'
    print(f"     Loaded {len(df_phishing)} rows | Labels: {df_phishing['label'].value_counts().to_dict()}")
    datasets.append(df_phishing)
except Exception as e:
    print(f"     ❌ Error: {e}")

# Merge all datasets
if datasets:
    merged_df = pd.concat(datasets, ignore_index=True)
    print(f"\n[INFO] Total merged rows: {len(merged_df)}")
    print(f"[INFO] Label distribution: {merged_df['label'].value_counts().to_dict()}")
    
    # Remove duplicates
    merged_df = merged_df.drop_duplicates(subset=['email_text'])
    print(f"[INFO] After removing duplicates: {len(merged_df)} rows")
    
    # Save merged dataset
    merged_df[['email_text', 'label']].to_csv(MERGED_FILE, index=False)
    print(f"\n[SUCCESS] Merged dataset saved: {MERGED_FILE}")
    print(f"[SUCCESS] Ready for retraining!")
else:
    print("[ERROR] No datasets loaded!")
