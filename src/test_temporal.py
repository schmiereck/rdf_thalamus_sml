"""
Self-tests for Phase 2 temporal infrastructure.

Tests:
  1. Temporal dataset generation and shape consistency
  2. Embedding lookup correctness
  3. All four encoder forward passes and output shapes
  4. P2-D gradient computation (numerical check)
  5. JEPALoss integration with temporal codes
  6. Linear probe training on mean-pooled codes
  7. Next-step prediction Ridge regression
  8. End-to-end mini training loop
"""

from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

from temporal_dataset import generate_temporal_dataset, generate_irregular_markov_dataset, make_state_embeddings
from temporal_encoder import P2DEncoder, P2AEncoder, P2BEncoder, P2CEncoder
from training_objectives import JEPALoss, _Adam
from harness import SimpleLogisticRegression


# ---------------------------------------------------------------------------
#  Test 1: Dataset generation
# ---------------------------------------------------------------------------

def test_dataset_shapes():
    ds = generate_temporal_dataset(seed=42)
    assert ds["train_seqs"].shape == (600, 64)
    assert ds["train_emb"].shape == (600, 64, 16)
    assert ds["train_y"].shape == (600,)
    assert ds["test_seqs"].shape == (300, 64)
    assert ds["test_emb"].shape == (300, 64, 16)
    assert ds["test_y"].shape == (300,)
    assert ds["embeddings"].shape == (8, 16)
    assert set(np.unique(ds["train_y"])) == {0, 1, 2}
    print("[PASS] test_dataset_shapes")


def test_embedding_lookup():
    ds = generate_temporal_dataset(seed=42)
    for i in range(8):
        mask = ds["train_seqs"] == i
        if mask.any():
            emb_vals = ds["train_emb"][mask]
            assert np.allclose(emb_vals, ds["embeddings"][i])
    print("[PASS] test_embedding_lookup")


def test_markov_dataset():
    ds = generate_irregular_markov_dataset(seed=42)
    assert ds["train_seqs"].shape == (200, 64)
    assert ds["test_seqs"].shape == (100, 64)
    print("[PASS] test_markov_dataset")


def test_embedding_scale():
    emb = make_state_embeddings(8, 16, seed=42)
    expected_scale = np.sqrt(2.0 / 16.0)
    # Check approximate scale (within 30% for small sample)
    actual_std = emb.std()
    assert abs(actual_std - expected_scale) / expected_scale < 0.3, \
        f"Expected std ~{expected_scale:.4f}, got {actual_std:.4f}"
    print("[PASS] test_embedding_scale")


# ---------------------------------------------------------------------------
#  Test 2: Encoder forward passes
# ---------------------------------------------------------------------------

def test_p2d_forward():
    rng = np.random.default_rng(7)
    x = rng.standard_normal((4, 64, 16))
    enc = P2DEncoder(d=16, d_out=16, seed=42)
    out = enc.forward(x)
    assert out.shape == (4, 64, 16)
    assert np.allclose(out[:, :2, :], 0.0)
    print("[PASS] test_p2d_forward")


def test_p2a_forward():
    rng = np.random.default_rng(7)
    x = rng.standard_normal((4, 64, 16))
    enc = P2AEncoder(d=16, d_out=16, N=3, seed=42)
    out = enc.forward(x)
    assert out.shape == (4, 64, 16)
    print("[PASS] test_p2a_forward")


def test_p2b_forward():
    rng = np.random.default_rng(7)
    x = rng.standard_normal((4, 64, 16))
    enc = P2BEncoder(d=16, d_out=16, seed=42)
    out = enc.forward(x)
    assert out.shape == (4, 64, 16)
    print("[PASS] test_p2b_forward")


def test_p2c_forward():
    rng = np.random.default_rng(7)
    x = rng.standard_normal((4, 64, 16))
    enc = P2CEncoder(d=16, d_out=16, seed=42)
    out = enc.forward(x)
    assert out.shape == (4, 64, 16)
    print("[PASS] test_p2c_forward")


# ---------------------------------------------------------------------------
#  Test 3: P2-D gradient numerical check
# ---------------------------------------------------------------------------

