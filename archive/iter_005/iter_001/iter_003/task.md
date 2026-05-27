Create the spatiotemporal encoder file at `src/spatiotemporal_encoder.py`.
Implement the `SpatiotemporalEncoder` class as designed.
It should support the three variants (P3-A, P3-B, P3-C) with d=16, d_out=16, and cross-layer weight sharing (one master spatial node and one master temporal node, which are the same UniversalNode object in P3-C).
It should implement:
1. `forward_with_intermediates(self, x_binary: np.ndarray) -> dict` which embeds input (using a non-learned lookup table initialized with Xavier scale), runs 3 spatial layers, transposes, runs 3 temporal layers, and average-pools across space and time.
2. `backward(self, fwd: dict, dL_dspatial_codes: list[np.ndarray], dL_dtemporal_codes: list[np.ndarray], alpha: float) -> dict` which propagates gradients back through the temporal and spatial passes.
Include a simple test in `__main__` to verify that forward and backward run without any shape errors.