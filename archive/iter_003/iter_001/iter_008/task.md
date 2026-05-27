Please implement the complete Phase 1 experimental runner in `src/run_phase1_v2.py` and run it to collect results.

### Configurations to run (35 total runs: 7 configs x 5 seeds [42–46]):
1. `P1-B-JEPA-d8`: cross_layer, d=8, JEPA loss (Simultaneous training)
2. `P1-B-Contrastive-d8`: cross_layer, d=8, Contrastive loss (Simultaneous training with NT-Xent + bit-flip augmentation)
3. `P1-B-SFA-d8`: cross_layer, d=8, SFA loss (Simultaneous training)
4. `P1-B-Hebbian-d8`: cross_layer, d=8, Hebbian Oja updates (Simultaneous training)
5. `P1-B-JEPA-d16`: cross_layer, d=16, JEPA loss (Simultaneous training)
6. `Untrained-d8`: cross_layer, d=8, no training (control baseline)
7. `Untrained-d16`: cross_layer, d=16, no training (control baseline)

### Training Parameters:
- 200 epochs (simultaneous training of all layers, not progressive)
- batch_size=64
- For JEPA, Contrastive, SFA: Adam optimizer for the master node parameters (`W_enc`, `b_enc` of the master node, and the input `embedding` table) with:
  $lr=1e-3, \beta_1=0.9, \beta_2=0.999, \epsilon=1e-8$.
  Use the private `_Adam` optimizer helper from `src.training_objectives`!
- For Hebbian: use Hebbian Oja updates with $\eta=1e-3$.
- No L1 penalty or k-WTA.

### Implementation details of simultaneous training:
- Setup Simultaneous weight sharing at initialization of each encoder:
  ```python
  if encoder.sharing_mode == "cross_layer":
      master = encoder.layer_nodes[0]
      for l in range(1, encoder.n_layers):
          encoder.layer_nodes[l] = master
  ```
- During training steps:
  1. For `ContrastiveLoss`:
     - Create an augmented batch using 1-2 random bit-flips per sample.
     - Stack original and augmented views: `batch_x_stacked = np.concatenate([batch_x, batch_x_aug], axis=0)` (shape `(2B, 16)`).
     - Run `fwd = encoder.forward_with_intermediates(batch_x_stacked)`.
     - Extract `z = fwd["codes"]`. Split into original `z1 = z[:B]` and augmented `z2 = z[B:]`.
     - Update the MLP projector: `loss_res = contr.step(z1, z2)`.
     - Concatenate gradients: `dL_dcodes = np.concatenate([loss_res["d_z1"], loss_res["d_z2"]], axis=0)`.
     - Backprop through encoder: `grads = encoder.backward_from_code_grads(dL_dcodes, fwd["codes"], fwd["node_inputs"], batch_x_stacked)`.
  2. For `JEPALoss`:
     - Run `fwd = encoder.forward_with_intermediates(batch_x)`.
     - Extract `codes = fwd["all_codes_3d"]`.
     - Update predictors: `loss_res = jepa.step(codes)`.
     - Backprop through encoder: `grads = encoder.backward_from_code_grads(loss_res["code_grads"], fwd["codes"], fwd["node_inputs"], batch_x)`.
  3. For `SFALoss`:
     - Run `fwd = encoder.forward_with_intermediates(batch_x)`.
     - Extract `codes = fwd["all_codes_3d"]`.
     - Compute layer-wise SFA loss and gradients:
       `dL_dcodes = []`
       `for l in range(encoder.n_layers):`
           `sfa_res = sfa.forward(codes[l])`
           `dL_dcodes.append(sfa_res["dL_dz"])`
     - Backprop through encoder: `grads = encoder.backward_from_code_grads(dL_dcodes, fwd["codes"], fwd["node_inputs"], batch_x)`.
  4. For `HebbianLoss`:
     - Just call `hebb.update(encoder, batch_x)` inside the batch loop. It handles the forward pass and updates the node weights directly. No backprop.
  
- For JEPA, SFA, Contrastive encoder updates (after backward pass):
  Averaging parameter gradients across all $L$ layers:
  ```python
  dW_enc_accum = np.zeros_like(master.W_enc)
  db_enc_accum = np.zeros_like(master.b_enc)
  for l in range(encoder.n_layers):
      dW_enc_accum += grads["dL_dnodes"][l]["W_enc"]
      db_enc_accum += grads["dL_dnodes"][l]["b_enc"]
  dW_enc_accum /= encoder.n_layers
  db_enc_accum /= encoder.n_layers
  
  grad_dict = {
      "W_enc": dW_enc_accum,
      "b_enc": db_enc_accum,
      "embedding": grads["dL_dembedding"],
  }
  encoder_adam.step(encoder_params, grad_dict)
  ```

### Evaluation Protocol:
- Evaluate using the standard `evaluate_hierarchical_encoder` function from `src/eval_phase1.py`!
- Untrained baselines: evaluate without any training epochs.

### Output:
- Save results to `phase_1/objectives_results.csv` with exactly these columns:
  `config, seed, test_accuracy, train_accuracy, sparsity, n_params`

Write `src/run_phase1_v2.py` cleanly, run it end-to-end (it should take a couple of minutes to run all 35 configurations since we use pure numpy with optimized batch sizes), print the results summary table to the console, and verify the output CSV is saved. Proceed directly to implementation! Thank you!