#!/usr/bin/env python3
"""
mutate.py -- measure whether a generated coverage model is any GOOD, not just
whether it is full.

THE PROBLEM THIS EXISTS FOR
    The LLM writes the coverage model, and then the LLM writes stimulus to fill
    it. The same model sets the exam and sits it. 100% functional coverage
    therefore proves only that the testbench satisfied the covergroup -- it says
    nothing about whether the covergroup was worth satisfying. A covergroup with
    two lazy bins reaches 100% and catches nothing.

    Nothing in the pipeline measures covergroup QUALITY. This does.

HOW
    Inject a small bug into the RTL -- swap + for -, <= for <, a constant for a
    neighbouring one -- and re-run the SAME coverage model and the SAME final
    testbench against the broken design.

    If the coverage numbers come out identical, the covergroup could not tell a
    correct design from a broken one. That is a blind spot, and it is invisible
    to any amount of coverage-percentage reporting.

    A good coverage model shows a different score, or fails to fill some bin,
    when the design misbehaves.

USAGE
    python mutate.py --design designs/fifo/fifo.v
    python mutate.py --design designs/fifo/fifo.v --run runs/run_20260823_120000
    python mutate.py --design designs/fifo/fifo.v --max_mutants 6

    Uses the most recent run for that design unless --run says otherwise.
    Needs a completed run: the golden files and FINAL testbench come from it.
    Costs no API calls.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import config


# ---------------------------------------------------------------------------
# Mutation operators
# ---------------------------------------------------------------------------

@dataclass
class Mutation:
    line_no: int
    original: str
    mutated: str
    description: str


# (pattern, replacement, human description). Applied one at a time, and only
# outside comments. Kept deliberately small and syntax-preserving -- the goal is
# a design that still compiles but behaves differently, not a parse error.
_OPERATORS: List[Tuple[str, str, str]] = [
    (r'(?<![+<>=!])\+(?!\+)', '-',  'addition -> subtraction'),
    (r'(?<![-<>=!])\-(?!\-)', '+',  'subtraction -> addition'),
    (r'&&',                   '||', 'AND -> OR'),
    (r'\|\|',                 '&&', 'OR -> AND'),
    (r'<=(?!\s*\{)(?![^;]*<=)', '<', 'less-or-equal -> less-than'),
    (r'>=',                   '>',  'greater-or-equal -> greater-than'),
    (r'==',                   '!=', 'equality -> inequality'),
    (r'!=',                   '==', 'inequality -> equality'),
]

_ASSIGN_RE = re.compile(r'<=')


def _strip_comment(line: str) -> str:
    return line.split('//')[0]


def find_mutations(rtl: str, limit: int) -> List[Mutation]:
    """One mutation per site, spread across the file rather than clustered at
    the top, so a small --max_mutants still probes different behaviours."""
    lines = rtl.splitlines()
    found: List[Mutation] = []

    for i, line in enumerate(lines):
        code = _strip_comment(line)
        if not code.strip() or code.strip().startswith(('module', 'input', 'output',
                                                        'endmodule', 'reg', 'wire')):
            continue
        for pattern, repl, desc in _OPERATORS:
            # A non-blocking assignment `<=` is not a comparison; never touch it.
            if pattern.startswith('<=') and _ASSIGN_RE.search(code):
                after = code.split('<=', 1)[1]
                if not re.match(r'\s*[\w\'{(]', after):
                    continue
                if re.search(r'(if|while|else if)\s*\([^)]*<=', code) is None:
                    continue
            m = re.search(pattern, code)
            if not m:
                continue
            mutated_line = line[:m.start()] + repl + line[m.end():]
            found.append(Mutation(i, line.rstrip(), mutated_line.rstrip(), desc))
            break                      # one mutation per line

    if len(found) <= limit:
        return found
    # Spread the sample evenly through the file.
    step = len(found) / limit
    return [found[int(k * step)] for k in range(limit)]


def apply_mutation(rtl: str, mut: Mutation) -> str:
    lines = rtl.splitlines()
    lines[mut.line_no] = mut.mutated
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Running one mutant
# ---------------------------------------------------------------------------

_SCORE_RE = re.compile(r'SV_FUNCTIONAL_COVERAGE:\s*([\d.]+)')
_CP_RE    = re.compile(r'SV_CP\s+(\w+)\s*:\s*([\d.]+)')


def run_once(rtl_path: Path, files: List[Path], top: str, work: Path) -> Tuple[Optional[float], str]:
    """Simulate one version of the design; return its functional coverage."""
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)

    cmd = [config.IRUN_BIN, "-access", "+rwc", "-sv",
           "-timescale", config.TIMESCALE]
    cmd += list(config.COVERAGE_FLAGS)
    cmd += ["-covoverwrite", "-covtest", config.COV_TEST, "-covscope", config.COV_SCOPE]
    cmd += [str(rtl_path.resolve())] + [str(f.resolve()) for f in files]
    cmd += ["-top", top]

    try:
        r = subprocess.run(cmd, cwd=str(work), capture_output=True, text=True,
                           timeout=config.SIM_TIMEOUT_SEC)
    except subprocess.TimeoutExpired:
        return None, "TIMEOUT"

    out = r.stdout + r.stderr
    (work / "sim.log").write_text(out, encoding="utf-8")

    m = _SCORE_RE.search(out)
    if not m:
        errs = [l for l in out.splitlines() if "*E," in l or "*F," in l]
        return None, (errs[0][:90] if errs else "no coverage line printed")
    return float(m.group(1)), ""


def find_run_dir(design_name: str, explicit: str) -> Path:
    if explicit:
        p = Path(explicit)
        if not p.exists():
            sys.exit(f"No such run directory: {p}")
        return p
    runs = sorted(Path(config.OUTPUT_BASE_DIR).glob("run_*"), reverse=True)
    for r in runs:
        if (r / f"FINAL_tb_{design_name}.sv").exists():
            return r
    sys.exit(f"No completed run found for '{design_name}'. Run main.py first.")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Inject bugs into the RTL and see whether the generated "
                    "coverage model notices.")
    ap.add_argument("--design", required=True, help="path to the RTL file")
    ap.add_argument("--run", default="", help="run directory (default: most recent)")
    ap.add_argument("--max_mutants", type=int, default=8)
    ap.add_argument("--keep", action="store_true", help="keep each mutant's work dir")
    args = ap.parse_args()

    rtl_path = Path(args.design)
    if not rtl_path.exists():
        sys.exit(f"No such file: {rtl_path}")
    name = re.search(r'\bmodule\s+(\w+)', rtl_path.read_text(encoding="utf-8")).group(1)

    run_dir = find_run_dir(name, args.run)
    files = [run_dir / f"{name}_if.sv",
             run_dir / f"{name}_coverage.sv",
             run_dir / f"FINAL_tb_{name}.sv",
             run_dir / f"top_{name}.sv"]
    missing = [f for f in files if not f.exists()]
    if missing:
        sys.exit("Run directory is incomplete:\n" + "\n".join(f"  {f}" for f in missing))

    print(f"design      : {name}")
    print(f"using run   : {run_dir}")
    print(f"testbench   : FINAL_tb_{name}.sv  (unchanged for every mutant)")
    print(f"coverage    : {name}_coverage.sv  (unchanged for every mutant)")
    print()

    base_dir = Path("mutation_work") / name
    base_dir.mkdir(parents=True, exist_ok=True)

    baseline, err = run_once(rtl_path, files, f"top_{name}", base_dir / "baseline")
    if baseline is None:
        sys.exit(f"Baseline run failed ({err}). Fix that before mutating.")
    print(f"BASELINE (correct design): {baseline:.2f}% functional coverage")
    print()

    rtl = rtl_path.read_text(encoding="utf-8")
    muts = find_mutations(rtl, args.max_mutants)
    if not muts:
        sys.exit("No mutation sites found in this RTL.")

    print(f"{'#':>3}  {'line':>5}  {'mutation':<26} {'coverage':>9}  verdict")
    print("-" * 78)

    blind = caught = broke = 0
    for i, mut in enumerate(muts, 1):
        work = base_dir / f"mutant_{i:02d}"
        mrtl = work.parent / f"mutant_{i:02d}.v"
        work.mkdir(parents=True, exist_ok=True)
        mrtl.write_text(apply_mutation(rtl, mut), encoding="utf-8")

        score, err = run_once(mrtl, files, f"top_{name}", work)

        if score is None:
            verdict, note = "did not run", err
            broke += 1
            shown = "   --   "
        elif abs(score - baseline) < 0.005:
            verdict, note = "BLIND -- identical score", ""
            blind += 1
            shown = f"{score:8.2f}%"
        else:
            verdict, note = f"caught ({score - baseline:+.2f}%)", ""
            caught += 1
            shown = f"{score:8.2f}%"

        print(f"{i:>3}  {mut.line_no + 1:>5}  {mut.description:<26} {shown}  {verdict}")
        if note:
            print(f"                                              {note}")
        if not args.keep:
            shutil.rmtree(work, ignore_errors=True)

    total = blind + caught
    print("-" * 78)
    print(f"caught {caught} / {total} injected bugs" + (f"   ({broke} did not compile, ignored)" if broke else ""))
    print()

    if total == 0:
        print("No usable mutants. Try --max_mutants with a larger number.")
    elif blind == 0:
        print("Every injected bug changed the coverage numbers. The covergroup")
        print("distinguishes a correct design from a broken one on all of them.")
    else:
        pct = 100 * blind / total
        print(f"{blind} of {total} bugs ({pct:.0f}%) produced IDENTICAL coverage.")
        print()
        print("For those, the covergroup cannot tell the correct design from the")
        print("broken one. The 100% it reports is 100% of the wrong question.")
        print()
        print("This is the number worth reporting alongside coverage, and the one")
        print("worth improving: add bins that separate the behaviours above.")

    print(f"\nLogs: {base_dir}/")


if __name__ == "__main__":
    main()
