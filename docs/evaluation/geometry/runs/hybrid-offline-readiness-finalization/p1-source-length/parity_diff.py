import json, sys
a = [json.loads(l) for l in open("parity-main.jsonl", encoding="utf-8")]
b = [json.loads(l) for l in open("parity-new.jsonl", encoding="utf-8")]
assert [x["text"] for x in a] == [x["text"] for x in b]
diff = []
for x, y in zip(a, b):
    ch = {k: (x[k], y[k]) for k in ("lengths", "nonpositive", "unread") if x[k] != y[k]}
    if ch:
        diff.append({"text": x["text"], **ch})
json.dump(diff, open("parity-diff.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("texts", len(a), "changed", len(diff))
for d in diff:
    print("-" * 80); print(d["text"][:300].replace("\n", " "))
    for k in ("lengths", "nonpositive", "unread"):
        if k in d: print(f"  {k}: {d[k][0]}  ->  {d[k][1]}")
