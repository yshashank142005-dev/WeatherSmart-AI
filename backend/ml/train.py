"""
train.py — Standalone training script.
Run with: python backend/ml/train.py
"""

import sys
import os

# Allow imports from backend/ root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ml.model import model_manager

if __name__ == "__main__":
    print("=== WeatherSmart AI — Model Training ===")
    model_manager.train()
    print("Training complete. Model saved.")
