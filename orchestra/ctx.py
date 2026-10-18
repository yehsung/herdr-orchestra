#!/usr/bin/env python3
"""Read a worker session's context usage (%) from its status line. Usage: ctx.py <handle> [...]

Expects a Claude Code status line that shows a 10-cell bar and a percentage, e.g.
  '◆ Fable 5.1 │ ████████░░ │ 81% │ 812K/1.0M'   (a narrow pane may cut it to '81…')
Prints the number when visible, otherwise '~N0' estimated from the bar, otherwise '?'.
Any status line plugin that prints such a bar works (the author uses claude-dashboard).
"""
import re
import subprocess
import sys


def read(handle):
    out = subprocess.run(["herdr", "agent", "read", handle, "--source", "visible"],
                         capture_output=True, text=True).stdout
    for line in reversed(out.splitlines()):
        if "█" in line or "░" in line:
            m = re.search(r"(\d{1,3})%", line)
            if m:
                return m.group(1)
            m = re.search(r"([█░]{10})", line)
            if m:
                return f"~{m.group(1).count('█') * 10}"
    return "?"


for h in sys.argv[1:]:
    print(h, read(h))
