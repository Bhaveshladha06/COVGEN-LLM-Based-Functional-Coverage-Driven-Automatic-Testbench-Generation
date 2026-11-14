# imc_runner.py -- IMC batch report generator
# Tested against IMC 15.20-s069
#
# KEY DISCOVERY:
# IMC load -run syntax: workDir/scopeDir/run
#   workDir  = cov_work  (default, no need to specify)
#   scopeDir = scope
#   run      = test
# So correct command: load -run scope/test
# cwd MUST be sim_work when imc runs (so cov_work is found as relative path)

import logging
import os
import subprocess
from pathlib import Path
from typing import Tuple

import config

log = logging.getLogger("IMC")


def generate_reports(run_dir: str, dut_module: str) -> Tuple[str, str, str]:
    """Returns (summary_text, detail_text, functional_text).

    functional_text is a covergroup-scoped report requested separately from the
    per-DUT summary; see _IMC_TCL. It may be empty if no IMC report command in
    the ladder succeeded -- callers must treat empty as "not measured", never
    as zero or as success.
    """
    cov_db = os.path.join(run_dir, config.COV_DB_DIR)

    if config.MOCK_SIMULATOR:
        summary, detail = _mock_reports(cov_db, dut_module)
        return summary, detail, ""

    if not os.path.exists(cov_db):
        msg = (
            f"Coverage database not found: {cov_db}\n"
            "ncverilog may have failed -- check sim_output.txt"
        )
        log.error(msg)
        return "COVERAGE DB NOT FOUND", msg, ""

    return _run_imc(run_dir, cov_db, dut_module)


# IMC 15.20 TCL script
# load -run scope/test  means:  cov_work(default)/scope/test
# cwd is set to sim_work so cov_work is found automatically
_IMC_TCL = """\
# Auto-generated IMC TCL script for IMC 15.20
# workDir=cov_work (default), scopeDir=scope, run=test

if {{[catch {{load -run scope/test}} err]}} {{
    puts "ERROR: $err"
    exit 1
}}

puts "DB loaded OK"

report -summary -out {summary_rpt}
report -summary

report -detail -uncovered -out {detail_rpt}

# ---------------------------------------------------------------------------
# Functional (covergroup) coverage, requested separately.
#
# `report -summary` is scoped by irun's -covdut, so a covergroup that sits
# outside the DUT module shows up there as "Functional Average: n/a" -- which
# reads like a formatting quirk but actually means the covergroups were never
# scored. simulator.py now names the coverage module as a second DUT, but this
# report is kept as an independent check: if the summary still says n/a, this
# file tells us whether the covergroups exist in the database at all.
#
# IMC option spellings differ across 15.x builds and no Cadence install was
# available while writing this, so try the known forms and keep the first that
# succeeds. imc.log records which one worked -- once you know, delete the rest.
# ---------------------------------------------------------------------------
set fc_written 0
foreach fc_cmd [list \
        {{report -summary -metrics functional -out {func_rpt}}} \
        {{report -summary -metrics covergroup -out {func_rpt}}} \
        {{report -detail -metrics functional -out {func_rpt}}} \
        {{report -detail -metrics covergroup -out {func_rpt}}} \
        {{report -detail -all -out {func_rpt}}} ] {{
    puts "FUNCTIONAL-REPORT TRY: $fc_cmd"
    if {{[catch {{eval $fc_cmd}} e]}} {{
        puts "  failed: $e"
    }} else {{
        puts "  OK -- functional report written by: $fc_cmd"
        set fc_written 1
        break
    }}
}}
if {{$fc_written == 0}} {{
    puts "WARNING: no covergroup report command was accepted by this IMC build"
}}

puts "Reports done."
exit
"""


