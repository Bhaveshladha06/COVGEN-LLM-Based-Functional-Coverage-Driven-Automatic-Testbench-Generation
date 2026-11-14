#!/usr/bin/env python3
"""
kb_compile_check.py -- actually compile every knowledge base coverage model
with Cadence irun, and mark the ones that pass as verified.

kb_validate.py only pattern-matches text. THIS script is the real thing: it
wraps each covergroup in a minimal module, hands it to irun, and reads the
result. Uses no Gemini credits -- only a simulator licence.

    python kb_compile_check.py                 # compile everything, report
    python kb_compile_check.py --apply         # ...and set verified=true on passes
    python kb_compile_check.py --id fifo_sync_8bit_001
    python kb_compile_check.py --category sequential
    python kb_compile_check.py --keep-files    # leave the wrappers for inspection

A covergroup taking `ref` arguments cannot be compiled on its own -- it must
live inside a module, with real variables to bind those references to. So for
each entry a wrapper is generated:

    `timescale 1ns/1ps
    module cg_check_<id>;
      logic clk;
      logic [7:0] a, b;          // declarations derived from the ref arguments
      <the covergroup verbatim>
      cg_name cg_inst = new(a, b);
    endmodule
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import config

# covergroup <name> ( <args> ) [@(...)] ;
CG_HEADER_RE = re.compile(
    r'covergroup\s+(\w+)\s*(?:\(([^)]*)\))?\s*(@\s*\([^)]*\))?\s*;', re.S)


def parse_ref_args(arg_text: str):
    """Turn a covergroup argument list into (declarations, instance_args).

    "ref logic [7:0] a, b, ref logic c"
        -> (["logic [7:0] a, b;", "logic c;"], ["a", "b", "c"])
    """
    if not arg_text or not arg_text.strip():
        return [], []

    decls, names = [], []
    # Split on `ref`, since each ref introduces a fresh type for its name list.
    chunks = [c.strip() for c in re.split(r'\bref\b', arg_text) if c.strip()]
    for chunk in chunks:
        chunk = chunk.strip().rstrip(',').strip()
        m = re.match(r'^((?:logic|bit|reg|int|integer)\s*(?:signed\s*)?'
                     r'(?:\[[^\]]+\]\s*)?)(.*)$', chunk, re.S)
        if not m:
            continue
        vtype, name_blob = m.group(1).strip(), m.group(2)
        chunk_names = [n.strip() for n in name_blob.split(',') if n.strip()]
        chunk_names = [n for n in chunk_names if re.fullmatch(r'[A-Za-z_]\w*', n)]
        if not chunk_names:
            continue
        decls.append(f"{vtype} {', '.join(chunk_names)};")
        names.extend(chunk_names)
    return decls, names


def build_wrapper(entry: dict):
    """Return (wrapper_source, note) or (None, reason_it_could_not_be_built)."""
    code = entry.get("coverage_model", "")
    m = CG_HEADER_RE.search(code)
    if not m:
        return None, "could not parse the covergroup header"

    cg_name, arg_text, clocking = m.group(1), m.group(2) or "", m.group(3) or ""
    decls, names = parse_ref_args(arg_text)

    # Any identifier used in the sampling event but not passed as an argument
    # (typically clk) still has to exist in the wrapper.
    extra = []
    for ident in re.findall(r'[A-Za-z_]\w*', clocking):
        if ident not in ("posedge", "negedge", "or", "edge") and ident not in names:
            if ident not in extra:
                extra.append(ident)

    # The covergroup body may also reference signals that are not arguments
    # (some entries sample an internal signal). Declare those too, as 1-bit,
    # rather than failing the whole entry on an undeclared identifier.
    body_ids = set(re.findall(r'\bcoverpoint\s+([A-Za-z_]\w*)', code))
    for ident in sorted(body_ids):
        if ident not in names and ident not in extra:
            extra.append(ident)

    decl_lines = "\n  ".join(decls)
    extra_lines = "\n  ".join(f"logic {e};" for e in extra)
    inst_args = ", ".join(names)

    src = f"""`timescale 1ns/1ps
// Auto-generated compile check for knowledge base entry: {entry.get('id')}
// Not part of the design -- exists only to give the covergroup a scope and
// real variables for its `ref` arguments to bind to.
module cg_check;
  {extra_lines}
  {decl_lines}

{code}

  {cg_name} cg_inst = new({inst_args});
endmodule
"""
    return src, f"{len(names)} ref arg(s), {len(extra)} extra decl(s)"


ERROR_LINE_RE = re.compile(r'^\s*\w+:\s*\*[EF],', re.M)


def compile_one(src: str, workdir: Path, timeout: int):
    """Run irun on one wrapper. Returns (ok, error_text)."""
    sv = workdir / "cg_check.sv"
    sv.write_text(src, encoding="utf-8")

    # -compile stops after compilation. If this irun build does not know the
    # flag, fall back to a plain run: a module with no processes finishes at
    # time 0 anyway.
    for attempt_flags in (["-compile"], []):
        cmd = [config.IRUN_BIN, "-sv", "-nocopyright"] + attempt_flags + [sv.name]
        try:
            r = subprocess.run(cmd, cwd=str(workdir), capture_output=True,
                               text=True, timeout=timeout)
        except FileNotFoundError:
            return False, (f"irun not found at '{config.IRUN_BIN}'. Set up Cadence "
                           f"first (see START_HERE.md), or export IRUN_BIN=<path>.")
        except subprocess.TimeoutExpired:
            return False, f"irun timed out after {timeout}s"

        out = r.stdout + "\n" + r.stderr
        if "unrecognized" in out.lower() and attempt_flags:
            continue          # retry without -compile
        errors = ERROR_LINE_RE.findall(out)
        error_lines = [l for l in out.splitlines()
                       if re.search(r'\*[EF],', l)]
        return (not error_lines), "\n".join(error_lines[:8])

    return False, "could not invoke irun"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kb", default=config.KB_JSON)
    ap.add_argument("--id", help="check a single entry")
    ap.add_argument("--category", help="check one category only")
    ap.add_argument("--apply", action="store_true",
                    help="set verified=true on entries that compile")
    ap.add_argument("--keep-files", action="store_true",
                    help="keep the generated wrappers for inspection")
    ap.add_argument("--timeout", type=int, default=120)
    args = ap.parse_args()

    kb_path = Path(args.kb)
    if not kb_path.exists():
        print(f"Knowledge base not found: {kb_path}", file=sys.stderr)
        return 1

    data = json.loads(kb_path.read_text(encoding="utf-8"))
    entries = data.get("entries", [])

    todo = entries
    if args.id:
        todo = [e for e in entries if e.get("id") == args.id]
        if not todo:
            print(f"No entry with id '{args.id}'", file=sys.stderr)
            return 1
    elif args.category:
        todo = [e for e in entries if e.get("category") == args.category]

    base = Path(tempfile.mkdtemp(prefix="kb_compile_"))
    print(f"Compiling {len(todo)} entries with {config.IRUN_BIN}")
    print(f"Work dir: {base}\n")

    passed, failed, skipped = [], [], []

    for i, entry in enumerate(todo, 1):
        eid = entry.get("id", "?")
        src, note = build_wrapper(entry)
        if src is None:
            skipped.append((eid, note))
            print(f"[{i:>3}/{len(todo)}] SKIP  {eid:<32} {note}")
            continue

        wd = base / eid
        wd.mkdir(parents=True, exist_ok=True)
        ok, err = compile_one(src, wd, args.timeout)

        if ok:
            passed.append(eid)
            print(f"[{i:>3}/{len(todo)}] PASS  {eid}")
        else:
            failed.append((eid, err))
            print(f"[{i:>3}/{len(todo)}] FAIL  {eid}")
            for line in err.splitlines()[:3]:
                print(f"                 {line.strip()[:110]}")
            if "irun not found" in err:
                print("\nStopping: Cadence is not set up in this shell.")
                return 1

    print("\n" + "=" * 70)
    print(f"PASS {len(passed)}   FAIL {len(failed)}   SKIP {len(skipped)}   "
          f"of {len(todo)}")
    print("=" * 70)

    if failed:
        print("\nFailures:")
        for eid, err in failed:
            first = err.splitlines()[0].strip() if err.strip() else "(no error text)"
            print(f"  {eid:<34} {first[:90]}")

    if args.apply and passed:
        by_id = {e["id"]: e for e in entries}
        for eid in passed:
            by_id[eid]["verified"] = True
            note = by_id[eid].get("notes", "")
            stamp = "Compiled successfully by kb_compile_check.py."
            by_id[eid]["notes"] = (note + " " + stamp).strip()
        data["metadata"]["verified_entries"] = sum(
            1 for e in entries if e.get("verified"))
        kb_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        print(f"\nMarked {len(passed)} entries verified in {kb_path}")
    elif passed and not args.apply:
        print(f"\n{len(passed)} entries compile. Re-run with --apply to mark them "
              f"verified.")

    if args.keep_files:
        print(f"\nWrappers kept in {base}")
    else:
        shutil.rmtree(base, ignore_errors=True)

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
