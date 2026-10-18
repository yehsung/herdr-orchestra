#!/usr/bin/env python3
"""Conductor tab layout: top = one row of worker panes (any count, equal width), bottom = the conductor pane.

  row.py add [--cwd PATH]   create a new pane at the right end of the row and print its pane_id
  row.py adopt <pane_id>    move a pane from elsewhere to the right end of the row and print its new pane_id
  row.py balance            re-fit the conductor height and the row widths (run after closing a pane)

Conductor pane = HERDR_PANE_ID, tab = HERDR_TAB_ID (set automatically when run inside the conductor session).
Conductor height ratio defaults to 0.3; override with ORCHESTRA_CONDUCTOR_RATIO.
"""
import json
import os
import socket
import subprocess
import sys

CONDUCTOR_RATIO = float(os.environ.get("ORCHESTRA_CONDUCTOR_RATIO", "0.3"))


def api(method, params):
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect(os.environ["HERDR_SOCKET_PATH"])
    s.sendall((json.dumps({"id": "orchestra", "method": method, "params": params}) + "\n").encode())
    buf = b""
    while not buf.endswith(b"\n"):
        chunk = s.recv(65536)
        if not chunk:
            break
        buf += chunk
    s.close()
    res = json.loads(buf)
    if "error" in res:
        sys.exit(f"herdr {method} failed: {res['error']}")
    return res["result"]


def cli(*args):
    out = subprocess.run(["herdr", *args], capture_output=True, text=True)
    if out.returncode != 0:
        sys.exit(f"herdr {' '.join(args[:2])} failed: {out.stderr.strip()}")
    return json.loads(out.stdout)


def tree():
    root = api("layout.export", {"tab_id": os.environ["HERDR_TAB_ID"]})["layout"]["root"]
    me = os.environ["HERDR_PANE_ID"]
    if root["type"] == "pane":
        if root["pane_id"] != me:
            sys.exit("the only pane in this tab is not the conductor pane")
        return None
    if not (root["direction"] == "down" and root["second"]["type"] == "pane" and root["second"]["pane_id"] == me):
        sys.exit("this tab is not shaped 'one row above / conductor below'. Fix the tab by hand, then run again")
    return root["first"]


def leaves(node):
    return 1 if node["type"] == "pane" else leaves(node["first"]) + leaves(node["second"])


def rightmost(node):
    while node["type"] == "split":
        node = node["second"]
    return node["pane_id"]


def balance():
    row = tree()
    if row is None:
        return
    tab = os.environ["HERDR_TAB_ID"]
    api("layout.set_split_ratio", {"tab_id": tab, "path": [], "ratio": 1 - CONDUCTOR_RATIO})

    def walk(node, path):
        if node["type"] == "pane":
            return
        if node["direction"] != "right":
            sys.exit("the worker row contains a vertical split. Workers must only be split side by side")
        api("layout.set_split_ratio", {"tab_id": tab, "path": path, "ratio": leaves(node["first"]) / leaves(node)})
        walk(node["first"], path + [False])
        walk(node["second"], path + [True])

    walk(row, [False])


def place(new_pane, first):
    # herdr splits only right/down, so the first worker lands below the conductor;
    # swap the two so the conductor ends up at the bottom (pane ids and processes are kept).
    if first:
        cli("pane", "swap", "--source-pane", os.environ["HERDR_PANE_ID"], "--target-pane", new_pane)
    balance()
    print(new_pane)


def add(cwd):
    row = tree()
    if row is None:
        res = cli("pane", "split", os.environ["HERDR_PANE_ID"], "--direction", "down", "--cwd", cwd, "--no-focus")
    else:
        res = cli("pane", "split", rightmost(row), "--direction", "right", "--cwd", cwd, "--no-focus")
    place(res["result"]["pane"]["pane_id"], row is None)


def adopt(pane_id):
    row = tree()
    target, direction = (os.environ["HERDR_PANE_ID"], "down") if row is None else (rightmost(row), "right")
    res = cli("pane", "move", pane_id, "--tab", os.environ["HERDR_TAB_ID"], "--split", direction,
              "--target-pane", target, "--no-focus")
    place(res["result"]["move_result"]["pane"]["pane_id"], row is None)


if __name__ == "__main__":
    args = sys.argv[1:]
    if os.environ.get("HERDR_ENV") != "1":
        sys.exit("must run inside a herdr pane")
    if not args:
        sys.exit(__doc__)
    if args[0] == "add":
        add(args[args.index("--cwd") + 1] if "--cwd" in args else os.getcwd())
    elif args[0] == "adopt" and len(args) == 2:
        adopt(args[1])
    elif args[0] == "balance":
        balance()
    else:
        sys.exit(__doc__)