def _numerical_grad_W_enc(encoder, x, eps=1e-6):
    """Numerical gradient for W_enc only."""
    orig = encoder.node.W_enc.copy()
    grad = np.zeros_like(orig)
    flat = orig.ravel()
    for idx in range(flat.size):
        original = flat[idx]
        flat[idx] = original + eps
        out_hi = encoder.forward(x)
        loss_hi = np.sum(out_hi ** 2)
        flat[idx] = original - eps
        out_lo = encoder.forward(x)
        loss_lo = np.sum(out_lo ** 2)
        flat[idx] = original
        grad.ravel()[idx] = (loss_hi - loss_lo) / (2.0 * eps)
    return grad


def test_p2d_gradient():
    rng = np.random.default_rng(7)
    x = rng.standard_normal((2, 16, 16))
    encoder = P2DEncoder(d=16, d_out=16, seed=42)

    # Analytical gradient
    out = encoder.forward(x)
    dL = 2.0 * out  # gradient of sum(out^2)
    grads = encoder.compute_gradients(x, dL)
    ana = grads["W_enc"]

    # Numerical gradient
    num = _numerical_grad_W_enc(encoder, x)

    rel_err = np.max(np.abs(ana - num) / (np.maximum(np.abs(ana), np.abs(num)) + 1e-12))
    assert rel_err < 1e-4, f"Relative error {rel_err:.2e} too large"
    print(f"[PASS] test_p2d_gradient (rel_err={rel_err:.2e})")


# ---------------------------------------------------------------------------
#  Test 4: JEPALoss integration
# ---------------------------------------------------------------------------

def test_jepa_integration():
    rng = np.random.default_rng(7)
    x = rng.standard_normal((8, 64, 16))
    encoder = P2DEncoder(d=16, d_out=16, seed=42)
    jepa = JEPALoss(n_layers=1, d=16, lr=1e-3)

    codes = encoder.forward(x)
    result = jepa.step([codes])

    assert "loss" in result
    assert "code_grads" in result
    assert len(result["code_grads"]) == 1
    assert result["code_grads"][0].shape == codes.shape
    assert result["loss"] > 0
    print("[PASS] test_jepa_integration")


# ---------------------------------------------------------------------------
#  Test 5: Linear probe on mean-pooled codes
# ---------------------------------------------------------------------------

def test_linear_probe():
    ds = generate_temporal_dataset(seed=42)
    encoder = P2DEncoder(d=16, d_out=16, seed=42)

    train_codes = encoder.forward(ds["train_emb"])
    test_codes = encoder.forward(ds["test_emb"])

    train_mean = train_codes.mean(axis=1)
    test_mean = test_codes.mean(axis=1)

    probe = SimpleLogisticRegression(n_classes=3, n_features=16, lr=0.1, max_iter=500, seed=42)
    probe.fit(train_mean, ds["train_y"])

    acc = probe.score(test_mean, ds["test_y"])
    assert 0.0 <= acc <= 1.0
    print(f"[PASS] test_linear_probe (acc={acc:.4f})")


# ---------------------------------------------------------------------------
#  Test 6: Next-step prediction
# ---------------------------------------------------------------------------

def test_next_step_prediction():
    ds = generate_irregular_markov_dataset(seed=42)
    encoder = P2DEncoder(d=16, d_out=16, seed=42)

    train_codes = encoder.forward(ds["train_emb"])
    test_codes = encoder.forward(ds["test_emb"])

    X_train = train_codes[:, :-1, :].reshape(-1, 16)
    y_train = ds["train_emb"][:, 1:, :].reshape(-1, 16)

    X_test = test_codes[:, :-1, :].reshape(-1, 16)
    y_test = ds["test_emb"][:, 1:, :].reshape(-1, 16)

    XtX = X_train.T @ X_train + 1.0 * np.eye(16)
    Xty = X_train.T @ y_train
    W = np.linalg.solve(XtX, Xty)

    y_pred = X_test @ W
    cos_sim = np.sum(y_pred * y_test, axis=1) / (np.linalg.norm(y_pred, axis=1) * np.linalg.norm(y_test, axis=1) + 1e-12)
    mean_cos = float(cos_sim.mean())

    assert -1.0 <= mean_cos <= 1.0
    print(f"[PASS] test_next_step_prediction (cos={mean_cos:.4f})")


