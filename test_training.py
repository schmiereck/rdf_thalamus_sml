#!/usr/bin/env python3
"""
Test script for Phase 1 training:
  1. Generate Phase 1 dataset
  2. Instantiate HierarchicalEncoder with cross_layer sharing, d=8
  3. Record initial embedding
  4. Train for 5 epochs per layer
  5. Print loss history
  6. Print max absolute change in embedding
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import numpy as np
from dataset_phase1 import generate_phase1_dataset
from hierarchical_encoder import HierarchicalEncoder

def main():
    print("=" * 60)
    print("  Phase 1 Training Test")
    print("=" * 60)

    # 1. Generate dataset
    print("\n[1] Generating Phase 1 dataset (n_train=200, n_test=100)...")
    data = generate_phase1_dataset(n_train=200, n_test=100, seed=42)
    train_x = data["train_x"]
    print(f"    train_x shape: {train_x.shape}")

    # 2. Instantiate encoder
    print("\n[2] Instantiating HierarchicalEncoder (sharing_mode='cross_layer', d=8)...")
    enc = HierarchicalEncoder(d=8, sharing_mode="cross_layer", seed=42)
    print(f"    n_nodes_per_layer: {enc.n_nodes_per_layer}")
    print(f"    d_out: {enc.d_out}")
    print(f"    embedding shape: {enc.embedding.shape}")

    # 3. Store initial embedding
    initial_embedding = enc.embedding.copy()
    print(f"\n[3] Initial embedding stored.")
    print(f"    embedding[0] = {initial_embedding[0]}")
    print(f"    embedding[1] = {initial_embedding[1]}")

    # 4. Train for 5 epochs per layer
    print("\n[4] Training for 5 epochs per layer...")
    info = enc.train(dataset=train_x, epochs_per_layer=5, lr=0.01, batch_size=32)

    # 5. Print training loss history
    print("\n[5] Training loss history (epoch-by-epoch):")
    n_layers = enc.n_layers
    epochs_per_layer = len(info["loss_history"]) // n_layers
    for l_idx in range(n_layers):
        print(f"\n    Layer {l_idx}:")
        for e in range(epochs_per_layer):
            loss = info["loss_history"][l_idx * epochs_per_layer + e]
            print(f"      Epoch {e+1:2d}:  loss = {loss:.6f}")

    # 6. Compute absolute change in embedding
    final_embedding = enc.embedding
    embed_diff = np.max(np.abs(final_embedding - initial_embedding))
    print(f"\n[6] Embedding change analysis:")
    print(f"    Initial embedding:\n{initial_embedding}")
    print(f"    Final embedding:\n{final_embedding}")
    print(f"    Max absolute change: {embed_diff:.8f}")

    # Additional info: per-embedding-slot change
    diff_0 = np.max(np.abs(final_embedding[0] - initial_embedding[0]))
    diff_1 = np.max(np.abs(final_embedding[1] - initial_embedding[1]))
    print(f"    Max change [0,:]: {diff_0:.8f}")
    print(f"    Max change [1,:]: {diff_1:.8f}")

    # Check if weights are actually shared cross-layer
    print("\n[7] Cross-layer weight sync check:")
    if enc.sharing_mode == "cross_layer":
        all_same = True
        for l in range(1, enc.n_layers):
            ok = np.allclose(enc.layer_nodes[l].W_enc, enc.layer_nodes[0].W_enc)
            print(f"    Layer {l} W_enc == Layer 0 W_enc: {ok}")
            all_same = all_same and ok
        print(f"    All layers share weights: {all_same}")

    print("\n" + "=" * 60)
    print("  DONE")
    print("=" * 60)


if __name__ == "__main__":
    main()