import csv, os
from collections import Counter

with open('phase_3/phase3_full_results.csv', 'r', newline='') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print('Total rows:', len(rows))
pairs = [(r['variant'], r['seed']) for r in rows]
counts = Counter(pairs)
duplicates = [(p, c) for p, c in counts.items() if c > 1]
print('Duplicates:', duplicates)
print('Unique pairs:', sorted(set(pairs)))

missing = []
for s in [42,43,44,45,46]:
    if ('P3-A', str(s)) not in counts:
        missing.append(s)
print('Missing P3-A seeds:', missing)