# ---------------------------------------------------------------------------
#  Test 7: End-to-end mini training loop
# ---------------------------------------------------------------------------

def test_training_loop():
    ds = generate_temporal_dataset(n_train_per_cat=50, n_test_per_cat=20, seed=42)
    encoder = P2DEncoder(d=16, d_out=16, seed=42)
    jepa = JEPALoss(n_layers=1, d=16, lr=1e-3)
    adam_enc = _Adam(
        {"W_enc": encoder.node.W_enc, "b_enc": encoder.node.b_enc},
        lr=1e-3,
    )

    for epoch in range(10):
        codes = encoder.forward(ds["train_emb"])
        result = jepa.step([codes])
        code_grads = result["code_grads"][0]
        enc_grads = encoder.compute_gradients(ds["train_emb"], code_grads)
        adam_enc.step(
            {"W_enc": encoder.node.W_enc, "b_enc": encoder.node.b_enc},
            {"W_enc": enc_grads["W_enc"], "b_enc": enc_grads["b_enc"]},
        )

    # After training, evaluate
    train_codes = encoder.forward(ds["train_emb"])
    test_codes = encoder.forward(ds["test_emb"])
    train_mean = train_codes.mean(axis=1)
    test_mean = test_codes.mean(axis=1)

    probe = SimpleLogisticRegression(n_classes=3, n_features=16, lr=0.1, max_iter=500, seed=42)
    probe.fit(train_mean, ds["train_y"])
    acc = probe.score(test_mean, ds["test_y"])

    assert 0.0 <= acc <= 1.0
    print(f"[PASS] test_training_loop (acc={acc:.4f})")


# ---------------------------------------------------------------------------
#  Test 8: Encoder gradient shapes
# ---------------------------------------------------------------------------

def test_encoder_gradient_shapes():
    rng = np.random.default_rng(7)
    x = rng.standard_normal((4, 64, 16))
    dL = rng.standard_normal((4, 64, 16))

    enc_d = P2DEncoder(d=16, d_out=16, seed=42)
    grads_d = enc_d.compute_gradients(x, dL)
    assert grads_d["W_enc"].shape == enc_d.node.W_enc.shape
    assert grads_d["b_enc"].shape == enc_d.node.b_enc.shape
    assert grads_d["x"].shape == x.shape

    enc_b = P2BEncoder(d=16, d_out=16, seed=42)
    grads_b = enc_b.compute_gradients(x, dL)
    assert grads_b["W_xh"].shape == enc_b.W_xh.shape
    assert grads_b["W_hh"].shape == enc_b.W_hh.shape
    assert grads_b["x"].shape == x.shape

    enc_c = P2CEncoder(d=16, d_out=16, seed=42)
    grads_c = enc_c.compute_gradients(x, dL)
    assert grads_c["W_enc"].shape == enc_c.node.W_enc.shape
    assert grads_c["W_proj"].shape == enc_c.W_proj.shape
    assert grads_c["x"].shape == x.shape

    print("[PASS] test_encoder_gradient_shapes")


# ---------------------------------------------------------------------------
#  Run all tests
# ---------------------------------------------------------------------------

def run_all_tests():
    print("=" * 60)
    print("  Phase 2 Temporal Infrastructure -- Self-Tests")
    print("=" * 60)

    tests = [
        test_dataset_shapes,
        test_embedding_lookup,
        test_markov_dataset,
        test_embedding_scale,
        test_p2d_forward,
        test_p2a_forward,
        test_p2b_forward,
        test_p2c_forward,
        test_p2d_gradient,
        test_jepa_integration,
        test_linear_probe,
        test_next_step_prediction,
        test_training_loop,
        test_encoder_gradient_shapes,
    ]

    passed = 0
    failed = 0

    for test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"[FAIL] {test_fn.__name__}: {e}")
            failed += 1

    print("\n" + "-" * 60)
    print(f"  Results: {passed} passed, {failed} failed")
    if failed == 0:
        print("  ALL TESTS PASSED!")
    else:
        print(f"  {failed} TEST(S) FAILED!")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
