## Task: Create Pre-Registration File and Experimental Harness

You are building the foundation for Phase 0 of the HSUN (Hierarchical Sparse Universal Nodes) project. This is a smoke test to verify the experimental pipeline.

### 1. Create `src/pre_registration.md`

Write a pre-registration file with the following CORRECTED hypothesis and falsification criteria (incorporating the Research Manager's strategic guidance):

**Hypothesis:** With 3 binary inputs (8 possible states), all five encoder types can be trained end-to-end. Non-trivial distributed encoders (P0-B SDR, P0-C SOM, P0-D Sparse AE, P0-E Predictive Coding) will produce codes where the Spearman rank correlation between pairwise code cosine similarity and pairwise input inverse Hamming distance is ≥ 0.6 when computed on DISTINCT (off-diagonal) pairs only. P0-A (lookup table / one-hot) is expected to FAIL this criterion (ρ ≈ 0) because one-hot vectors are mutually orthogonal — this failure is the scientific justification for requiring distributed representations. Locally-trained encoders (P0-B, P0-C, P0-E) will achieve similarity preservation within 0.15 (absolute ρ difference) of the globally-trained sparse autoencoder (P0-D) baseline.

**Falsification criteria:** The hypothesis is falsified if EITHER:
1. Any non-trivial encoder (P0-B through P0-E) fails to achieve Spearman ρ ≥ 0.6 on OFF-DIAGONAL pairs between code cosine similarity and input inverse Hamming distance, OR
2. Any locally-trained encoder (P0-B, P0-C, P0-E) achieves ρ more than 0.15 below the P0-D Sparse Autoencoder baseline on off-diagonal pairs.
3. Additionally, if any implementation cannot run end-to-end (crashes, fails to converge, or produces NaN/constant outputs), the smoke test fails.

**Critical metric detail:** Spearman ρ is computed STRICTLY on distinct pairs (off-diagonal elements of the pairwise similarity matrix). Self-pairs (diagonal, where cosine similarity = 1.0 for identical inputs) are excluded to avoid artificial inflation.

**P0-A expected result:** P0-A (one-hot lookup table) is EXEMPT from the ρ ≥ 0.6 threshold. We expect ρ ≈ 0 because one-hot vectors for distinct inputs are mutually orthogonal (cosine similarity = 0 regardless of Hamming distance). This failure validates the need for distributed representations.

### 2. Create `src/harness.py`

Build the experimental harness containing:

#### Dataset Generator
- Enumerate all 8 binary-3-tuples: (0,0,0), (0,0,1), ..., (1,1,1)
- Generate noise variants: for each base state, create 10 variants by flipping each bit independently with probability 0.1
- Total: 8 base states + 80 noise variants = 88 samples
- Each sample is a numpy array of shape (3,) with values 0 or 1
- Provide method to get just the 8 base states (for pairwise evaluation)
- Provide method to get all 88 samples (for training)

#### Similarity Evaluator
- Compute pairwise Hamming distance for 8 base states (8×8 matrix)
- Compute inverse Hamming distance: 1 / (1 + hamming_distance)
- Compute pairwise cosine similarity of encoded codes for 8 base states
- **CRITICAL:** Compute Spearman ρ ONLY on off-diagonal pairs (exclude self-pairs where i==j). Use scipy.stats.spearmanr on the flattened upper triangle (or lower triangle) of both matrices.
- Return: spearman_rho, p_value, and the raw pair lists for plotting

#### Encoder Interface (Abstract Base Class)
```python
from abc import ABC, abstractmethod
import numpy as np

class EncoderBase(ABC):
    @abstractmethod
    def train(self, inputs: np.ndarray, epochs: int = 50) -> dict:
        """Train the encoder on inputs. Return training metrics dict."""
        pass
    
    @abstractmethod
    def encode(self, inputs: np.ndarray) -> np.ndarray:
        """Encode inputs, return array of shape (n_samples, dim_out)."""
        pass
    
    @property
    @abstractmethod
    def dim_out(self) -> int:
        """Output dimension of the encoder."""
        pass
    
    @property
    def name(self) -> str:
        return self.__class__.__name__
```

#### Utility Functions
- `compute_sparsity(codes, threshold=0.01)`: fraction of activations below threshold
- `compute_reconstruction_error(original, reconstructed)`: MSE
- `linear_probe_accuracy(codes, labels)`: simple logistic regression accuracy (for future use, but implement now)

### 3. Create `src/encoders/__init__.py`

A simple registry that can import and list all available encoders. For now, just create the file with a placeholder registry dict.

### File naming
- All files use snake_case
- Classes use PascalCase
- Use numpy for numerical operations, scipy for Spearman correlation
- No external ML libraries (no torch, no tensorflow) — use only numpy/scipy for Phase 0

### Important
- All code goes in `src/` directory
- Do NOT create code in `archive/`
- Make sure the harness works with a quick test: create a simple test that generates the dataset and checks shapes