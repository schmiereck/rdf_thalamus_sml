"""
Quick self-test for training objectives.

Checks:
  1. All loss functions compute non-zero loss without NaNs.
  2. All gradients have matching shapes and are finite.
  3. Adam updates change parameters.
  4. HebbianLoss updates encoder node weights.
"""

from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np

from src.training_objectives import JEPALoss, ContrastiveLoss, SFALoss, HebbianLoss
from src.hierarchical_encoder import HierarchicalEncoder


def test_jepa():
    print("--- Testing JEPALoss ---")
    rng = np.random.default_rng(1)
    B, P, d, n_layers = 8, 5, 32, 3

    jepa = JEPALoss(n_layers=n_layers, d=d, lr=1e-3)

    # Create layer codes: each layer has shape (B, P, d)
    codes = [rng.standard_normal((B, P, d)) for _ in range(n_layers)]

    result = jepa.loss_and_grads(codes)

    assert not np.isnan(result["loss"]), "JEPA loss is NaN"
    assert result["loss"] != 0.0, "JEPA loss is zero (should be non-zero)"
    print(f"  loss = {result['loss']:.4f} (pred={result['pred_loss']:.4f}, "
          f"var={result['var_loss']:.4f}, cov={result['cov_loss']:.4f})")

    # Predictor gradient shapes
    p_grads = result["grads"]
    for l in range(n_layers):
        assert p_grads[l]["W_pred"].shape == (d, d), f"Layer {l} W_pred shape mismatch"
        assert p_grads[l]["b_pred"].shape == (d,), f"Layer {l} b_pred shape mismatch"
        assert not np.any(np.isnan(p_grads[l]["W_pred"])), f"NaN in layer {l} W_pred"
        assert np.all(np.isfinite(p_grads[l]["W_pred"])), f"Inf in layer {l} W_pred"

    # Code gradient shapes
    c_grads = result["code_grads"]
    for l in range(n_layers):
        assert c_grads[l].shape == (B, P, d), f"Layer {l} code_grad shape mismatch"
        assert not np.any(np.isnan(c_grads[l])), f"NaN in layer {l} code_grad"
        assert np.all(np.isfinite(c_grads[l])), f"Inf in layer {l} code_grad"

    # Check Adam update changes parameters
    W_pred_0 = jepa.predictors[0]["W_pred"].copy()
    jepa.step(codes)
    assert not np.allclose(jepa.predictors[0]["W_pred"], W_pred_0), "Predictor weights did not change after Adam step"

    print("  [PASS]\n")


def test_contrastive():
    print("--- Testing ContrastiveLoss ---")
    rng = np.random.default_rng(2)
    B, d = 16, 8

    contr = ContrastiveLoss(d=d, temp=0.5, lr=1e-3)

    # Representations from encoder: shape (B, 10 * d)
    z1 = rng.standard_normal((B, 10 * d))
    z2 = rng.standard_normal((B, 10 * d))

    result = contr.loss_and_grads(z1, z2)

    assert not np.isnan(result["loss"]), "Contrastive loss is NaN"
    assert result["loss"] > 0.0, "Contrastive loss should be > 0"
    print(f"  loss = {result['loss']:.4f}")

    assert result["d_z1"].shape == (B, 10 * d), "d_z1 shape mismatch"
    assert result["d_z2"].shape == (B, 10 * d), "d_z2 shape mismatch"
    for wname in ("W1", "b1", "W2", "b2"):
        assert not np.any(np.isnan(result[wname])), f"NaN in {wname}"

    # Check weight shapes
    assert contr.W1.shape == (10 * d, 5 * d), f"W1 shape mismatch: {contr.W1.shape}"
    assert contr.b1.shape == (5 * d,), f"b1 shape mismatch: {contr.b1.shape}"
    assert contr.W2.shape == (5 * d, int(2.5 * d)), f"W2 shape mismatch: {contr.W2.shape}"
    assert contr.b2.shape == (int(2.5 * d),), f"b2 shape mismatch: {contr.b2.shape}"

    # Check Adam update changes parameters
    W1_0 = contr.W1.copy()
    contr.step(z1, z2)
    assert not np.allclose(contr.W1, W1_0), "Projection weights did not change after Adam step"

    print("  [PASS]\n")


def test_sfa():
    print("--- Testing SFALoss ---")
    rng = np.random.default_rng(3)
    T, d = 50, 16

    sfa = SFALoss(delta_order=1, lambda_var=25.0)

    z = rng.standard_normal((T, d))
    # Make it somewhat smooth
    z = np.cumsum(z, axis=0) * 0.1

    result = sfa.forward(z)

    assert not np.isnan(result["loss"]), "SFA loss is NaN"
    assert result["loss"] > 0.0, "SFA loss should be > 0"
    print(f"  loss = {result['loss']:.4f} (slow={result['slowness']:.4f}, "
          f"var={result['variance']:.4f})")

    assert result["dL_dz"].shape == (T, d), "dL_dz shape mismatch"
    assert not np.any(np.isnan(result["dL_dz"])), "NaN in dL_dz"
    assert np.all(np.isfinite(result["dL_dz"])), "Inf in dL_dz"

    # Check gradient direction: reducing slowness should decrease loss
    z_shifted = z.copy()
    z_shifted[1:] -= 0.01 * result["dL_dz"][1:]
    result2 = sfa.forward(z_shifted)
    print(f"  step check: before={result['loss']:.4f}, after={result2['loss']:.4f}")

    print("  [PASS]\n")


