Please modify `src/hierarchical_encoder.py` to support list-of-arrays in `backward_from_code_grads` natively:

1. Update `backward_from_code_grads(self, dL_dcodes, codes, node_inputs, x_binary)`:
   - Check if `dL_dcodes` is a list.
   - If it is a list of arrays (one per layer, each of shape `(batch, n_nodes_l, d_out)`):
     - Initialize the propagated gradient `dL_dx_prop` to zeros of shape `(batch, self.n_nodes_per_layer[-1], self.d_out)`.
   - If it is not a list (i.e. single numpy array):
     - Initialize `dL_dx_prop = dL_dcodes.reshape(batch, n_nodes_last, self.d_out)`.
   - Inside the loop over layers `for l in reversed(range(self.n_layers))`:
     - The total incoming gradient for this layer's codes is `dL_dx_total = dL_dx_prop + dL_dcodes[l]` if `dL_dcodes` is a list, else `dL_dx_prop`.
     - Use `dL_dx_total` instead of `dL_dx` to extract the gradient for each position `p`: `dL_da = dL_dx_total[:, p, :].copy()`.
     - At the end of each layer $l > 0$, set `dL_dx_prop` to `dL_dlayer_input` (padded to `self.d_out` if `self.d_out > self.d` as in the current code).
   - This ensures that local gradients at every layer are correctly added and propagated!

2. Run `src/test_objectives.py` to verify that all existing tests pass perfectly.

Use the `write_file` tool to directly modify `src/hierarchical_encoder.py` and verify. Thank you!