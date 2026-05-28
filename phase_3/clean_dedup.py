import csv

INPUT = "phase_3/phase3_full_results.csv"
rows = []
seen = set()
with open(INPUT) as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    for row in reader:
        key = (row['variant'], row['seed'])
        if key not in seen:
            seen.add(key)
            rows.append(row)

with open(INPUT, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
print(f"Cleaned: {len(rows)} unique rows")
