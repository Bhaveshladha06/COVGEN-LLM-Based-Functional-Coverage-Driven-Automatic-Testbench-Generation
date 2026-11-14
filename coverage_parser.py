#!/usr/bin/env python3
"""
coverage_parser.py -- parse IMC summary/detail reports into structured data
for main.py's iteration loop and prompt_builder's refinement prompts.

TWO SUMMARY LAYOUTS ARE SUPPORTED.

1. The real IMC 15.20 per-DUT table produced by `report -summary`:

    name      Overall Average  Overall Covered   Code Average  Code Covered     Fsm Average  Fsm Covered  Functional Average  Functional Covered
    -------------------------------------------------------------------------------------------------------------------------------------------
    counter   100.00%          100.00% (12/12)   100.00%       100.00% (12/12)  n/a          n/a          n/a                 n/a

   Note the `n/a` in the Functional columns. That is NOT 100% and it is not a
   rounding detail: it means no covergroup was found inside the coverage scope,
   so the functional coverage this whole project exists to measure was not
   measured at all. The old parser fell back to "last percentage in the text"
   and read that row as 100.00% overall, so a run with zero functional coverage
   was reported as a complete success. parse_summary() now records functional
   coverage as *unavailable* in that case and main.py refuses to call it a pass.

2. The simple per-metric table used by imc_runner's mock:

    Coverage Type      Covered   Total   Percentage
    Block                    12      17       70.59%
    Overall                   -       -       67.20%
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class CoverageBreakdown:
    overall: float
    categories: Dict[str, float] = field(default_factory=dict)
    # Functional (covergroup) coverage. None means IMC reported it as "n/a" or
    # the report contained no functional column at all -- i.e. not measured.
    functional: Optional[float] = None
    # Code (block/expression/toggle) coverage, when the report separates it.
    code: Optional[float] = None
    # Per-DUT rows recognised in the layout-1 table, for diagnostics.
    rows: List[str] = field(default_factory=list)

    @property
    def functional_measured(self) -> bool:
        return self.functional is not None

    def headline(self) -> float:
        """The number the refinement loop should optimise.

        Functional coverage is the goal of this project, so it wins whenever it
        was actually measured. Code coverage is only a stand-in used to keep the
        loop moving when the functional metric is missing -- and main.py warns
        loudly and refuses to declare success in that case.
        """
        return self.functional if self.functional is not None else self.overall


_PCT_RE = re.compile(r'([\d.]+)\s*%')


def _cell_pct(cell: str) -> Optional[float]:
    """Percentage in an IMC table cell, or None for 'n/a' / '-' / unparsable."""
    cell = cell.strip()
    if not cell or cell.lower() in ("n/a", "na", "-", "--"):
        return None
    m = _PCT_RE.search(cell)
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:
        return None


def _split_cells(line: str) -> List[str]:
    """IMC pads columns with 2+ spaces; values like '100.00% (12/12)' contain a
    single space, so splitting on runs of 2+ spaces keeps each cell intact."""
    return [c for c in re.split(r'\s{2,}', line.strip()) if c]


def _parse_dut_table(text: str) -> Optional[CoverageBreakdown]:
    """Layout 1: the real IMC per-DUT summary table. Returns None if absent."""
    lines = text.splitlines()

    header_idx = None
    header_cells: List[str] = []
    for i, line in enumerate(lines):
        cells = _split_cells(line)
        if not cells:
            continue
        if cells[0].strip().lower() == "name" and any("overall" in c.lower() for c in cells):
            header_idx = i
            header_cells = cells
            break
    if header_idx is None:
        return None

    def col(*keywords) -> Optional[int]:
        for j, c in enumerate(header_cells):
            lc = c.lower()
            if all(k in lc for k in keywords):
                return j
        return None

    i_overall = col("overall", "average")
    i_code    = col("code", "average")
    i_func    = col("functional", "average")

    overalls, codes, funcs, names = [], [], [], []

    for line in lines[header_idx + 1:]:
        stripped = line.strip()
        if not stripped or set(stripped) <= {"-", "="}:
            continue
        cells = _split_cells(line)
        if len(cells) < 2:
            continue
        # A data row starts with a scope name, not another header.
        if cells[0].strip().lower() == "name":
            continue
        names.append(cells[0].strip())

        def at(idx):
            return _cell_pct(cells[idx]) if idx is not None and idx < len(cells) else None

        for value, bucket in ((at(i_overall), overalls),
                              (at(i_code), codes),
                              (at(i_func), funcs)):
            if value is not None:
                bucket.append(value)

    if not names:
        return None

    def mean(values):
        return sum(values) / len(values) if values else None

    functional = mean(funcs)
    code       = mean(codes)
    # With -covdut naming both the DUT and its coverage module, IMC emits one
    # row per scope: code numbers on the DUT row, functional numbers on the
    # coverage-module row. Averaging each column across rows recombines them.
    overall    = mean(overalls)

    categories: Dict[str, float] = {}
    if code is not None:
        categories["Code"] = code
    if functional is not None:
        categories["Functional"] = functional
    if overall is not None:
        categories["Overall"] = overall

    return CoverageBreakdown(
        overall=overall if overall is not None else (code or 0.0),
        categories=categories,
        functional=functional,
        code=code,
        rows=names,
    )


# Layout 2: "<Category>  <covered>  <total>  <pct>%"
_ROW_RE = re.compile(r'^([A-Za-z][A-Za-z \-]*?)\s{2,}.*?([\d.]+)\s*%\s*$')


def _parse_metric_table(summary_text: str) -> CoverageBreakdown:
    categories: Dict[str, float] = {}

    for line in summary_text.splitlines():
        stripped = line.strip()
        if not stripped or set(stripped) <= {"-"}:
            continue
        if stripped.lower().startswith("coverage type"):
            continue

        m = _ROW_RE.match(line.rstrip())
        if not m:
            continue
        name = m.group(1).strip()
        try:
            categories[name] = float(m.group(2))
        except ValueError:
            continue

    overall = categories.get("Overall")
    if overall is None:
        all_pcts = _PCT_RE.findall(summary_text)
        overall = float(all_pcts[-1]) if all_pcts else 0.0

    functional = None
    for key in ("Functional", "Covergroup", "Assertion"):
        if key in categories:
            functional = categories[key]
            break

    code = None
    code_keys = [k for k in ("Block", "Expression", "Toggle", "Branch", "Statement")
                 if k in categories]
    if code_keys:
        code = sum(categories[k] for k in code_keys) / len(code_keys)

    return CoverageBreakdown(overall=overall, categories=categories,
                             functional=functional, code=code)


def parse_summary(summary_text: str) -> CoverageBreakdown:
    """Extract per-category, functional and overall coverage percentages.

    Tries the real IMC per-DUT table first, then the simple per-metric table.
    A functional column of `n/a` yields functional=None -- deliberately not 0.0
    and never 100.0 -- so callers can tell "no covergroups were scored" apart
    from "covergroups were scored and hit nothing".
    """
    if not summary_text or not summary_text.strip():
        return CoverageBreakdown(overall=0.0)

    dut = _parse_dut_table(summary_text)
    if dut is not None:
        return dut
    return _parse_metric_table(summary_text)


# ---------------------------------------------------------------------------
# Functional (covergroup) report -- the fallback when the summary says n/a
# ---------------------------------------------------------------------------

_CG_LINE_RE = re.compile(
    r'^\s*(?P<name>[A-Za-z_][\w:.\[\]$]*)\s+.*?(?P<pct>[\d.]+)\s*%')


def parse_functional_report(text: str) -> Optional[float]:
    """Scrape an average covergroup percentage out of IMC's covergroup report.

    imc_runner asks IMC for a covergroup-scoped report separately, because the
    per-DUT summary is scoped by irun's -covdut and hides covergroups declared
    outside the DUT module. The exact layout differs between IMC builds, so this
    is deliberately loose: take every "<something> ... NN%" line that is not a
    banner and average the percentages. Returns None when nothing looks like a
    covergroup row, which callers must treat as "not measured".
    """
    if not text or not text.strip():
        return None

    pcts: List[float] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or set(stripped) <= {"-", "="}:
            continue
        low = stripped.lower()
        if low.startswith(("name", "total", "coverage type", "report", "loading",
                           "cumulative", "summary")):
            continue
        m = _CG_LINE_RE.match(line)
        if not m:
            continue
        try:
            pcts.append(float(m.group("pct")))
        except ValueError:
            continue

    if not pcts:
        return None
    return sum(pcts) / len(pcts)


# ---------------------------------------------------------------------------
# Functional coverage straight from the simulator
# ---------------------------------------------------------------------------

_SV_COV_RE   = re.compile(r'^\s*SV_FUNCTIONAL_COVERAGE:\s*([\d.]+)', re.M)
_SV_INST_RE  = re.compile(r'^\s*SV_CG_INST_COVERAGE:\s*([\d.]+)', re.M)


def parse_sv_functional(sim_output: str) -> Optional[float]:
    """Read the covergroup score printed by the coverage module's `final` block.

    This is the most reliable functional coverage number available, because it
    comes from the simulator's own covergroup engine at end of simulation rather
    than from the coverage database. IMC reported `Functional: n/a` even with the
    coverage module inside the -covdut scope and even with a covergroup that
    demonstrably compiled and sampled, so the database route cannot be trusted on
    its own on this tool version.

    `$get_coverage()` is the total across every covergroup type in the design;
    the per-instance figure is used only as a fallback. Returns None when neither
    line is present -- meaning the coverage model predates this convention (its
    cached copy needs regenerating with --regen_cov) or the simulation died
    before its `final` block ran.
    """
    if not sim_output:
        return None
    for regex in (_SV_COV_RE, _SV_INST_RE):
        matches = regex.findall(sim_output)
        if matches:
            try:
                # Last occurrence: one print per simulation, but be safe.
                return float(matches[-1])
            except ValueError:
                continue
    return None


NO_DETAIL_AVAILABLE = (
    "(IMC produced no per-bin detail -- see HANDOFF.md: covergroup data does not "
    "reach the coverage database on this tool version, so the exact empty bins "
    "cannot be listed. Reason from the coverage model instead.)")

NO_DUT_HOLES = (
    "(no uncovered items in the DUT -- every remaining uncovered item "
    "belongs to the testbench or harness and is not a design coverage hole)")


def detail_is_useless(detail_text: str) -> bool:
    """True when the detail report names no actual coverage hole, so the
    refinement prompt must fall back to reasoning from the coverage model."""
    return (not detail_text
            or detail_text.startswith(NO_DETAIL_AVAILABLE[:40])
            or detail_text.startswith(NO_DUT_HOLES[:40]))


_TYPE_RE = re.compile(r'^Type name:\s*(\S+)', re.M)


def filter_detail_to_dut(detail_text: str, dut_module: str) -> str:
    """Keep only the uncovered items belonging to the DUT.

    IMC's detail report is organised into per-instance sections, each headed by
    "Instance name:" / "Type name:". Without this filter the report also lists
    the testbench's own unreachable code -- watchdog timeouts, "value never
    reached" else-branches, loop bound guards -- and those items then flow into
    the refinement prompt, where the model dutifully writes stimulus trying to
    make the testbench's error handlers execute. That is wasted effort at best
    and actively counterproductive at worst.

    The <dut>_coverage module is kept as well: it is now inside the coverage
    scope (see simulator.py's -covdut handling) and an uncovered covergroup bin
    reported there IS a real coverage hole worth feeding back to the model.
    """
    if not detail_text:
        return detail_text

    if "Type name:" not in detail_text:
        # An IMC detail report with no "Type name:" anywhere has no per-item
        # entries at all -- every "Uncovered ... Detail Report" section came
        # back empty. Returning the text unchanged then fed IMC's own banner
        # (username, hostname, file paths, the table legend) into the
        # refinement prompt under the heading "UNCOVERED ITEMS", which is
        # worse than sending nothing: the model was handed noise and asked to
        # write stimulus for it.
        if "Detail Report" in detail_text or "Coverage Table Legend" in detail_text:
            return NO_DETAIL_AVAILABLE
        return detail_text          # unrecognised format -- pass through

    wanted = {dut_module, f"{dut_module}_coverage"}

    kept = []
    for part in re.split(r'(?m)^(?=Instance name:)', detail_text):
        m = _TYPE_RE.search(part)
        if m is None:
            continue                      # preamble and section banners
        if m.group(1) in wanted:
            kept.append(part.rstrip())

    if not kept:
        return NO_DUT_HOLES
    return "\n\n".join(kept)


def trim_detail_for_prompt(detail_text: str, max_chars: int = 2000) -> str:
    """Dedupe and truncate the uncovered-items detail report so refinement
    prompts stay within a sane token budget instead of dumping a full IMC
    detail log at Gemini every iteration."""
    if not detail_text or not detail_text.strip():
        return "(no detail report available)"

    seen = set()
    deduped = []
    for line in detail_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped in seen:
            continue
        seen.add(stripped)
        deduped.append(stripped)

    out_lines = []
    total = 0
    for i, line in enumerate(deduped):
        if total + len(line) + 1 > max_chars:
            remaining = len(deduped) - i
            if remaining > 0:
                out_lines.append(f"... and {remaining} more uncovered item(s) (truncated)")
            break
        out_lines.append(line)
        total += len(line) + 1

    return "\n".join(out_lines) if out_lines else "(no distinct uncovered items found)"
