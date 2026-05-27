#!/usr/bin/env python3
"""Test raw input accuracy on Phase 1 dataset using SimpleLogisticRegression."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from dataset_phase1 import generate_phase1_dataset
from harness import SimpleLogisticRegression


def main():
    # Generate the Phase 1 dataset
    dataset = generate_phase1_dataset(seed=42)
    train_x = dataset["train_x"]  # (1000, 16) - 5 categories x 200 each
    train_y = dataset["train_y"]
    test_x = dataset["test_x"]    # (500, 16)  - 5 categories x 100 each
    test_y = dataset["test_y"]

    print(f"Train set: {train_x.shape}, Test set: {test_x.shape}")
    print(f"Input dtype: {train_x.dtype}, unique values: {np.unique(train_x)}")

    # Train a logistic regression directly on the raw 16-bit inputs
    n_classes = 5
    n_features = train_x.shape[1]

    model = SimpleLogisticRegression(
        n_classes=n_classes,
        n_features=n_features,
        lr=0.1,
        max_iter=1000,
        seed=42,
    )
    model.fit(train_x, train_y)

    train_acc = model.score(train_x, train_y)
    test_acc = model.score(test_x, test_y)

    print(f"\nRaw input logistic regression results:")
    print(f"  Train accuracy: {train_acc:.4f}")
    print(f"  Test accuracy:  {test_acc:.4f}")
    print(f"  Chance level:   {1.0/n_classes:.4f}")


if __name__ == "__main__":
    import numpy as np
    main()