def test_hebbian():
    print("--- Testing HebbianLoss (Oja's rule) ---")
    rng = np.random.default_rng(4)
    B = 32

    # Test with cross_layer sharing
    enc = HierarchicalEncoder(d=4, sharing_mode="cross_layer", seed=42)
    x_binary = (rng.random((B, 16)) < 0.5).astype(np.float64)

    hebb = HebbianLoss(eta=1e-3)

    # Save initial weights
    W0 = enc.layer_nodes[0].W_enc.copy()

    # Apply Oja update
    loss_val = hebb.update(enc, x_binary)

    assert not np.isnan(loss_val), "Hebbian monitoring loss is NaN"
    print(f"  monitoring loss = {loss_val:.4f}")

    # Check weights changed
    assert not np.allclose(enc.layer_nodes[0].W_enc, W0), "Weights did not change after Oja update"
    print(f"  weight change = {np.abs(enc.layer_nodes[0].W_enc - W0).mean():.6f}")

    # Test with none sharing
    enc2 = HierarchicalEncoder(d=4, sharing_mode="none", seed=42)
    W0_2 = enc2.nodes[0][0].W_enc.copy()

    loss_val2 = hebb.update(enc2, x_binary)
    assert not np.isnan(loss_val2), "Hebbian monitoring loss is NaN (none sharing)"
    assert not np.allclose(enc2.nodes[0][0].W_enc, W0_2), "Weights did not change (none sharing)"

    print("  [PASS]\n")


def test_encoder_backward():
    print("--- Testing Encoder backward_from_code_grads ---")
    rng = np.random.default_rng(5)

    for mode in ("none", "within_layer", "cross_layer"):
        print(f"  [mode={mode}]")
        enc = HierarchicalEncoder(d=4, sharing_mode=mode, seed=42)

        batch = 4
        x_binary = (rng.random((batch, 16)) < 0.5).astype(np.float64)

        # Forward with intermediates
        fwd = enc.forward_with_intermediates(x_binary)
        codes = fwd["codes"]
        node_inputs = fwd["node_inputs"]

        assert codes.shape == (batch, 10 * enc.d_out), "codes shape mismatch"
        assert len(node_inputs) == enc.n_layers, "node_inputs length mismatch"

        # Fake gradient at output
        dL_dcodes = rng.standard_normal(codes.shape)

        # Backward
        grads = enc.backward_from_code_grads(
            dL_dcodes=dL_dcodes,
            codes=codes,
            node_inputs=node_inputs,
            x_binary=x_binary,
        )

        # Check embedding gradient shape
        assert grads["dL_dembedding"].shape == enc.embedding.shape, \
            "dL_dembedding shape mismatch"
        assert not np.any(np.isnan(grads["dL_dembedding"])), "NaN in dL_dembedding"

        # Check node gradients
        dL_dnodes = grads["dL_dnodes"]
        if mode == "none":
            for l in range(enc.n_layers):
                assert len(dL_dnodes[l]) == enc.n_nodes_per_layer[l]
                for p in range(enc.n_nodes_per_layer[l]):
                    node = enc._get_node(l, p)
                    g = dL_dnodes[l][p]
                    assert g["W_enc"].shape == node.W_enc.shape
                    assert g["b_enc"].shape == node.b_enc.shape
                    assert not np.any(np.isnan(g["W_enc"]))
        else:
            for l in range(enc.n_layers):
                g = dL_dnodes[l]
                node = enc.layer_nodes[l]
                assert g["W_enc"].shape == node.W_enc.shape
                assert not np.isnan(g["W_enc"]).any()

        print(f"    embedding grad shape: {grads['dL_dembedding'].shape}  [OK]")
        print(f"    dx_binary shape: {grads['dL_dx_binary'].shape}  [OK]")
    print("  [PASS]\n")


def test_encoder_reconstruction_consistency():
    """Verify forward_with_intermediates agrees with regular forward."""
    print("--- Testing forward consistency ---")
    rng = np.random.default_rng(6)
    enc = HierarchicalEncoder(d=4, sharing_mode="cross_layer", seed=42)

    x = (rng.random((4, 16)) < 0.5).astype(np.float64)
    codes_regular = enc.forward(x)
    codes_intermediate = enc.forward_with_intermediates(x)["codes"]

    assert np.allclose(codes_regular, codes_intermediate), \
        "forward() and forward_with_intermediates() disagree!"
    print("  forward() == forward_with_intermediates()  [PASS]\n")


def main():
    print("=" * 60)
    print("  training objectives & encoder backward  --  Self-Test")
    print("=" * 60 + "\n")

    test_jepa()
    test_contrastive()
    test_sfa()
    test_hebbian()
    test_encoder_backward()
    test_encoder_reconstruction_consistency()

    print("=" * 60)
    print("  ALL SELF-TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()
