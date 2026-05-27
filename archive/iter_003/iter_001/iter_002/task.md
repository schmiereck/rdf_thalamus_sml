Please proceed DIRECTLY to implementing the required files. No need to spend too much time exploring since we already know the exact requirements.

### Tasks to complete:

1. Create `src/training_objectives.py` with pure numpy implementations of:
   - `JEPALoss`
   - `ContrastiveLoss`
   - `SFALoss`
   - `HebbianLoss`
   Make sure to implement the bidirectional prediction, VICReg variance and covariance penalties, projection MLP with ReLU and L2-normalization, standard InfoNCE loss and gradients, slowness loss, and Oja's rule updates.

2. Modify `src/hierarchical_encoder.py` to add:
   - `forward_with_intermediates(self, x_binary)`
   - `backward_from_code_grads(self, dL_dcodes, codes, node_inputs, x_binary)`

3. Create a quick self-test script `src/test_objectives.py` to check:
   - All loss functions calculate non-zero loss and gradients without any NaNs.
   - The backward pass in the encoder successfully computes gradients of matching shapes.

Let's do this efficiently! Use `write_file` tool to create and edit files directly. Thank you!