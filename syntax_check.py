#!/usr/bin/env python3
"""
syntax_check.py -- compile SystemVerilog files with irun, syntax only.

Used by main.py to validate each golden file the moment it is generated,
instead of discovering the breakage later during a full simulation. A compile
costs a few seconds and no Gemini credits; a wasted iteration costs a
testbench generation, a full elaboration, and an IMC run.
"""

import logging
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import List, Tuple

import config

log = logging.getLogger("SyntaxCheck")

_ERR_RE = re.compile(r'\*[EF],')


def check(files: List[str], work_dir: str = None,
          timeout: int = 120, top: str = None) -> Tuple[bool, str]:
    """Check `files` with irun. Returns (ok, error_text).

    Without `top`, uses -compile: irun stops after compilation, which is all
    that can be checked for a file in isolation.

    With `top`, uses -elaborate -top <top>, which additionally catches the
    whole class of errors that only appear when modules are wired together --
    port name and width mismatches, multiple drivers, and unsupported
    constructs such as hierarchical virtual-interface assignment (*E,VIFCVU).
    Those are invisible to -compile and would otherwise only surface during a
    full simulation run, after a testbench had already been generated.
    """
    if config.MOCK_SIMULATOR:
        return True, ""

    abs_files = [str(Path(f).resolve()) for f in files]
    missing = [f for f in abs_files if not os.path.exists(f)]
    if missing:
        return False, "File(s) not found:\n" + "\n".join(missing)

    wd = work_dir or tempfile.mkdtemp(prefix="syntax_check_")
    Path(wd).mkdir(parents=True, exist_ok=True)

    mode = ["-elaborate", "-top", top] if top else ["-compile"]
    # These must match simulator.run()'s flags. Without -timescale, a design
    # whose RTL carries no `timescale directive fails elaboration with
    # *F,CUMSTS here while succeeding in the real run -- a phantom failure
    # that costs repair attempts and fixes nothing.
    cmd = ([config.IRUN_BIN, "-sv", "-nocopyright",
            "-timescale", config.TIMESCALE]
           + list(config.EXTRA_SIM_FLAGS) + mode + abs_files)
    try:
        r = subprocess.run(cmd, cwd=wd, capture_output=True, text=True,
                           timeout=timeout)
    except FileNotFoundError:
        return False, f"irun not found at '{config.IRUN_BIN}'"
    except subprocess.TimeoutExpired:
        return False, f"irun timed out after {timeout}s"

    out = r.stdout + "\n" + r.stderr
    errors = [l for l in out.splitlines() if _ERR_RE.search(l)]

    # A missing top module is expected when compiling files in isolation.
    errors = [l for l in errors if "NOTOPL" not in l]

    return (not errors), "\n".join(errors[:12])


def stub_testbench(design_name: str, port_decl: str, path: str) -> str:
    """Write a minimal testbench so the top module can be compiled during
    phase 1, before a real testbench exists. Its port list must match what the
    top module connects to, so it is generated from the same helper the real
    testbench prompt uses."""
    src = f"""`timescale 1ns/1ps
// Placeholder used only for compiling {design_name}'s top module during
// generation. Replaced by the real testbench every iteration.
module tb_{design_name} (
{port_decl}
);
endmodule
"""
    Path(path).write_text(src, encoding="utf-8")
    return src
