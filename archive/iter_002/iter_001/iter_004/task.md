Implement `src/dataset_phase1.py` with the function `generate_phase1_dataset(n_train=200, n_test=100, seed=42)`.
This function must generate 5 categories of 16-bit binary inputs, with `n_train` training samples and `n_test` testing samples per category, totaling 1000 training samples and 500 testing samples.

Follow the specifications exactly:
- **Category 0 (Uniform random bits)**: Each bit independently 0 or 1 with probability 0.5. Label = 0.
- **Category 1 (Single-blob)**: Pick a random start position (0 to 12) and width (2 to 6). Set bits in `[start, start+width)` to 1, rest to 0. Slicing in Python is fine (e.g. `bits[start:start+width] = 1.0` is robust even if start+width > 16, but make sure to generate start such that it is always in `[0, 12]` and width is in `[2, 6]`). Label = 1.
- **Category 2 (Two-blob)**: Pick two non-overlapping intervals of width 2-4 each. Set bits in both intervals to 1, rest to 0. To do this, you can use a simple `while True` loop to pick `start1, width1` and `start2, width2` such that `start1 + width1 <= start2` or `start2 + width2 <= start1`. Widths should be randomly selected in `[2, 4]`, and start positions in `[0, 16-width]`. Label = 2.
- **Category 3 (Periodic patterns)**: Pick period `p` in `{2, 3, 4}` and random phase offset. For each index `i` in `0..15`, set `bit[i] = 1.0` if `(i + phase) % p < p // 2` else `0.0`. Add slight noise by flipping each bit independently with 5% probability (i.e. `rng.random() < 0.05`). Label = 3.
- **Category 4 (Mixed noise)**: Pick a structured base pattern from categories 1, 2, or 3 (chosen uniformly at random). Then flip 15% of the bits randomly (i.e. for each of the 16 bits, flip it with 15% probability). Label = 4.

The returned value of `generate_phase1_dataset` must be a dictionary with keys `'train_x'`, `'train_y'`, `'test_x'`, `'test_y'`, all being numpy arrays.
- `train_x` should have shape `(1000, 16)` and type `np.float64` containing binary elements 0.0 or 1.0.
- `train_y` should have shape `(1000,)` containing integers from 0 to 4.
- `test_x` should have shape `(500, 16)` and type `np.float64`.
- `test_y` should have shape `(500,)` containing integers from 0 to 4.

Please add a self-test in `if __name__ == "__main__":` to generate the dataset and print the shapes and label distributions to verify everything is correct. Then save the file.