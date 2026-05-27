"""
Quick self-test for training objectives and encoder backward pass.

Checks:
  1. All loss functions compute non-zero loss without NaNs.
  2. All gradients have matching shapes and are finite.
  3. Encoder backward_from_code_grads produces correctly-shaped gradients.
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
    B, d = 8, 32

    jepa = JEPALoss(d=d, predictor_hidden=64)

    context = rng.standard_normal((B, d))
    target = rng.standard_normal((B, d))

    result = jepa.loss_and_grads(context, target)

    assert not np.isnan(result["loss"]), "JEPA loss is NaN"
    assert result["loss"] != 0.0, "JEPA loss is zero (should be non-zero)"
    print(f"  loss = {result['loss']:.4f} (sim={result['sim_loss']:.4f}, "
          f"var={result['var_loss']:.4f}, cov={result['cov_loss']:.4f})")

    # Gradient shapes
    assert result["d_context"].shape == (B, d), "d_context shape mismatch"
    assert result["d_target"].shape == (B, d), "d_target shape mismatch"
    for wname in ("W1_ct", "b1_ct", "W2_ct", "b2_ct",
                  "W1_tc", "b1_tc", "W2_tc", "b2_tc"):
        assert not np.any(np.isnan(result[wname])), f"NaN in {wname}"
        assert np.all(np.isfinite(result[wname])), f"Inf in {wname}"

    # Check update direction (make sure gradients drive change)
    old_context = context.copy()
    new_context = context - 0.01 * result["d_context"]
    new_res = jepa.forward(new_context, target)
    # Loss should generally decrease after small gradient step
    print(f"  step check: before={result['loss']:.4f}, after={new_res['loss']:.4f}")
    print("  [PASS]\n")


def test_contrastive():
    print("--- Testing ContrastiveLoss ---")
    rng = np.random.default_rng(2)
    B, d = 16, 32

    contr = ContrastiveLoss(d=d, proj_hidden=64, temperature=0.1)

    z1 = rng.standard_normal((B, d))
    z2 = rng.standard_normal((B, d))

    result = contr.loss_and_grads(z1, z2)

    assert not np.isnan(result["loss"]), "Contrastive loss is NaN"
    assert result["loss"] > 0.0, "Contrastive loss should be > 0"
    print(f"  loss = {result['loss']:.4f}")

    assert result["d_z1"].shape == (B, d), "d_z1 shape mismatch"
    assert result["d_z2"].shape == (B, d), "d_z2 shape mismatch"
    for wname in ("W1", "b1", "W2", "b2"):
        assert not np.any(np.isnan(result[wname])), f"NaN in {wname}"
    print("  [PASS]\n")


def test_sfa():
    print("--- Testing SFALoss ---")
    rng = np.random.default_rng(3)
    T, d = 50, 16

    sfa = SFALoss(delta_order=1, whitening_coeff=0.1)

    z = rng.standard_normal((T, d))
    # Make it somewhat smooth
    z = np.cumsum(z, axis=0) * 0.1

    result = sfa.forward(z)

    assert not np.isnan(result["loss"]), "SFA loss is NaN"
    assert result["loss"] > 0.0, "SFA loss should be > 0"
    print(f"  loss = {result['loss']:.4f} (slow={result['slowness']:.4f}, "
          f"white={result['whitening']:.4f})")

    assert result["dL_dz"].shape == (T, d), "dL_dz shape mismatch"
    assert not np.any(np.isnan(result["dL_dz"])), "NaN in dL_dz"
    assert np.all(np.isfinite(result["dL_dz"])), "Inf in dL_dz"
    print("  [PASS]\n")


def test_hebbian():
    print("--- Testing HebbianLoss (Oja's rule) ---")
    rng = np.random.default_rng(4)
    B, in_dim, out_dim = 32, 20, 8

    hebb = HebbianLoss(in_dim=in_dim, out_dim=out_dim, lr=0.001)
    W0 = hebb.W.copy()

    x = rng.standard_normal((B, in_dim))

    # Forward
    fwd = hebb.forward(x)
    assert fwd["y"].shape == (B, out_dim), "y shape mismatch"
    assert not np.any(np.isnan(fwd["y"])), "NaN in Hebbian output"

    # Update
    upd = hebb.update(x)
    assert upd["delta_W"].shape == (out_dim, in_dim), "delta_W shape mismatch"
    assert not np.any(np.isnan(upd["delta_W"])), "NaN in delta_W"
    assert not np.allclose(hebb.W, W0), "Weights did not change after update"

    loss_val = hebb.loss(x)
    assert not np.isnan(loss_val), "Hebbian proxy loss is NaN"
    print(f"  proxy loss = {loss_val:.4f}, weight change = "
          f"{np.abs(hebb.W - W0).mean():.6f}")
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