def _run_imc(run_dir: str, cov_db: str, dut_module: str) -> Tuple[str, str, str]:
    # Use absolute paths for report output files
    run_dir_abs = str(Path(run_dir).resolve())

    summary_rpt = os.path.join(run_dir_abs, "coverage_summary.rpt")
    detail_rpt  = os.path.join(run_dir_abs, config.IMC_DETAIL_REPORT)
    func_rpt    = os.path.join(run_dir_abs, config.IMC_FUNCTIONAL_REPORT)
    tcl_path    = os.path.join(run_dir_abs, config.IMC_TCL_SCRIPT)
    imc_log     = os.path.join(run_dir_abs, config.IMC_LOG)

    for stale in (summary_rpt, detail_rpt, func_rpt):
        # Reports are read back below; a leftover file from the previous
        # iteration would otherwise be mistaken for this iteration's result.
        if os.path.exists(stale):
            os.remove(stale)

    tcl_content = _IMC_TCL.format(
        summary_rpt = summary_rpt,
        detail_rpt  = detail_rpt,
        func_rpt    = func_rpt,
    )

    with open(tcl_path, "w", encoding="utf-8") as f:
        f.write(tcl_content)

    cmd = [
        config.IMC_BIN,
        "-exec",    tcl_path,
        "-logfile", imc_log,
    ]

    log.info(f"IMC cmd: {' '.join(cmd)}")
    log.info(f"IMC cwd: {run_dir_abs}  (so cov_work/scope/test is found)")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=config.IMC_TIMEOUT_SEC,
            cwd=run_dir_abs,   # CRITICAL: run from sim_work so load -run scope/test works
        )
    except FileNotFoundError:
        msg = f"IMC not found at '{config.IMC_BIN}'. Set IMC_BIN in config.py."
        log.error(msg)
        return "IMC NOT FOUND", msg, ""
    except subprocess.TimeoutExpired:
        msg = f"IMC timed out after {config.IMC_TIMEOUT_SEC}s"
        log.error(msg)
        return "IMC TIMEOUT", msg, ""

    imc_stdout = result.stdout + "\n" + result.stderr

    if result.returncode != 0:
        log.warning(f"IMC exited with code {result.returncode}")
        log.warning(f"IMC output:\n{imc_stdout[:800]}")

    summary_text = _read_file(summary_rpt, "summary report")
    detail_text  = _read_file(detail_rpt,  "detail report")
    func_text    = _read_file(func_rpt,    "functional report", warn_missing=False)

    if not summary_text.strip():
        log.warning("Summary file empty -- using IMC stdout")
        summary_text = imc_stdout
    if not detail_text.strip():
        log.warning("Detail file empty -- using IMC stdout")
        detail_text = imc_stdout
    if not func_text.strip():
        log.warning(
            "No covergroup report was produced. Either this IMC build accepts "
            "none of the report forms tried (see FUNCTIONAL-REPORT TRY lines in "
            f"{config.IMC_LOG}) or the database holds no covergroups at all."
        )

    log.info(
        f"IMC reports: summary={len(summary_text)} chars  "
        f"detail={len(detail_text)} chars  functional={len(func_text)} chars"
    )
    return summary_text, detail_text, func_text


def _read_file(path: str, label: str, warn_missing: bool = True) -> str:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    if warn_missing:
        log.warning(f"IMC {label} not found: {path}")
    return ""


# ---------------------------------------------------------------------------
# Mock IMC
# ---------------------------------------------------------------------------

_mock_imc_iter = 0

def _mock_reports(cov_db: str, dut_module: str) -> Tuple[str, str]:
    global _mock_imc_iter
    _mock_imc_iter += 1

    cov = 45.0 + (_mock_imc_iter - 1) * 14.0
    mock_file = os.path.join(cov_db, "mock.ucis")
    if os.path.exists(mock_file):
        with open(mock_file, encoding="utf-8") as f:
            for line in f:
                if line.startswith("MOCK_COVERAGE="):
                    cov = float(line.split("=")[1])

    cov        = min(cov, 100.0)
    block_cov  = min(cov + 5,  100.0)
    toggle_cov = max(cov - 5,  0.0)

    summary = f"""\
Coverage Type      Covered   Total   Percentage
-----------------  --------  ------  ----------
Block              {int(block_cov/100*17):>8}  {17:>6}  {block_cov:>9.2f}%
Expression         {int(block_cov/100*12):>8}  {12:>6}  {block_cov:>9.2f}%
Toggle             {int(toggle_cov/100*31):>8}  {31:>6}  {toggle_cov:>9.2f}%
Functional         {int(cov/100*20):>8}  {20:>6}  {cov:>9.2f}%
Overall            -         -       {cov:>9.2f}%
"""
    items = [
        "Line 22 [BRANCH-FALSE] wr_en && full never simultaneously true",
        "Line 31 [BRANCH-FALSE] rd_en && empty never simultaneously true",
        "Toggle: din[7] 0->1 never driven",
    ]
    shown = items[:max(0, 3 - _mock_imc_iter + 1)]
    detail = "Uncovered items:\n" + ("\n".join(shown) if shown else "All covered!")

    log.info(f"[MOCK] IMC coverage={cov:.2f}%")
    return summary, detail
