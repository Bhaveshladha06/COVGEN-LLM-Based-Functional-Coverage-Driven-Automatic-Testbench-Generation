#!/usr/bin/env python3
"""
main.py -- Coverage-Driven SV Verification Framework
4-file architecture per design:
  {name}_if.sv        -- interface with modports         [GOLDEN]
  {name}_coverage.sv  -- self-sampling coverage module    [GOLDEN]
  top_{name}.sv       -- top wiring module               [GOLDEN]
  tb_{name}.sv        -- procedural stimulus testbench    [iterates]

irun compiles all 5: rtl.v + if.sv + coverage.sv + tb.sv + top.sv
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

import config
import coverage_parser
import imc_runner
import simulator
import syntax_check
from gemini_client import GeminiClient
from prompt_builder import (
    DesignInfo,
    parse_design,
    build_interface_code,
    build_coverage_model_prompt,
    ensure_per_instance,
    build_top_code,
    build_random_tb_prompt,
    build_constrained_tb_prompt,
    build_directed_tb_prompt,
    build_repair_prompt,
    _if_name, _cov_name, _tb_name, _top_name, _tb_port_decl,
)


def setup_logging(run_dir: Path) -> logging.Logger:
    fmt = "%(asctime)s [%(levelname)-8s] %(name)-16s: %(message)s"
    handlers = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(str(run_dir / "run.log"), encoding="utf-8"),
    ]
    logging.basicConfig(level=getattr(logging, config.LOG_LEVEL, logging.INFO),
                        format=fmt, handlers=handlers)
    return logging.getLogger("Main")


SEP = "=" * 64
def banner(msg): print(f"\n{SEP}\n  {msg}\n{SEP}")
def tick(msg):   print(f"  [OK]  {msg}")
def warn(msg):   print(f"  [WARN]   {msg}")
def info(msg):   print(f"  [INFO]   {msg}")
def cross(msg):  print(f"  [FAIL]  {msg}")
def save(path: Path, text: str): path.write_text(text, encoding="utf-8")


def _fix_clock_refs(code: str, clock: str) -> str:
    """No-op, kept so the call site stays stable.

    This used to rewrite bare `posedge clk` into `posedge intf.clk` for a
    testbench that held a virtual interface. The testbench is now a plain
    module with ports and refers to signals by their bare names, so the same
    rewrite would corrupt every file it touched.
    """
    return code


def _fix_top_module(code: str) -> str:
    """No-op, kept so the call site stays stable.

    This used to normalise `tb_inst.<something> = <if_inst>;` to
    `tb_inst.intf = ...`. irun 15.20 rejects that hierarchical virtual
    interface assignment outright (*E,VIFCVU), so the top module now connects
    the testbench by named ports and there is nothing to normalise.
    """
    return code


def _read(path: str) -> str:
    """File contents, or empty string if it cannot be read. Used to feed the
    coverage model into refinement prompts; a missing file must degrade the
    prompt, never crash the run."""
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception:
        return ""


def _sim_errors(out: str) -> str:
    """
    Extract relevant simulator errors from irun output.
    """
    lines = [
        l for l in out.splitlines()
        if any(k in l.lower() for k in ["*e,", "*f,", "error:", "fatal"])
        and "0 error" not in l.lower()
    ]
    return "\n".join(lines[:30])


# =============================================================================
# Phase 1: Generate golden files
# =============================================================================

def phase1_golden(
    design: DesignInfo, run_dir: Path, client: GeminiClient, regen: bool
) -> tuple:
    """
    Returns (if_path, cov_path, top_path) -- always paths inside run_dir.
    The design_dir copies act as a persistent cache for reuse across runs.
    irun always compiles from run_dir so all 5 files come from one folder.
    """
    design_dir = Path(design.file_path).parent

    # Persistent cache paths (next to RTL) -- used only for caching
    cache_if  = design_dir / f"{_if_name(design)}.sv"
    cache_cov = design_dir / f"{_cov_name(design)}.sv"
    cache_top = design_dir / f"{_top_name(design)}.sv"

    # Paths irun will actually compile -- always inside run_dir
    out_if    = run_dir / f"{_if_name(design)}.sv"
    out_cov   = run_dir / f"{_cov_name(design)}.sv"
    out_top   = run_dir / f"{_top_name(design)}.sv"

    if cache_if.exists() and cache_cov.exists() and cache_top.exists() and not regen:
        banner("PHASE 1 -- Reusing golden files")
        tick(f"Interface    : {cache_if}")
        tick(f"Coverage     : {cache_cov}")
        tick(f"Top module   : {cache_top}")
        info("Pass --regen_cov to regenerate")
        # Copy cached files into run_dir so irun finds everything in one folder.
        # Always re-apply _fix_top_module in case the cached top has a stale vif name.
        save(out_if,  cache_if.read_text(encoding="utf-8"))
        save(out_cov, cache_cov.read_text(encoding="utf-8"))
        top_code = _fix_top_module(cache_top.read_text(encoding="utf-8"))
        save(out_top, top_code)
        save(cache_top, top_code)   # update cache so next reuse is already clean
        return str(out_if), str(out_cov), str(out_top)

    banner("PHASE 1 -- Generating golden files")

    check_dir = run_dir / "syntax_check"
    check_dir.mkdir(parents=True, exist_ok=True)

    def _gen_checked(kind, label, prompt_fn, gen_fn, cache_path, out_path,
                     deps, post=None, top=None):
        """Generate one golden file, then COMPILE it immediately and repair it
        until it is clean. Catching a bad file here costs one short irun run;
        catching it later costs a whole wasted iteration -- a testbench
        generation, a full elaboration and an IMC run."""
        info(f"Generating {label} ...")
        prompt = prompt_fn(design)
        save(run_dir / f"{label}_prompt.txt", prompt)
        code = gen_fn(prompt)
        if post:
            code = post(code)
        save(out_path, code)
        tick(f"{label}: {len(code.splitlines())} lines")

        basename = Path(out_path).name
        prev_errs = None
        for attempt in range(1, config.GOLDEN_MAX_REPAIRS + 2):
            ok, errs = syntax_check.check(deps + [str(out_path)], str(check_dir),
                                          top=top)
            if ok:
                tick(f"{label}: compiles cleanly")
                save(cache_path, code)
                return code

            # The check compiles this file together with its dependencies, so a
            # broken dependency fails it too. Repairing THIS file for someone
            # else's error cannot work: on the FIFO a bad interface made the
            # coverage model and the top module each burn every repair attempt
            # on errors they had nothing to do with. Only errors naming this
            # file are this file's to fix.
            own_errs = "\n".join(l for l in errs.splitlines() if basename in l)
            if not own_errs.strip():
                warn(f"{label}: compile failed, but every error is in a "
                     f"dependency, not in {basename} -- not repairing it")
                for line in errs.splitlines()[:3]:
                    warn(f"    {line.strip()[:110]}")
                save(cache_path, code)
                return code
            errs = own_errs

            # An identical error after a repair means the model is not
            # converging on this one; further attempts just spend credits.
            if errs == prev_errs:
                warn(f"{label}: repair produced the same error -- not retrying")
                warn(errs[:400])
                save(cache_path, code)
                return code
            prev_errs = errs

            if attempt > config.GOLDEN_MAX_REPAIRS:
                warn(f"{label}: still failing after {config.GOLDEN_MAX_REPAIRS} "
                     f"repair attempt(s) -- continuing anyway")
                warn(errs[:400])
                save(cache_path, code)
                return code

            warn(f"{label}: compile failed (repair {attempt}/{config.GOLDEN_MAX_REPAIRS})")
            for line in errs.splitlines()[:3]:
                warn(f"    {line.strip()[:110]}")

            rp = build_repair_prompt(kind, design, code, errs)
            save(run_dir / f"{label}_repair_{attempt}_prompt.txt", rp)
            code = client.generate_coverage_model(rp)
            if post:
                code = post(code)
            save(out_path, code)

    # The interface is mechanical -- one logic per DUT port plus the mirrored
    # modports -- so it is written directly rather than generated. See
    # prompt_builder.build_interface_code for why.
    info("Writing interface (generated locally, no API call) ...")
    if_code = build_interface_code(design)
    save(out_if, if_code)
    save(cache_if, if_code)
    ok, errs = syntax_check.check([str(out_if)], str(check_dir))
    if ok:
        tick(f"interface: {len(if_code.splitlines())} lines, compiles cleanly")
    else:
        cross("interface: FAILED TO COMPILE -- this is a bug in "
              "prompt_builder.build_interface_code, not model output")
        warn(errs[:400])

    # ensure_per_instance is applied to every generation AND every repair: the
    # line is what makes IMC record the covergroup at all, and a model that
    # drops it fails silently rather than failing to compile.
    cov_code = _gen_checked("coverage_model", "coverage_model",
                            build_coverage_model_prompt, client.generate_coverage_model,
                            cache_cov, out_cov, deps=[str(out_if)],
                            post=ensure_per_instance)

    # The top module is pure wiring -- every line of it was already assembled in
    # Python and handed to the model with "change nothing but the comments".
    # Write it here instead. See prompt_builder.build_top_code.
    info("Writing top module (generated locally, no API call) ...")
    top_code = build_top_code(design, cov_module_code=cov_code)
    save(out_top, top_code)
    save(cache_top, top_code)

    # The top instantiates the testbench, which does not exist yet, so a
    # placeholder stands in purely for this compile check. Elaborating the top
    # catches wiring errors -- port mismatches, multiple drivers -- here rather
    # than during the run.
    stub_tb = check_dir / f"{_tb_name(design)}.sv"
    syntax_check.stub_testbench(design.name, _tb_port_decl(design), str(stub_tb))
    ok, errs = syntax_check.check(
        [design.file_path, str(out_if), str(out_cov), str(stub_tb), str(out_top)],
        str(check_dir), top=_top_name(design))
    if ok:
        tick(f"top_module: {len(top_code.splitlines())} lines, elaborates cleanly")
    else:
        own = "\n".join(l for l in errs.splitlines() if out_top.name in l)
        if own.strip():
            cross("top_module: FAILED -- this is a bug in "
                  "prompt_builder.build_top_code, not model output")
            warn(own[:400])
        else:
            warn("top_module: elaboration failed, but the errors are in the "
                 "coverage model or the DUT, not in the top module")
            warn(errs[:400])

    info("Golden files saved to run_dir (cached in design_dir for future runs)")
    return str(out_if), str(out_cov), str(out_top)


def record_in_knowledge_base(design: DesignInfo, coverage_model_code: str,
                             verified: bool, coverage: float = 0.0) -> None:
    """Append this run's (requirement, RTL, coverage model) triple to the corpus.

    `verified` must be True only when the coverage model actually compiled and
    produced coverage. Unverified entries are stored for the record but are NOT
    indexed for retrieval -- otherwise a covergroup that never compiled gets
    retrieved on a later run as a "known-good example" and its errors get
    imitated instead of fixed.
    """
    if not config.RAG_ENABLED:
        return
    try:
        from retriever import get_kb
        note = (f"Auto-recorded from run; overall coverage {coverage:.2f}%."
                if verified else
                "Auto-recorded from run; NOT verified (did not compile / no coverage).")
        get_kb().add_entry(
            english_requirement=(design.coverage_spec
                                 or f"(inferred) functional coverage for {design.name}"),
            coverage_model=coverage_model_code,
            rtl=design.rtl_code,
            design_context={"module": design.name.upper(),
                            "data_width": _infer_width(design),
                            "type": f"{design.name} module"},
            signals=design.inputs + design.outputs,
            verified=verified,
            notes=note,
        )
        tick(f"Knowledge base updated (verified={verified})")
    except Exception as exc:
        warn(f"Could not update knowledge base: {exc}")


def _infer_width(design: DesignInfo) -> int:
    """Widest declared port width, as a coarse design-size hint for the corpus."""
    import re
    widest = 1
    for p in design.ports:
        m = re.search(r'\[\s*(\d+)\s*:\s*(\d+)\s*\]', p.get("width", "") or "")
        if m:
            widest = max(widest, abs(int(m.group(1)) - int(m.group(2))) + 1)
    return widest


def repair_golden_files(
    design: DesignInfo, sim_err: str, if_file: str, cov_file: str, top_file: str,
    run_dir: Path, client: GeminiClient, iteration: int,
) -> bool:
    """Golden files are generated once and only the testbench iterates, so a
    compile error inside the interface/coverage/top would otherwise repeat
    forever. When irun's errors name one of them, regenerate that file from
    its original requirements plus the compiler errors, and update both the
    run_dir copy irun compiles and the design_dir cache.

    Returns True if any file was repaired.
    """
    if not sim_err.strip():
        return False

    design_dir = Path(design.file_path).parent

    # The interface is written locally, so if irun blames it the fix is to
    # rewrite it from the port table -- not to ask the model.
    if_base = Path(if_file).name
    if if_base in sim_err:
        warn(f"Compile errors name {if_base} -- rewriting it from the port table")
        fresh = build_interface_code(design)
        save(Path(if_file), fresh)
        save(design_dir / f"{_if_name(design)}.sv", fresh)
        tick(f"Rewrote {if_base}")

    top_base = Path(top_file).name
    if top_base in sim_err:
        warn(f"Compile errors name {top_base} -- rewriting it from the port table")
        fresh = build_top_code(design, cov_module_code=_read(cov_file))
        save(Path(top_file), fresh)
        save(design_dir / f"{_top_name(design)}.sv", fresh)
        tick(f"Rewrote {top_base}")

    targets = [
        ("coverage_model", cov_file, design_dir / f"{_cov_name(design)}.sv"),
    ]

    repaired = (if_base in sim_err) or (top_base in sim_err)
    for kind, out_path, cache_path in targets:
        basename = Path(out_path).name
        if basename not in sim_err:
            continue

        warn(f"Compile errors implicate golden file {basename} -- repairing it")
        broken = Path(out_path).read_text(encoding="utf-8")

        # Only feed back the error lines naming this file, so the LLM isn't
        # distracted by unrelated failures in the other four files.
        own_errors = "\n".join(l for l in sim_err.splitlines() if basename in l)

        prompt = build_repair_prompt(kind, design, broken, own_errors or sim_err)
        save(run_dir / f"repair_{kind}_iter_{iteration:02d}_prompt.txt", prompt)

        fixed = client.generate_coverage_model(prompt)   # same plain SV extraction
        if kind == "coverage_model":
            fixed = ensure_per_instance(fixed)
        if kind == "top_module":
            fixed = _fix_top_module(fixed)

        save(Path(out_path), fixed)
        save(cache_path, fixed)
        tick(f"Repaired {basename} (cache updated)")
        repaired = True

    return repaired


# =============================================================================
# Phase 2: One iteration
# =============================================================================

def phase2_iteration(
    iteration:    int,
    design:       DesignInfo,
    if_file:      str,
    cov_file:     str,
    top_file:     str,
    prev_tb:      str,
    prev_summary: str,
    prev_detail:  str,
    prev_cov:     float,
    prev_err:     str,
    run_dir:      Path,
    client:       GeminiClient,
    threshold:    float,
) -> tuple:

    iter_dir = run_dir / f"iter_{iteration:02d}"
    iter_dir.mkdir(parents=True, exist_ok=True)
    sim_dir  = str(iter_dir / "sim_work")

    strategy = ("RANDOM" if iteration == 0
                else "CONSTRAINED RANDOM" if iteration == 1
                else f"DIRECTED (iter {iteration})")

    banner(f"ITERATION {iteration} -- {strategy}  |  Coverage: {prev_cov:.2f}%  |  Target: {threshold:.1f}%")

    if iteration == 0:
        info("Strategy: CRV (2000 cycles) + directed corner cases")
        prompt = build_random_tb_prompt(design)
    elif iteration == 1:
        info("Strategy: constrained random biased toward uncovered bins")
        dut_only = coverage_parser.filter_detail_to_dut(prev_detail, design.name)
        trimmed  = coverage_parser.trim_detail_for_prompt(dut_only, max_chars=2000)
        prompt  = build_constrained_tb_prompt(design, prev_tb, prev_summary, trimmed,
                                              prev_cov, prev_err, cov_model=_read(cov_file))
    else:
        info("Strategy: directed sequences for each uncovered item")
        dut_only = coverage_parser.filter_detail_to_dut(prev_detail, design.name)
        trimmed  = coverage_parser.trim_detail_for_prompt(dut_only, max_chars=2000)
        prompt  = build_directed_tb_prompt(design, prev_tb, prev_summary, trimmed,
                                           prev_cov, iteration, prev_err,
                                           cov_model=_read(cov_file))

    save(iter_dir / "prompt.txt", prompt)
    info(f"Prompt: {len(prompt)} chars")

    info("Calling Gemini for testbench ...")
    tb_code = client.generate_testbench(prompt)
    tb_code = _fix_clock_refs(tb_code, design.clock)   # guarantee intf.clk everywhere
    tb_file = iter_dir / f"{_tb_name(design)}.sv"
    save(tb_file, tb_code)
    tick(f"Testbench: {tb_code.count(chr(10))+1} lines")

    info("Running irun (rtl + interface + coverage + tb + top) ...")
    sim_ok, sim_out = simulator.run(
        design_file = design.file_path,
        if_file     = if_file,
        cov_file    = cov_file,
        tb_file     = str(tb_file),
        top_file    = top_file,
        run_dir     = sim_dir,
        dut_module  = design.name,
    )
    save(iter_dir / "sim_output.txt", sim_out)

    sim_err = ""
    if sim_ok:
        tick("irun: simulation complete")
    else:
        warn("irun: non-zero exit -- check sim_output.txt")
        sim_err = _sim_errors(sim_out)
        if sim_err:
            warn(f"Errors:\n{sim_err}")

    info("Running IMC ...")
    imc_summary, imc_detail, imc_functional = imc_runner.generate_reports(
        run_dir=sim_dir, dut_module=design.name)
    save(iter_dir / "imc_summary.rpt", imc_summary)
    save(iter_dir / "imc_detail.rpt",  imc_detail)
    if imc_functional.strip():
        save(iter_dir / "imc_functional.rpt", imc_functional)
    tick("IMC reports written")

    breakdown = coverage_parser.parse_summary(imc_summary)

    # Functional coverage, in order of reliability.
    #
    # IMC on this tool version reports "Functional: n/a" even with the coverage
    # module inside the -covdut scope, so the coverage database is not a
    # dependable source for it. The simulator's own end-of-simulation covergroup
    # score is, which is why the coverage model prints it and why that reading
    # is preferred over anything IMC says.
    sv_functional = coverage_parser.parse_sv_functional(sim_out)
    if sv_functional is not None:
        if breakdown.functional is None:
            info("Functional coverage taken from the simulator's own covergroup "
                 "score (IMC reported it as n/a)")
        elif abs(sv_functional - breakdown.functional) > 0.01:
            warn(f"IMC says functional={breakdown.functional:.2f}% but the simulator "
                 f"says {sv_functional:.2f}% -- using the simulator's figure")
        breakdown.functional = sv_functional
        breakdown.categories["Functional"] = sv_functional
    elif breakdown.functional is None:
        scraped = coverage_parser.parse_functional_report(imc_functional)
        if scraped is not None:
            breakdown.functional = scraped
            breakdown.categories["Functional"] = scraped
            info(f"Functional coverage read from {config.IMC_FUNCTIONAL_REPORT} "
                 f"(the per-DUT summary reported it as n/a)")

    func_measured = breakdown.functional_measured
    new_cov = breakdown.headline()

    if breakdown.categories:
        info("Coverage by type: " + "  ".join(
            f"{k}={v:.1f}%" for k, v in breakdown.categories.items()
            if k.lower() != "overall"))

    if func_measured:
        tick(f"Functional (covergroup) coverage: {breakdown.functional:.2f}%"
             + (f"   code coverage: {breakdown.code:.2f}%" if breakdown.code is not None else ""))
    else:
        warn("FUNCTIONAL COVERAGE WAS NOT MEASURED.")
        warn("  IMC reported it as 'n/a' AND the simulation printed no")
        warn("  SV_FUNCTIONAL_COVERAGE line, so there is no reading from either")
        warn("  source. The number below is CODE coverage (block/expression/")
        warn("  toggle) only -- it says nothing about whether the covergroups")
        warn("  were hit, which is the entire point of this pipeline.")
        warn("  Most likely cause: the coverage model is a cached copy from")
        warn("  before the `final` block was added. Re-run with --regen_cov.")
        warn(f"  Otherwise check that {design.name}_coverage's final block survived")
        warn(f"  generation, and look at {sim_dir}/../sim_output.txt.")

    # If nothing in the DUT is uncovered, the remaining gap is harness code and
    # no amount of extra stimulus will close it.
    dut_holes = coverage_parser.filter_detail_to_dut(imc_detail, design.name)
    dut_clean = dut_holes.startswith("(no uncovered items in the DUT")
    if dut_clean:
        tick("No uncovered items remain in the DUT itself")

    delta = new_cov - prev_cov
    arrow = (f"^ +{delta:.2f}%" if delta > 0 else f"v {delta:.2f}%" if delta < 0 else "-> no change")
    info(f"Coverage: {prev_cov:.2f}% -> {new_cov:.2f}%  ({arrow})")

    save(iter_dir / "iter_summary.json", json.dumps({
        "iteration": iteration, "strategy": strategy,
        "coverage": new_cov, "delta": delta,
        "coverage_metric": "functional" if func_measured else "code_only",
        "functional_coverage": breakdown.functional,
        "code_coverage": breakdown.code,
        "functional_measured": func_measured,
        "sim_ok": sim_ok, "sim_errors": sim_err,
    }, indent=2))

    if sv_functional is not None:
        imc_summary = (
            f"{imc_summary}\n"
            f"Functional (covergroup) coverage reported by the simulator: "
            f"{sv_functional:.2f}%\n"
            "(This is the number to improve. IMC's summary above may show the\n"
            "functional columns as n/a; that is a database limitation, not a score.)\n"
        )

    return tb_code, new_cov, imc_summary, imc_detail, sim_err, dut_clean, func_measured


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--design",    required=True)
    parser.add_argument("--spec",      default=None,
                        help="English functional-coverage requirement, or @path/to/file.txt. "
                             "Falls back to <design>.spec.txt beside the RTL file if omitted.")
    parser.add_argument("--threshold", type=float, default=None)
    parser.add_argument("--max_iter",  type=int,   default=None)
    parser.add_argument("--mock",      action="store_true")
    parser.add_argument("--regen_cov", action="store_true",
                        help="Regenerate golden interface, coverage, and top files")
    args = parser.parse_args()

    threshold = args.threshold or config.COVERAGE_THRESHOLD
    max_iter  = args.max_iter  or config.MAX_ITERATIONS
    if args.mock:
        config.MOCK_SIMULATOR = True

    ts      = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = Path(config.OUTPUT_BASE_DIR) / f"run_{ts}"
    run_dir.mkdir(parents=True, exist_ok=True)

    log = setup_logging(run_dir)

    print(f"""
{'#'*64}
  Coverage-Driven SV Verification Framework
  Model      : {config.GEMINI_MODEL}
  Design     : {args.design}
  Files      : interface.sv + coverage.sv + tb.sv + top.sv
  Simulator  : {"MOCK" if config.MOCK_SIMULATOR else config.IRUN_BIN}
  IMC        : {"MOCK" if config.MOCK_SIMULATOR else config.IMC_BIN}
  Threshold  : {threshold}%
  Max iters  : {max_iter}
  Regen      : {args.regen_cov}
  Run dir    : {run_dir}
{'#'*64}""")

    if not Path(args.design).exists():
        cross(f"Design file not found: {args.design}")
        sys.exit(1)

    spec_text = None
    if args.spec:
        if args.spec.startswith("@"):
            spec_path = Path(args.spec[1:])
            if not spec_path.exists():
                cross(f"Spec file not found: {spec_path}"); sys.exit(1)
            spec_text = spec_path.read_text(encoding="utf-8").strip()
        else:
            spec_text = args.spec.strip()

    design = parse_design(args.design, coverage_spec=spec_text)
    tick(f"Design: module='{design.name}'")
    info(f"  Inputs : {design.inputs}")
    info(f"  Outputs: {design.outputs}")
    info(f"  Clock  : {design.clock}   Reset: {design.reset}")
    if design.coverage_spec:
        info(f"  Spec   : {design.coverage_spec[:100]}{'...' if len(design.coverage_spec) > 100 else ''}")
    else:
        warn("No coverage spec provided or found -- LLM will infer goals from ports only")

    if not config.COV_DUT_MODULE:
        config.COV_DUT_MODULE = design.name

    try:
        client = GeminiClient()
        tick("Gemini client ready")
    except EnvironmentError as e:
        cross(str(e)); sys.exit(1)

    try:
        if_file, cov_file, top_file = phase1_golden(design, run_dir, client, args.regen_cov)
    except RuntimeError as e:
        cross(f"Golden file generation failed: {e}"); sys.exit(1)

    tb_code = ""; coverage = 0.0; imc_summary = ""; imc_detail = ""
    last_err = ""; history = []; final_iter = 0; kb_recorded = False
    dut_clean = False; func_measured = False

    for iteration in range(max_iter):
        final_iter = iteration
        try:
            (tb_code, coverage, imc_summary, imc_detail,
             last_err, dut_clean, func_measured) = phase2_iteration(
                iteration=iteration, design=design,
                if_file=if_file, cov_file=cov_file, top_file=top_file,
                prev_tb=tb_code, prev_summary=imc_summary,
                prev_detail=imc_detail, prev_cov=coverage,
                prev_err=last_err, run_dir=run_dir,
                client=client, threshold=threshold,
            )
        except RuntimeError as e:
            cross(f"Iteration {iteration} failed: {e}")
            log.exception("Iteration error")
            break

        history.append({"iteration": iteration,
                         "strategy": ("random" if iteration == 0
                                      else "constrained" if iteration == 1 else "directed"),
                         "coverage": coverage,
                         "functional_measured": func_measured})

        # A compile error inside a golden file repeats every iteration until the
        # golden file itself is fixed, so repair it before giving up.
        if coverage == 0.0 and last_err:
            if repair_golden_files(design, last_err, if_file, cov_file, top_file,
                                   run_dir, client, iteration):
                info("Golden files repaired -- retrying")
                continue

        if coverage == 0.0 and iteration >= 1:
            cross("Simulation failed multiple times -- check testbench errors")
            break

        # The coverage model provably compiles and yields *functional* coverage,
        # so it is now safe to admit into the retrieval corpus as a verified
        # example. Code coverage is not evidence about the covergroups: a
        # coverage model whose covergroups were never scored could sit at 100%
        # code coverage and still be worthless, and admitting it here is exactly
        # how the corpus poisoned itself before.
        if coverage > 0.0 and func_measured and not kb_recorded:
            record_in_knowledge_base(
                design, Path(cov_file).read_text(encoding="utf-8"),
                verified=True, coverage=coverage)
            kb_recorded = True

        # A run in which the covergroups were never scored has not met the goal,
        # however good the code-coverage number looks. Keep iterating (the extra
        # attempts are cheap next to a false "100%") and never print [DONE].
        blocked_on_functional = (not func_measured) and config.REQUIRE_FUNCTIONAL_COVERAGE

        # dut_clean means IMC's *code* coverage detail lists no uncovered items
        # in the DUT. That is not a reason to stop on its own: code coverage hits
        # 100% on a trivial design long before the covergroups are full, so the
        # threshold on functional coverage still has to be met.
        if dut_clean and not blocked_on_functional and coverage >= threshold:
            banner(f"[DONE] DUT FULLY COVERED -- {coverage:.2f}% functional")
            tick("No uncovered code items in the DUT either")
            tick(f"Converged in {iteration + 1} iteration(s)")
            break
        if dut_clean and coverage < threshold:
            info("No uncovered code items in the DUT, but functional coverage is "
                 f"{coverage:.2f}% -- covergroup bins remain, continuing")

        if coverage >= threshold and not blocked_on_functional:
            banner(f"[DONE] TARGET REACHED -- {coverage:.2f}% >= {threshold}%")
            tick(f"Converged in {iteration + 1} iteration(s)")
            break
        elif blocked_on_functional:
            banner("[BLOCKED] NO FUNCTIONAL COVERAGE MEASURED")
            warn(f"{coverage:.2f}% is code coverage; the covergroups were not scored,")
            warn("so this run does NOT count as reaching the target. Re-run with")
            warn("--regen_cov so the coverage model is rebuilt with the `final` block")
            warn("that prints the covergroup score.")
            warn("(Set REQUIRE_FUNCTIONAL_COVERAGE=False in config.py to accept")
            warn(" code coverage alone, but then stop calling the result functional.)")
            break
        else:
            warn(f"Coverage {coverage:.2f}% < {threshold}% -- next strategy ...")
    else:
        banner(f"[WARN] MAX ITERATIONS ({max_iter}) REACHED")
        warn(f"Final coverage: {coverage:.2f}%")

    final_tb = run_dir / f"FINAL_{_tb_name(design)}.sv"
    save(final_tb, tb_code)
    tick(f"Final testbench: {final_tb}")

    # A run only succeeds if the metric it optimised was the functional one.
    success = (coverage >= threshold or dut_clean) and (
        func_measured or not config.REQUIRE_FUNCTIONAL_COVERAGE)

    save(run_dir / "summary.json", json.dumps({
        "design": args.design, "module": design.name,
        "model": config.GEMINI_MODEL, "threshold": threshold,
        "final_coverage": coverage, "success": success,
        "coverage_metric": "functional" if func_measured else "code_only",
        "functional_measured": func_measured,
        "iterations_used": final_iter + 1, "history": history,
        "interface": if_file, "coverage_model": cov_file,
        "top_file": top_file, "final_tb": str(final_tb),
        "run_dir": str(run_dir),
    }, indent=2))

    banner("RUN COMPLETE")
    info(f"Design         : {args.design}  [{design.name}]")
    info(f"Interface      : {if_file}  [GOLDEN]")
    info(f"Coverage model : {cov_file}  [GOLDEN]")
    info(f"Top module     : {top_file}  [GOLDEN]")
    info(f"Iterations     : {final_iter + 1} / {max_iter}")
    metric = "FUNCTIONAL (covergroup)" if func_measured else "CODE ONLY -- covergroups NOT scored"
    info(f"Final coverage : {coverage:.2f}%  (target: {threshold}%)")
    info(f"Metric         : {metric}")
    info(f"Final TB       : {final_tb}")
    info(f"Run folder     : {run_dir}")
    print()
    print(f"  {'Iter':>4}  {'Strategy':>12}  {'Coverage':>10}")
    print(f"  {'-'*32}")
    for h in history:
        flag = "" if h.get("functional_measured") else "   <- code coverage only"
        print(f"  {h['iteration']:>4}  {h['strategy']:>12}  {h['coverage']:>9.2f}%{flag}")
    print()
    if not func_measured:
        cross("Functional coverage was never measured in this run.")
        cross("Do not report this percentage as functional coverage.")
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
