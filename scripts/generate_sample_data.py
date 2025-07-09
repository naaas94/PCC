#!/usr/bin/env python3
"""
Generate synthetic sample data for PCC Pipeline testing
"""

import numpy as np
import pandas as pd
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder
import json
import os
from datetime import datetime

def generate_sample_embeddings(n_samples=100, embedding_dim=384):
    """Generate synthetic embeddings"""
    np.random.seed(42)  # For reproducibility
    return np.random.randn(n_samples, embedding_dim)

def generate_sample_cases(n_samples=100):
    """Generate synthetic case data"""
    np.random.seed(42)
    
    # Generate case IDs
    case_ids = [f"CASE_{i:06d}" for i in range(n_samples)]
    
    # Generate timestamps as pandas datetime64[ns]
    base_date = datetime(2025, 1, 1)
    timestamps = pd.date_range(start=base_date, periods=n_samples, freq='H')
    
    # Generate embeddings
    embeddings = generate_sample_embeddings(n_samples)
    
    return pd.DataFrame({
        'case_id': case_ids,
        'embedding_vector': embeddings.tolist(),
        'timestamp': timestamps
    })

def train_dummy_model(df):
    """Train a dummy model with synthetic data"""
    # Extract embeddings
    X = np.array(df['embedding_vector'].tolist())
    
    # Generate synthetic labels (simulate privacy cases)
    np.random.seed(42)
    y = np.random.choice(['NOT_PC', 'PC'], size=len(df), p=[0.7, 0.3])
    
    # Train simple model
    model = LogisticRegression(random_state=42, max_iter=1000)
    model.fit(X, y)
    
    return model, y

def save_sample_data():
    """Generate and save all sample data"""
    print("Generating sample data...")
    
    # Create directories if they don't exist
    os.makedirs('tests/fixtures', exist_ok=True)
    os.makedirs('src/models', exist_ok=True)
    
    # Generate sample cases
    df = generate_sample_cases(100)
    df.to_json('tests/fixtures/sample_data.json', orient='records', date_format='iso')
    print(f"✓ Saved {len(df)} sample cases to tests/fixtures/sample_data.json")
    
    # Train and save dummy model
    model, labels = train_dummy_model(df)
    joblib.dump(model, 'src/models/pcc_v0.1.1.pkl')
    print("✓ Saved dummy model to src/models/pcc_v0.1.1.pkl")
    
    # Update metadata
    metadata = {
        "model_version": "v0.1",
        "trained_on": datetime.now().isoformat(),
        "embedding_model": "all-MiniLM-L6-v2",
        "label_mapping": {"NOT_PC": 0, "PC": 1},
        "train_shape": [len(df), 384],
        "classifier": "LogisticRegression",
        "config": {
            "solver": "liblinear",
            "penalty": "l1",
            "C": 10
        },
        "notes": "Dummy model trained on synthetic data for testing"
    }
    
    with open('src/models/metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    print("✓ Updated metadata.json")
    
    # Print summary
    print(f"\n📊 Summary:")
    print(f"   - Generated {len(df)} sample cases")
    print(f"   - Model trained with {len(set(labels))} classes")
    print(f"   - Embedding dimension: 384")
    print(f"   - Files created in tests/fixtures/ and src/models/")

if __name__ == "__main__":
    save_sample_data() 