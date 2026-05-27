"""Fix imports and train_grid/test_grid in spatiotemporal_dataset.py."""

path = r"src\spatiotemporal_dataset.py"
with open(path, "r") as f:
    content = f.read()

# Fix imports: src.harness -> harness
content = content.replace("from src.harness import SimpleLogisticRegression", "from harness import SimpleLogisticRegression")

# Fix train_grid / test_grid
old_return = '''    return {
        "train_x": train_x,
        "train_y": train_y,
        "test_x": test_x,
        "test_y": test_y,
        "train_grid": train_parts[0].reshape(n_train_per_class, N_SPATIAL, N_TIMESTEPS),
        "test_grid": test_parts[0].reshape(n_test_per_class, N_SPATIAL, N_TIMESTEPS),
    }'''

new_return = '''    train_grid_all = np.concatenate(train_parts, axis=0)
    test_grid_all = np.concatenate(test_parts, axis=0)

    return {
        "train_x": train_x,
        "train_y": train_y,
        "test_x": test_x,
        "test_y": test_y,
        "train_grid": train_grid_all,
        "test_grid": test_grid_all,
    }'''

content = content.replace(old_return, new_return)

with open(path, "w") as f:
    f.write(content)

print("Fixed.")
