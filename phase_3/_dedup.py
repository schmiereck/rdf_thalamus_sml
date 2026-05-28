"""Just deduplicate the CSV."""
import csv

RESULTS_CSV = 'phase_3/phase3_full_results.csv'

with open(RESULTS_CSV, 'r', newline='') as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows = list(reader)

print(f"Total rows before dedup: {len(rows)}")

seen = set()
unique_rows = []
for row in rows:
    key = (row['variant'], row['seed'])
    if key not in seen:
        seen.add(key)
        unique_rows.append(row)

print(f"Total rows after dedup:  {len(unique_rows)}")

with open(RESULTS_CSV, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(unique_rows)

print("Done.")
