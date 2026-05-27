Please rewrite `src/training_objectives.py` and `src/test_objectives.py` to match the exact interfaces requested:

1. `JEPALoss(self, n_layers, d, temp=0.5, lr=1e-3)` with per-layer predictors updated using Adam, bidirectional prediction loss, VICReg variance (weight 25.0) and covariance (weight 25.0).
2. `ContrastiveLoss(self, d, temp=0.5, lr=1e-3)` with a projection MLP (10*d -> 5*d -> 2.5*d), ReLU activation, and L2 normalization, NT-Xent loss on stacked original+augmented views, updated using Adam.
3. `SFALoss(self, delta_order=1, lambda_var=25.0)` with slowness MSE + variance penalty (weight 25.0) and analytical gradients.
4. `HebbianLoss(self, eta=1e-3)` with Oja update applied directly to the layer_nodes, and returning negative correlation as a monitoring loss.

Write these implementations and update `src/test_objectives.py` to test them. Run the tests to verify syntax and math correctness. Proceed directly to writing files so you do not time out. Thank you!