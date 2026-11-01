#!/usr/bin/env python3
"""Turn the registry's main table (registry-ME.md) into ArtifactData batch files for the board's `sessions` collection.

Usage: python3 ~/.claude/orchestra/board_sync.py <ME> <out dir> [--known h1,h2] [--versions h1=3,h2=2]
Output: <out dir>/sessions-<handle>.json per row, and <out dir>/writes.json (pass it as the `writes` of an ArtifactData batch).
--known: handles currently on the board, comma-separated. Any of them missing from the registry (a closed session) becomes a delete.
--versions: updating an existing doc needs if_version. Read the versions first with `ArtifactData list sessions` and pass them as 'insta=3,global=2'.
"""
import argparse
import datetime
import json
import os

ap = argparse.ArgumentParser()
ap.add_argument("me")
ap.add_argument("out")
ap.add_argument("--known", default="", help="handles currently on the board, comma-separated")
ap.add_argument("--versions", default="", help="versions of docs already on the board: 'insta=3,global=2' (from ArtifactData list sessions)")
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)
lines = open(os.path.expanduser(f"~/.claude/orchestra/registry-{a.me}.md")).read().split("\n")
head = next(i for i, l in enumerate(lines) if l.startswith("| handle |"))
ver = dict(x.split("=") for x in a.versions.split(",") if "=" in x)
writes, seen, order = [], set(), 0
for l in lines[head + 2:]:
    if not l.startswith("| "):
        break
    c = [x.strip() for x in l.strip().strip("|").split("|")]
    h, name, _pane, _folder, role, state, now, queue, upd = c[:9]
    order += 1
    seen.add(h)
    p = f"{a.out}/sessions-{h}.json"
    json.dump({"order": order, "name": name, "role": role, "state": state, "now": now, "queue": queue, "updated": upd},
              open(p, "w"), ensure_ascii=False)
    w = {"op": "set", "collection": "sessions", "doc_id": h, "file_path": p}
    if h in ver:
        w["if_version"] = int(ver[h])
    writes.append(w)
for h in [x for x in a.known.split(",") if x and x not in seen]:
    w = {"op": "delete", "collection": "sessions", "doc_id": h}
    if h in ver:
        w["if_version"] = int(ver[h])
    writes.append(w)
json.dump(writes, open(f"{a.out}/writes.json", "w"), ensure_ascii=False)
print(f"{len(writes)} writes -> {a.out}/writes.json ({datetime.datetime.now():%m-%d %H:%M})")
