#!/usr/bin/env python3
import pathlib, re, sys

p = pathlib.Path("services/common_lib/protos_generated")
if not p.exists():
    print("Directory not found:", p)
    sys.exit(1)

patched = 0
for path in p.glob("*_pb2_grpc.py"):
    s = path.read_text()
    s_new = re.sub(r'(^|\n)import\s+([0-9A-Za-z_]+_pb2)\s+as\s+([0-9A-Za-z_]+)', 
                   lambda m: f"{m.group(1)}from . import {m.group(2)} as {m.group(3)}", s)
    if s != s_new:
        path.write_text(s_new)
        patched += 1
        print("Patched", path)
print(f"Patched {patched} files")
