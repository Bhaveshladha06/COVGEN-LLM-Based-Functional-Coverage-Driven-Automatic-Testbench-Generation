#!/usr/bin/env python3
"""
simulator.py -- runs Cadence irun to compile+elaborate+simulate the 5-file
set (rtl.v + if.sv + coverage.sv + tb.sv + top.sv) and produce a coverage
database that imc_runner.py then reports on.

NOTE ON THE irun COMMAND BELOW: -covscope/-covtest are inferred to line up
with imc_runner.py's hardcoded `load -run scope/test` (workDir=cov_work,
scopeDir=scope, run=test) -- that TCL syntax was validated against a real
IMC 15.20-s069 by this project's own imc_runner.py, but the exact irun flags
that produce that layout were NOT verified against a real server from this
session (no Cadence toolchain available here). Run once with a tiny design
and check `ls cov_work/` inside the run's sim_work dir actually contains
`scope/test/` before trusting the loop; adjust COV_SCOPE/COV_TEST in
config.py or the flags here if your irun names it differently.
"""

import logging
import os
import subprocess
from pathlib import Path
from typing import Tuple

import config

log = logging.getLogger("Simulator")


def run(design_file: str, if_file: str, cov_file: str, tb_file: str, top_file: str,
        run_dir: str, dut_module: str) -> Tuple[bool, str]:
    run_dir_abs = str(Path(run_dir).resolve())
    os.makedirs(run_dir_abs, exist_ok=True)

    if config.MOCK_SIMULATOR:
        return _mock_run(run_dir_abs)

    return _run_irun(design_file, if_file, cov_file, tb_file, top_file, run_dir_abs, dut_module)


def _run_irun(design_file: str, if_file: str, cov_file: str, tb_file: str, top_file: str,
             run_dir_abs: str, dut_module: str) -> Tuple[bool, str]:
    top_module = f"top_{dut_module}"  # matches prompt_builder._top_name() convention

    # irun runs with cwd=sim_work (so it drops cov_work/ there for imc_runner),
    # but the five source files are given relative to the project root. Resolve
    # them to absolute paths first or irun looks for them under sim_work and
    # fails with *E,FILEMIS.
    sources = [str(Path(f).resolve()) for f in
               (design_file, if_file, cov_file, tb_file, top_file)]

    missing = [f for f in sources if not os.path.exists(f)]
    if missing:
        msg = "Source files not found:\n" + "\n".join(f"  {f}" for f in missing)
        log.error(msg)
        return False, msg

    cmd = [
        config.IRUN_BIN,
        "-access", "+rwc",
        "-sv",
        "-timescale", config.TIMESCALE,
    ]
    cmd += list(config.COVERAGE_FLAGS)
    cmd += [
        "-covoverwrite",
        "-covtest", config.COV_TEST,
        "-covscope", config.COV_SCOPE,
    ]
    if config.COV_DUT_ONLY:
        # Restrict code coverage to the design under test; see COV_DUT_ONLY.
        cmd += ["-covdut", dut_module]
        if config.COV_DUT_INCLUDE_COVERAGE_MODULE:
            # ...and name the coverage module as a second DUT, or its
            # covergroups fall outside the coverage scope entirely and IMC
            # reports "Functional Average: n/a" -- code coverage only, with the
            # functional coverage this project measures silently absent.
            cmd += ["-covdut", f"{dut_module}_coverage"]
    if os.path.exists(config.COV_CONFIG_FILE):
        cmd += ["-covfile", str(Path(config.COV_CONFIG_FILE).resolve())]
    cmd += list(config.EXTRA_SIM_FLAGS)
    cmd += sources + ["-top", top_module]

    covdut_scopes = [cmd[i + 1] for i, a in enumerate(cmd) if a == "-covdut"]
    log.info(f"irun cmd: {' '.join(cmd)}")
    log.info(f"irun cwd: {run_dir_abs}")
    log.info(f"coverage scope (-covdut): {covdut_scopes or ['<whole design>']}")

    try:
        result = subprocess.run(
            cmd, cwd=run_dir_abs, capture_output=True, text=True,
            timeout=config.SIM_TIMEOUT_SEC,
        )
    except FileNotFoundError:
        msg = f"irun not found at '{config.IRUN_BIN}'. Set IRUN_BIN in config.py or the environment."
        log.error(msg)
        return False, msg
    except subprocess.TimeoutExpired:
        msg = f"irun timed out after {config.SIM_TIMEOUT_SEC}s"
        log.error(msg)
        return False, msg

    out = result.stdout + "\n" + result.stderr
    cov_db_present = os.path.exists(os.path.join(run_dir_abs, config.COV_DB_DIR))
    ok = result.returncode == 0 and cov_db_present

    if result.returncode != 0:
        log.warning(f"irun exited with code {result.returncode}")
    if result.returncode == 0 and not cov_db_present:
        log.warning(f"irun exited 0 but no {config.COV_DB_DIR}/ was produced -- "
                    f"coverage flags likely need adjustment (see module docstring)")

    return ok, out


def _mock_run(run_dir_abs: str) -> Tuple[bool, str]:
    cov_db = os.path.join(run_dir_abs, config.COV_DB_DIR, config.COV_SCOPE, config.COV_TEST)
    os.makedirs(cov_db, exist_ok=True)
    log.info(f"[MOCK] simulator: wrote fake coverage DB at {cov_db}")
    return True, "MOCK irun run: 0 errors, 0 warnings\nTEST PASSED\n"
