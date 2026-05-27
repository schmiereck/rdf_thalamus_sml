"""Generate Phase-1 dataset: 5 categories of 16-bit binary inputs."""

import numpy as np


def generate_phase1_dataset(n_train: int = 200, n_test: int = 100, seed: int = 42):
    """Generate a dataset with 5 categories of 16-bit binary inputs.

    Args:
        n_train: Number of training samples per category.
        n_test: Number of testing samples per category.
        seed: Random seed for reproducibility.

    Returns:
        Dictionary with keys 'train_x', 'train_y', 'test_x', 'test_y'.
    """
    rng = np.random.default_rng(seed)

    def cat0_uniform(count):
        """Category 0: Uniform random bits."""
        return (rng.random((count, 16)) < 0.5).astype(np.float64)

    def cat1_single_blob(count):
        """Category 1: Single-blob pattern."""
        result = np.zeros((count, 16), dtype=np.float64)
        for i in range(count):
            start = rng.integers(0, 13)   # 0 to 12 inclusive
            width = rng.integers(2, 7)    # 2 to 6 inclusive
            end = min(start + width, 16)
            result[i, start:end] = 1.0
        return result

    def cat2_two_blob(count):
        """Category 2: Two non-overlapping blobs."""
        result = np.zeros((count, 16), dtype=np.float64)
        for i in range(count):
            while True:
                width1 = rng.integers(2, 5)  # 2 to 4 inclusive
                start1 = rng.integers(0, 16 - width1 + 1)
                width2 = rng.integers(2, 5)  # 2 to 4 inclusive
                start2 = rng.integers(0, 16 - width2 + 1)
                # Check non-overlapping
                if start1 + width1 <= start2 or start2 + width2 <= start1:
                    break
            result[i, start1:start1 + width1] = 1.0
            result[i, start2:start2 + width2] = 1.0
        return result

    def cat3_periodic(count):
        """Category 3: Periodic patterns with 5% noise."""
        result = np.zeros((count, 16), dtype=np.float64)
        for i in range(count):
            p = rng.choice([2, 3, 4])
            phase = rng.integers(0, int(p))
            for j in range(16):
                bit = 1.0 if (j + phase) % p < p // 2 else 0.0
                # 5% noise flip
                if rng.random() < 0.05:
                    bit = 1.0 - bit
                result[i, j] = bit
        return result

    def cat4_mixed_noise(count):
        """Category 4: Base pattern from cat 1/2/3, then 15% bit flips."""
        result = np.zeros((count, 16), dtype=np.float64)
        for i in range(count):
            cat_choice = rng.integers(0, 3)
            if cat_choice == 0:
                # Single blob
                start = rng.integers(0, 13)
                width = rng.integers(2, 7)
                base = np.zeros(16, dtype=np.float64)
                base[start:min(start + width, 16)] = 1.0
            elif cat_choice == 1:
                # Two blob
                while True:
                    w1 = rng.integers(2, 5)
                    s1 = rng.integers(0, 16 - w1 + 1)
                    w2 = rng.integers(2, 5)
                    s2 = rng.integers(0, 16 - w2 + 1)
                    if s1 + w1 <= s2 or s2 + w2 <= s1:
                        break
                base = np.zeros(16, dtype=np.float64)
                base[s1:s1 + w1] = 1.0
                base[s2:s2 + w2] = 1.0
            else:
                # Periodic
                p = rng.choice([2, 3, 4])
                phase = rng.integers(0, int(p))
                base = np.array(
                    [1.0 if (j + phase) % p < p // 2 else 0.0 for j in range(16)],
                    dtype=np.float64,
                )

            # Flip 15% of bits
            for j in range(16):
                if rng.random() < 0.15:
                    base[j] = 1.0 - base[j]
            result[i] = base
        return result

    # Generate for training
    train_x = np.vstack([
        cat0_uniform(n_train),
        cat1_single_blob(n_train),
        cat2_two_blob(n_train),
        cat3_periodic(n_train),
        cat4_mixed_noise(n_train),
    ])
    train_y = np.repeat(np.arange(5), n_train)

    # Generate for testing
    test_x = np.vstack([
        cat0_uniform(n_test),
        cat1_single_blob(n_test),
        cat2_two_blob(n_test),
        cat3_periodic(n_test),
        cat4_mixed_noise(n_test),
    ])
    test_y = np.repeat(np.arange(5), n_test)

    return {
        "train_x": train_x,
        "train_y": train_y,
        "test_x": test_x,
        "test_y": test_y,
    }


if __name__ == "__main__":
    dataset = generate_phase1_dataset()
    print("train_x shape:", dataset["train_x"].shape, "dtype:", dataset["train_x"].dtype)
    print("train_y shape:", dataset["train_y"].shape, "dtype:", dataset["train_y"].dtype)
    print("test_x shape:", dataset["test_x"].shape, "dtype:", dataset["test_x"].dtype)
    print("test_y shape:", dataset["test_y"].shape, "dtype:", dataset["test_y"].dtype)
    print()
    print("Train label distribution:")
    for label in range(5):
        count = np.sum(dataset["train_y"] == label)
        print(f"  Label {label}: {count}")
    print()
    print("Test label distribution:")
    for label in range(5):
        count = np.sum(dataset["test_y"] == label)
        print(f"  Label {label}: {count}")
    print()
    print("train_x unique values:", np.unique(dataset["train_x"]))
    print("test_x unique values:", np.unique(dataset["test_x"]))
