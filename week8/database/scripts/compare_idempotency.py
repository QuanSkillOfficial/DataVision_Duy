import json
import sys

d1 = json.load(open(sys.argv[1]))["counts"]
d2 = json.load(open(sys.argv[2]))["counts"]

result = {"pass": True, "tables": {}}
for t in d1:
    match = d1[t] == d2.get(t)
    result["tables"][t] = {"run1": d1[t], "run2": d2.get(t), "match": match}
    if not match:
        result["pass"] = False

print(json.dumps(result, indent=2))

if not result["pass"]:
    sys.exit(1)
