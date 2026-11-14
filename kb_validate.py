#!/usr/bin/env python3
"""
kb_validate.py -- structural linter for knowledge base coverage models.

This is NOT a SystemVerilog compiler. It checks the specific rules that irun
15.20 enforces and that an LLM (or a human) most often violates -- the exact
failures seen in this project's own runs:

  *E,ECGECL  unlabelled coverpoint / cross
  *E,ECGEGN  covergroup not closed (usually a malformed bins earlier)
  bins with `iff`            -- illegal, iff belongs on the coverpoint
  transition bins over variables -- must be constant
  crossing a transition coverpoint -- illegal per LRM

Passing this does not mean an entry compiles. It means the entry does not
contain the classes of error we already know break irun 15.20. Entries still
need a real tool run before they are marked verified.

    python kb_validate.py                 # validate the knowledge base
    python kb_validate.py --strict        # exit non-zero on warnings too
"""

import argparse
import json
import re
import sys
from pathlib import Path

import config

COVERPOINT_RE = re.compile(r'^\s*(?:(\w+)\s*:\s*)?coverpoint\b', re.M)
CROSS_RE = re.compile(r'^\s*(?:(\w+)\s*:\s*)?cross\b', re.M)
BINS_RE = re.compile(r'^\s*(?:wildcard\s+|illegal_|ignore_)?bins\b.*$', re.M)
TRANSITION_RE = re.compile(r'=>')
IDENT_RE = re.compile(r'[A-Za-z_]\w*')

SV_LITERAL_RE = re.compile(r"^\s*\d*'[bodhBODH][0-9a-fA-FxzXZ_?]+\s*$|^\s*\d+\s*$")


def _covergroup_body(code: str):
    """Return the text between the covergroup header and endgroup."""
    m = re.search(r'covergroup\b.*?;(.*?)\bendgroup\b', code, re.S)
    return m.group(1) if m else None


def _coverpoint_blocks(body: str):
    """Yield (label, inner_text) for each coverpoint with a brace block."""
    for m in re.finditer(r'(?:(\w+)\s*:\s*)?coverpoint\s+[^{;]+\{', body):
        start = m.end() - 1
        depth, i = 0, start
        while i < len(body):
            if body[i] == '{':
                depth += 1
            elif body[i] == '}':
                depth -= 1
                if depth == 0:
                    break
            i += 1
        yield m.group(1), body[start + 1:i]


def validate_entry(entry: dict):
    """Return (errors, warnings) for one entry."""
    errors, warnings = [], []
    eid = entry.get("id", "<no id>")
    code = entry.get("coverage_model", "")

    if not code.strip():
        return [f"{eid}: empty coverage_model"], []

    # --- structural ---------------------------------------------------------
    if "covergroup" not in code:
        errors.append(f"{eid}: no covergroup declaration")
    if "endgroup" not in code:
        errors.append(f"{eid}: missing endgroup (would be *E,ECGEGN)")
    if code.count("{") != code.count("}"):
        errors.append(f"{eid}: unbalanced braces "
                      f"({code.count('{')} open, {code.count('}')} close)")

    body = _covergroup_body(code)
    if body is None:
        errors.append(f"{eid}: could not isolate covergroup body")
        return errors, warnings

    # --- every coverpoint and cross must be labelled ------------------------
    for m in COVERPOINT_RE.finditer(body):
        if not m.group(1):
            errors.append(f"{eid}: unlabelled coverpoint (would be *E,ECGECL): "
                          f"{body[m.start():m.start() + 60].strip()!r}")
    for m in CROSS_RE.finditer(body):
        if not m.group(1):
            errors.append(f"{eid}: unlabelled cross (would be *E,ECGECL): "
                          f"{body[m.start():m.start() + 60].strip()!r}")

    # --- bins-level rules ---------------------------------------------------
    transition_cps = set()
    for label, inner in _coverpoint_blocks(body):
        for bm in BINS_RE.finditer(inner):
            line = bm.group(0).strip()

            if re.search(r'\biff\b', line):
                errors.append(f"{eid}: `iff` on a bins statement is illegal "
                              f"(belongs on the coverpoint): {line[:70]!r}")

            if TRANSITION_RE.search(line):
                if label:
                    transition_cps.add(label)
                # every operand of => must be a constant
                for side in re.findall(r'\(([^)]*=>[^)]*)\)', line):
                    for operand in side.split("=>"):
                        operand = operand.strip()
                        if not operand:
                            continue
                        if not SV_LITERAL_RE.match(operand):
                            if IDENT_RE.fullmatch(operand):
                                errors.append(
                                    f"{eid}: transition bin uses variable "
                                    f"{operand!r}; must be a constant: {line[:70]!r}")

    # --- a coverpoint with transition bins may not be crossed ---------------
    for m in re.finditer(r'(?:\w+\s*:\s*)?cross\s+([^;{]+)', body):
        members = [x.strip() for x in m.group(1).split(",")]
        for member in members:
            if member in transition_cps:
                errors.append(f"{eid}: cross includes {member!r}, which contains "
                              f"transition bins -- illegal per LRM")

    # --- softer signals -----------------------------------------------------
    if not re.search(r'covergroup\s+\w+\s*\(', code):
        warnings.append(f"{eid}: covergroup takes no arguments; the seed style "
                        f"passes signals as `ref` parameters")
    if "cross" not in body:
        warnings.append(f"{eid}: no cross coverage defined")

    return errors, warnings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kb", default=config.KB_JSON)
    ap.add_argument("--strict", action="store_true",
                    help="Exit non-zero if there are warnings as well as errors")
    args = ap.parse_args()

    path = Path(args.kb)
    if not path.exists():
        print(f"Knowledge base not found: {path}", file=sys.stderr)
        return 1

    data = json.loads(path.read_text(encoding="utf-8"))
    entries = data.get("entries", [])

    all_errors, all_warnings = [], []
    for e in entries:
        errs, warns = validate_entry(e)
        all_errors.extend(errs)
        all_warnings.extend(warns)

    print(f"Validated {len(entries)} entries in {path}\n")

    if all_errors:
        print(f"ERRORS ({len(all_errors)}) -- these would fail to compile:")
        for e in all_errors:
            print(f"  x {e}")
        print()
    if all_warnings:
        print(f"WARNINGS ({len(all_warnings)}):")
        for w in all_warnings:
            print(f"  ! {w}")
        print()

    if not all_errors and not all_warnings:
        print("All entries pass the structural checks.")
    elif not all_errors:
        print("No errors. Warnings above are stylistic.")

    print("\nNOTE: these are structural checks, not a compile. An entry that passes\n"
          "      still needs a real irun run before it is marked verified.")

    if all_errors:
        return 1
    if args.strict and all_warnings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
