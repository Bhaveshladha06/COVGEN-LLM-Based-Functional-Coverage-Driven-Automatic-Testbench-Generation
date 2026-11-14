#!/usr/bin/env python3
"""
prompt_builder.py -- RTL parsing + prompt construction for the 4-file
architecture (interface / coverage model / top / testbench).

Only build_coverage_model_prompt() talks to the FAISS knowledge base
(retriever.py): the interface, top, and coverage model are generated once
per design and cached (see main.py phase1_golden), matching the
architecture diagram where the RAG retrieval box only feeds the first
Prompt Generator. The per-iteration testbench prompts intentionally do not
retrieve -- their feedback signal is the previous iteration's own coverage
report, not the corpus.
"""

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import config

log = logging.getLogger("PromptBuilder")


# =============================================================================
# RTL parsing
# =============================================================================

@dataclass
class DesignInfo:
    name: str
    file_path: str
    rtl_code: str
    ports: List[Dict[str, str]]
    inputs: List[str]
    outputs: List[str]
    clock: str
    reset: str
    coverage_spec: str = ""


_MODULE_RE = re.compile(r'\bmodule\s+(\w+)')

_DIR_RE = re.compile(r'\b(input|output|inout)\b')
_WIDTH_RE = re.compile(r'^\s*(?:wire|reg|logic)?\s*(?:signed\s+)?(\[[^\]]+\])?\s*(.*)$', re.S)
_IDENT_RE = re.compile(r'^[A-Za-z_]\w*$')


def _parse_ports(rtl_code: str) -> List[Dict[str, str]]:
    """Best-effort Verilog/SV port extraction, handling both styles:

        input a, b, sel;              -> a, b, sel   (non-ANSI, shared decl)
        input [7:0] a, b;             -> a, b        (shared width)
        input wire clk,               -> clk         (ANSI, one per line)
        output reg [3:0] count

    A single direction keyword can introduce SEVERAL comma-separated names,
    all sharing the declared width. Grabbing only the first identifier after
    the keyword silently drops ports, which then go missing from the prompt
    and from the generated interface. Not a full HDL parser -- consistent
    with the regex approach used elsewhere in this project.
    """
    # Strip comments so they cannot contribute identifiers.
    code = re.sub(r'//[^\n]*', ' ', rtl_code)
    code = re.sub(r'/\*.*?\*/', ' ', code, flags=re.S)

    ports: List[Dict[str, str]] = []
    seen = set()

    matches = list(_DIR_RE.finditer(code))
    for i, m in enumerate(matches):
        direction = m.group(1)
        # Segment runs to the next direction keyword, or a ';' / ')' terminator.
        end = matches[i + 1].start() if i + 1 < len(matches) else len(code)
        segment = code[m.end():end]
        stop = min([p for p in (segment.find(';'), segment.find(')')) if p != -1],
                   default=len(segment))
        segment = segment[:stop]

        wm = _WIDTH_RE.match(segment)
        if not wm:
            continue
        width, names_blob = (wm.group(1) or "").strip(), wm.group(2)

        for raw in names_blob.split(','):
            name = raw.strip()
            # Drop any lingering type keyword prefix on an individual name.
            name = re.sub(r'^(?:wire|reg|logic|signed)\s+', '', name).strip()
            if not _IDENT_RE.match(name) or name in seen:
                continue
            seen.add(name)
            ports.append({"dir": direction, "width": width, "name": name})

    return ports


def _guess_clock(inputs: List[str]) -> str:
    """Empty string when the design has no clock port -- a combinational block.
    Callers must not fall back to a literal "clk" that does not exist on the
    DUT, or the generated files reference a phantom signal."""
    return next((s for s in inputs if re.search(r'clk|clock', s, re.I)), "")


def _guess_reset(inputs: List[str]) -> str:
    return next((s for s in inputs if re.search(r'rst|reset', s, re.I)), "")


def _load_spec_sidecar(rtl_path: Path) -> str:
    """Convenience fallback: <design>.spec.txt next to the RTL file, used
    when --spec isn't passed on the command line."""
    sidecar = rtl_path.with_suffix("").with_suffix(".spec.txt")
    if sidecar.exists():
        log.info(f"Loaded coverage spec sidecar: {sidecar}")
        return sidecar.read_text(encoding="utf-8").strip()
    return ""


def parse_design(path: str, coverage_spec: Optional[str] = None) -> DesignInfo:
    rtl_path = Path(path)
    rtl_code = rtl_path.read_text(encoding="utf-8")

    name_match = _MODULE_RE.search(rtl_code)
    name = name_match.group(1) if name_match else rtl_path.stem

    ports = _parse_ports(rtl_code)
    inputs = [p["name"] for p in ports if p["dir"] == "input"]
    outputs = [p["name"] for p in ports if p["dir"] in ("output", "inout")]

    clock = _guess_clock(inputs)
    reset = _guess_reset(inputs)
    if not clock:
        log.info(f"No clock port found on '{name}' -- treating as combinational")

    if coverage_spec is None:
        coverage_spec = _load_spec_sidecar(rtl_path)

    return DesignInfo(
        name=name, file_path=str(rtl_path), rtl_code=rtl_code,
        ports=ports, inputs=inputs, outputs=outputs,
        clock=clock, reset=reset, coverage_spec=(coverage_spec or "").strip(),
    )


# =============================================================================
# Naming helpers (must match main.py's 4-file architecture)
# =============================================================================

def _if_name(design: DesignInfo) -> str:
    return f"{design.name}_if"


def _cov_name(design: DesignInfo) -> str:
    return f"{design.name}_coverage"


def _tb_name(design: DesignInfo) -> str:
    return f"tb_{design.name}"


def _top_name(design: DesignInfo) -> str:
    return f"top_{design.name}"


def _port_table(design: DesignInfo) -> str:
    return "\n".join(
        f"  {p['dir']:<6} {p['width']:<10} {p['name']}" for p in design.ports
    ) or "  (no ports parsed -- verify the RTL file)"


def _tb_ports(design: DesignInfo):
    """Testbench port list. The testbench DRIVES the DUT's inputs and OBSERVES
    its outputs, so the directions are mirrored relative to the DUT. The clock
    is generated by the top module, so the testbench only reads it.

    A virtual interface handle would be the modern way to do this, but irun
    15.20 rejects assigning one hierarchically (*E,VIFCVU), so the testbench is
    a plain module with ports instead.
    """
    ins, outs = [], []
    for p in design.ports:
        w = (p["width"] + " ") if p["width"] else ""
        if p["dir"] == "input" and p["name"] != design.clock:
            outs.append(f"  output logic {w}{p['name']}")
        else:
            ins.append(f"  input  logic {w}{p['name']}")
    return ins, outs


def _tb_port_decl(design: DesignInfo) -> str:
    ins, outs = _tb_ports(design)
    return ",\n".join(ins + outs)


def _port_conn(design: DesignInfo, inst: str) -> str:
    return ",\n".join(f"    .{p['name']:<12}({inst}.{p['name']})" for p in design.ports)


def _rtl_excerpt(design: DesignInfo, max_chars: int = None) -> str:
    """The design's own source, for prompts that must reason about what it can
    actually produce.

    The coverage-model prompt used to carry only the port table, so the model
    had no way to know that a 4-bit `count` on an 8-deep FIFO never exceeds 8.
    It binned 0/1/[2:14]/15 off the declared width, and the bin for 15 and the
    transition (14 => 15) became permanent holes -- the FIFO's missing 9.82%.
    Every instruction to prune unreachable bins is useless without this.
    """
    if max_chars is None:
        max_chars = config.RTL_MAX_PROMPT_CHARS
    code = design.rtl_code.strip()
    if len(code) <= max_chars:
        return code
    return (code[:max_chars]
            + f"\n// ... truncated at {max_chars} chars of {len(code)} ...")


def _spec_line(design: DesignInfo, label: str = "COVERAGE REQUIREMENT (English)") -> str:
    if design.coverage_spec:
        return f'{label}: "{design.coverage_spec}"'
    return f"{label}: none provided -- infer sensible goals from the port list and design name."


# =============================================================================
# Phase 1 prompts (golden files -- generated once per design)
# =============================================================================

def build_interface_code(design: DesignInfo) -> str:
    """Write the interface directly, without asking the model for it.

    The interface is a pure signal bundle: one `logic` per DUT port, at the same
    width, plus the two mirrored modports. Nothing about it requires judgement,
    and every fact it needs is already in the parsed port table -- so generating
    it costs an API call and buys only the chance of getting it wrong.

    It did get it wrong: on the FIFO the generated `fifo_if.sv` failed to parse
    (*E,EXPIDN / *E,FNDKWD) three times in phase 1, and because every later
    syntax check compiles the interface as a dependency, its errors were then
    blamed on the coverage model and the top module, costing six more repair
    calls for files that were fine. Writing it here removes that whole class of
    failure and one round trip per design.
    """
    lines = [
        "`timescale 1ns/1ps",
        f"// Generated by prompt_builder.build_interface_code -- not by the LLM.",
        f"interface {_if_name(design)};",
        "",
    ]
    for p in design.ports:
        width = (p["width"] + " ") if p["width"] else ""
        lines.append(f"  logic {width}{p['name']};")

    dut_in  = [p["name"] for p in design.ports if p["dir"] == "input"]
    dut_out = [p["name"] for p in design.ports if p["dir"] != "input"]

    def modport(name: str, ins, outs) -> List[str]:
        items = [f"input  {n}" for n in ins] + [f"output {n}" for n in outs]
        if not items:
            return []
        body = ",\n".join(f"    {it}" for it in items)
        return ["", f"  modport {name} (", body, "  );"]

    # `dut` sees the DUT's own directions; `tb` is the mirror image.
    lines += modport("dut", dut_in, dut_out)
    lines += modport("tb", dut_out, dut_in)
    lines += ["", "endinterface"]
    return "\n".join(lines) + "\n"


def _is_sequential(design: DesignInfo) -> bool:
    return bool(design.clock)


def _clock_line(design: DesignInfo) -> str:
    if not _is_sequential(design):
        return "Clocking    : none -- this is a COMBINATIONAL design (no clock or reset port)"
    reset = design.reset or "none"
    return f"Clock       : {design.clock}    Reset: {reset}"


def _sampling_rule(design: DesignInfo) -> str:
    """irun 15.20 rejects any covergroup whose @(...) event names one of the
    covergroup's own arguments (*E,EFASAM). A clock port is not passed as an
    argument so it is safe to clock on; a combinational design has no such
    signal, so it must carry no sampling event at all and be sampled by an
    explicit .sample() call from the testbench."""
    if _is_sequential(design):
        return (f"This design is SEQUENTIAL: clock the covergroup on the module's "
                f"{design.clock} port:\n"
                f"      covergroup {_cov_name(design)}_cg @(posedge {design.clock});")
    ins = [p["name"] for p in design.ports if p["dir"] == "input"]
    sens = " or ".join(ins) if ins else "the input ports"
    return (f"This design is COMBINATIONAL (no clock port). Give the covergroup NO sampling\n"
            f"    event and sample it explicitly, one time unit after the inputs change:\n\n"
            f"      covergroup {_cov_name(design)}_cg;          // no @(...) here\n"
            f"        option.per_instance = 1;\n"
            f"        <coverpoints and crosses>\n"
            f"      endgroup\n\n"
            f"      {_cov_name(design)}_cg cg_inst = new();\n\n"
            f"      // Sample AFTER the outputs have settled, not at the instant the\n"
            f"      // inputs change. `@({sens})` on its own fires in the same region as\n"
            f"      // the DUT's continuous assignments, so the output coverpoints would\n"
            f"      // read the PREVIOUS vector's results -- a race that still reports\n"
            f"      // 100% while crediting the wrong bins.\n"
            f"      always @({sens}) begin\n"
            f"        #1 cg_inst.sample();\n"
            f"      end\n\n"
            f"    Write that `always` block exactly as shown. Never reference a clock or "
            f"reset signal; the DUT has none.")


def _truncate(text: str, limit: int) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + f"\n... (truncated, {len(text) - limit} more chars)"


def _retrieval_query(design: DesignInfo) -> str:
    """Mirror of CoverageEntry.search_text(): the query is embedded in the same
    space as the corpus, combining the English requirement with the design's
    structural hints."""
    return (f"{design.coverage_spec} "
            f"{design.name} "
            f"{' '.join(design.inputs + design.outputs)}").strip()


def _covergroup_body(code: str) -> str:
    """Just the coverpoints and crosses, without the covergroup header.

    The header in the corpus uses `ref` arguments, but generated models are
    module-scoped and take none -- showing the header would model the wrong
    thing and cost prompt space for it.
    """
    m = re.search(r'covergroup\b[^;]*;(.*?)\bendgroup\b', code, re.S)
    body = (m.group(1) if m else code).strip()
    return _truncate(body, config.RAG_MAX_EXAMPLE_CHARS)


def _format_examples(examples: List) -> str:
    """Render retrieved entries compactly: the requirement that matched, and
    the coverpoint/cross body. The example's RTL and covergroup header are
    omitted -- they were the bulk of the prompt and taught nothing the target
    design's own port table does not already say."""
    if not examples:
        return ""

    block = "\n" + "-" * 66 + "\n"
    block += "EXAMPLE COVERAGE FROM A SIMILAR VERIFIED DESIGN -- copy this STYLE\n"
    block += "of binning and crossing, but use the target design's own signals.\n"

    for entry, score in examples:
        block += f"""
[{entry.design_context.get('type', 'design')}, similarity {score:.2f}]
Requirement: "{_truncate(entry.english_requirement, 200)}"
```systemverilog
{_covergroup_body(entry.coverage_model)}
```
"""
    return block


_CG_DECL_RE = re.compile(r'(covergroup\s+\w+[^;{]*;)')


def ensure_per_instance(code: str) -> str:
    """Insert `option.per_instance = 1;` into every covergroup that lacks it.

    This one line is the difference between IMC recording the covergroup and
    recording nothing. Measured on manual_test/: without it the coverage
    database holds no covergroup data and IMC reports Functional as n/a; with
    it, IMC reports 87.50% and names the empty bin

        |--count_cp    75.00% (3/4)
        | |--three      0.00% (0/1)   bins three = {2'd3};

    which is exactly the hole list the refinement loop needs and had no way to
    get. A covergroup's results can be merged across instances of the type or
    kept per instance, and this tool only writes the per-instance form into the
    database.

    The prompt asks for the line too, but asking is not a guarantee and a
    missing line fails silently -- the model still compiles, still samples, and
    quietly costs us the bin detail. So it is enforced here in Python.
    """
    if not code or "per_instance" in code:
        return code
    return _CG_DECL_RE.sub(r"\1\n    option.per_instance = 1;", code, count=0)


def build_coverage_model_prompt(design: DesignInfo, use_rag: bool = True) -> str:
    examples: List = []
    if config.RAG_ENABLED and use_rag:
        try:
            from retriever import get_kb
            examples = get_kb().retrieve(_retrieval_query(design))
        except Exception as exc:
            log.warning(f"RAG retrieval unavailable ({exc}) -- continuing without examples")

    if examples:
        examples_block = _format_examples(examples)
    elif config.RAG_ENABLED and use_rag:
        examples_block = (
            f"\n(No knowledge base entry cleared the similarity threshold "
            f"({config.RAG_MIN_SIMILARITY}). Generating from the rules below without "
            f"precedent -- do not invent an example to imitate.)\n"
        )
    else:
        examples_block = ""

    return f"""Write a SystemVerilog functional coverage model for the DUT below.

{"=" * 66}
TARGET DESIGN
{"=" * 66}
Module      : {design.name}
Ports (direction, width, name):
{_port_table(design)}
{_clock_line(design)}

RTL SOURCE (read it before choosing bins -- see the bin-boundary rule below):
```verilog
{_rtl_excerpt(design)}
```

{_spec_line(design)}
{examples_block}
{"=" * 66}
REQUIREMENTS FOR THE MODEL YOU GENERATE
{"=" * 66}
- Output a COMPLETE, COMPILABLE FILE: a module named `{_cov_name(design)}` whose ports are
  the DUT signals you want to cover, containing the covergroup and one instance of it.
  A bare covergroup on its own is not a valid file. The retrieved examples show only the
  covergroup body -- copy their BIN AND CROSS STYLE, but wrap yours like this:

      `timescale 1ns/1ps
      module {_cov_name(design)} (
        <input logic ports, one per DUT signal you cover, matching widths>
      );
        covergroup {_cov_name(design)}_cg <sampling event>;
          option.per_instance = 1;
          <labelled coverpoints and crosses>
        endgroup

        {_cov_name(design)}_cg cg_inst = new();

        // Report the covergroup score directly from the simulator, so the
        // number does not depend on the coverage database or IMC's flags.
        final begin
          $display("SV_FUNCTIONAL_COVERAGE: %0.4f", $get_coverage());
          $display("SV_CG_INST_COVERAGE: %0.4f", cg_inst.get_inst_coverage());
        end
      endmodule

- KEEP `option.per_instance = 1;` as the FIRST line inside the covergroup. Without it
  this simulator writes no covergroup data into the coverage database at all: the
  coverage report shows "Functional: n/a" and the per-bin breakdown is lost, even
  though the covergroup samples and scores correctly. Verified on this exact toolchain.
- The covergroup takes NO arguments. It reads the module's ports directly, which is why it
  may safely name them in its sampling event.
- Declare the module's ports as `input logic ...`, matching the widths in the port table.
- Include ONLY signals that appear in the port table. Never invent a signal.
- Every coverpoint and every cross MUST be labelled with a name followed by a colon:
      sig_a_cp : coverpoint sig_a {{ bins ... }}
      a_b_x    : cross sig_a_cp, sig_b_cp;
  An unlabelled coverpoint or cross is a fatal *E,ECGECL error in irun 15.20.
- Write bins that reflect the coverage requirement: individual values for narrow signals,
  and ranges (low / mid / high, plus boundary values) for wide ones so the bin count stays
  tractable -- see the 8-bit adder example for the range-bucketing idiom.
- Cross coverpoints wherever the requirement describes a joint condition.
- Use `wildcard bins` for don't-care patterns.
- DERIVE BIN BOUNDARIES FROM THE RTL, NOT FROM THE SIGNAL WIDTH. A signal's declared
  width is an upper bound on what it CAN hold, not on what the design ever PRODUCES.
  Read the RTL above and find the real limits: the constants it compares against, the
  values it assigns, the depth of any memory, the value reset forces. A bin holding a
  value the design cannot produce is a hole no stimulus can ever fill, and it caps
  coverage below 100% forever.
    * A counter of occupancy declared `[3:0]` but whose full flag is
      `assign full = (count == 4'd8);` never exceeds 8. Bins for 9..15 are dead, and
      so is a transition bin like `(14 => 15)`. The top bin is 8, and the transition
      to watch is `(7 => 8)`.
    * A value the RTL only ever assigns from a fixed set cannot take other values.
    * An output that is a registered copy of an input lags it by a cycle -- do not
      write a bin that requires them to change together.
  State the limit you found in a comment above the coverpoint, so the reasoning is
  checkable.
- PRUNE UNREACHABLE CROSS BINS. A cross of N coverpoints creates the full product of
  their bins, and any combination the design cannot physically produce becomes a hole
  that no stimulus can ever fill, capping coverage below 100% permanently. Before
  crossing, ask what the RTL forces:
    * A signal driven to a fixed value by reset cannot hold any other value while
      reset is active, so crossing it with the reset coverpoint yields dead bins.
      Remove them:  ignore_bins in_reset = binsof(rst_cp.asserted) &&
                                           !binsof(val_cp.reset_value);
    * An output that is a pure function of an input cannot take every combination
      with it -- prune the pairs the function cannot produce.
    * A state machine cannot be in two states at once, and cannot reach a state
      except through its legal predecessors.
  Prefer a small cross of two coverpoints you have reasoned about over a large cross
  of three or more that you have not.
- Use `illegal_bins` for values the design must never produce, so a violation is
  flagged rather than silently counted as a hole.
- Do NOT put `iff` on an individual bins statement; `iff` is legal only on a whole coverpoint.
- Transition bins must use CONSTANT values, e.g. `bins wrap = (15 => 0);`, and a coverpoint
  containing transition bins must NOT take part in a cross.
- QUALIFY CONDITIONAL TRANSITIONS WITH `iff`. A transition bin fires on the value change
  alone, no matter what caused it, so a bin can be credited for the wrong reason and the
  coverage number then overstates what was really exercised. If the requirement says a
  transition happens UNDER SOME CONDITION, put that condition on the coverpoint:
      count_wrap_cp : coverpoint count iff (en)  {{ bins wrap = (15 => 0); }}
      count_hold_cp : coverpoint count iff (!en) {{ bins hold = (0 => 0); }}
  Without the `iff (en)` above, an asynchronous reset driving the value from 15 to 0 would
  also count as a "wrap". Ask for every transition bin: what else in this design can produce
  this same value change? If the answer is anything, qualify it. `iff` on a coverpoint is
  legal; only `iff` on an individual bins statement is not.
- {_sampling_rule(design)}
- End the covergroup with `endgroup`.
- KEEP THE `final` BLOCK EXACTLY AS SHOWN, after the covergroup instance. It prints the
  functional coverage score straight out of the simulator at end of simulation. That
  reading is the pipeline's source of truth: it works whether or not the coverage
  database records covergroups, so do not remove, rename or reword those two $display
  lines -- their text is parsed.
- Follow all OUTPUT RULES and LANGUAGE RULES from the system prompt exactly.

Generate the coverage model now."""


def build_top_code(design: DesignInfo, cov_module_code: str = "") -> str:
    """Write the top level directly, without asking the model for it.

    build_top_prompt used to hand the model the entire finished file and say
    "Emit EXACTLY this structure, changing nothing but the comments" -- every
    line was already assembled here in Python. Spending an API call to have the
    file copied back bought nothing and gave the model a chance to alter it.

    One thing this does better than the prompt did: the coverage module's port
    list is read from the module the model actually wrote, rather than assumed
    to be every DUT port. A coverage model that covers a subset of the ports now
    gets connected correctly instead of failing elaboration.
    """
    inst = "intf"
    clk = design.clock

    cov_ports = [p["name"] for p in _parse_ports(cov_module_code)] if cov_module_code else []
    dut_names = {p["name"] for p in design.ports}
    cov_ports = [n for n in cov_ports if n in dut_names] or [p["name"] for p in design.ports]

    def conn(names) -> str:
        return ",\n".join(f"    .{n:<12}({inst}.{n})" for n in names)

    clock_block = ""
    if clk:
        clock_block = f"""
  // Top generates the clock. Nothing else drives it.
  initial begin
    {inst}.{clk} = 1'b0;
    forever #5 {inst}.{clk} = ~{inst}.{clk};
  end
"""

    tb_names = [p["name"] for p in design.ports]

    return f"""`timescale 1ns/1ps
// Generated by prompt_builder.build_top_code -- not by the LLM.
module {_top_name(design)};

  {_if_name(design)} {inst}();
{clock_block}
  {design.name} dut_inst (
{conn([p['name'] for p in design.ports])}
  );

  {_cov_name(design)} cov_inst (
{conn(cov_ports)}
  );

  {_tb_name(design)} tb_inst (
{conn(tb_names)}
  );

endmodule
"""


def build_top_prompt(design: DesignInfo) -> str:
    inst = "intf"
    conn = _port_conn(design, inst)
    clk = design.clock or "clk"
    return f"""Write the SystemVerilog top-level module `{_top_name(design)}` that wires the DUT,
the coverage module and the testbench together.

DUT: {design.name}
{_port_table(design)}

Emit EXACTLY this structure, changing nothing but the comments:

```systemverilog
`timescale 1ns/1ps
module {_top_name(design)};

  {_if_name(design)} {inst}();

  // Top generates the clock. Nothing else drives it.
  initial begin
    {inst}.{clk} = 1'b0;
    forever #5 {inst}.{clk} = ~{inst}.{clk};
  end

  {design.name} dut_inst (
{conn}
  );

  {_cov_name(design)} cov_inst (
{conn}
  );

  {_tb_name(design)} tb_inst (
{conn}
  );

endmodule
```

RULES:
- Do NOT use a virtual interface anywhere. irun 15.20 rejects assigning one
  hierarchically (*E,VIFCVU). Every connection is a plain named port connection.
- Do NOT drive {design.reset or 'any DUT input'} or any other DUT input here -- the
  testbench drives them through its output ports. Two drivers on one signal is a
  fatal elaboration error.
- Connect exactly the ports listed above, no more and no fewer.
- Follow all OUTPUT RULES and LANGUAGE RULES from the system prompt.

Generate the top module now."""


# =============================================================================
# Repair prompts (golden files that failed to compile)
# =============================================================================

# The interface is not in this map: it is written by build_interface_code(),
# so there is nothing for the model to repair. If it ever fails to compile,
# that is a bug in this file, not something to spend an API call on.
_REPAIR_SPEC = {
    "coverage_model": (_cov_name, build_coverage_model_prompt),
}


def build_repair_prompt(kind: str, design: DesignInfo, broken_code: str,
                        compile_errors: str) -> str:
    """Ask the LLM to fix a golden file that irun rejected, re-stating the
    original requirements so the fix can't drift away from the contract the
    other three files depend on."""
    name_fn, original_fn = _REPAIR_SPEC[kind]
    return f"""The SystemVerilog file `{name_fn(design)}.sv` below FAILED TO COMPILE under
Cadence irun 15.20. Fix the errors and regenerate the complete file.

BROKEN FILE:
```systemverilog
{broken_code}
```

COMPILER ERRORS FROM irun:
{compile_errors}

HOW TO READ THESE ERRORS:
- *E,ECGECL  -> a coverpoint or cross is missing its `label:` prefix.
- *E,ECGEGN  -> a covergroup is malformed above this line (often a bad bins statement
                earlier in the file); the reported line is where the parser gave up,
                so the real fault is usually EARLIER.
- *E,MISEXX  -> a declaration appears after a statement inside begin...end.
- Port connection errors -> a port was used that does not exist on the module.

Below are the ORIGINAL REQUIREMENTS this file must still satisfy. The fix must keep
every name and interface contract intact, because the other generated files depend on them.

{original_fn(design)}"""


def build_random_tb_prompt(design: DesignInfo) -> str:
    drivable = [x for x in design.inputs if x not in (design.clock, design.reset)]

    # A combinational DUT has no clock port, so there is nothing to wait on.
    # This used to fall back to a literal "clk", and the skeleton handed to the
    # model still said `@(posedge clk)` even while the header above it announced
    # "COMBINATIONAL design (no clock or reset port)" -- guaranteeing a
    # testbench that references a signal the design does not have.
    clk = design.clock
    advance = f"@(posedge {clk});" if clk else "#10;"
    never_drive = ", ".join(filter(None, [clk] + design.outputs)) or "the DUT outputs"

    if design.reset:
        reset_block = (f"    {design.reset} = 1'b0;\n"
                       f"    repeat (3) {advance}\n"
                       f"    {design.reset} = 1'b1;")
    elif clk:
        reset_block = "    // no reset port on this DUT"
    else:
        reset_block = "    // combinational DUT: no clock, no reset -- settle between vectors with #10"
    return f"""Write the SystemVerilog testbench module `{_tb_name(design)}` that drives the DUT.

DUT: {design.name}
{_port_table(design)}
{_clock_line(design)}
Signals you must drive: {', '.join(drivable) or '(none)'}

{_spec_line(design)}

REQUIRED SHAPE -- the port list is fixed, copy it exactly:

```systemverilog
`timescale 1ns/1ps
module {_tb_name(design)} (
{_tb_port_decl(design)}
);

  integer i;

  // Watchdog: never let the simulation hang.
  initial begin
    #200000;
    $display("TB: watchdog timeout");
    $finish;
  end

  initial begin
{reset_block}
    for (i = 0; i < 500; i = i + 1) begin
      // drive each signal with $urandom_range(0, <max for its width>)
      {advance}
    end
    // then directed sequences for whatever the coverage requirement names
    $finish;
  end

endmodule
```

RULES:
- The testbench is a plain module with PORTS. There is NO virtual interface and no
  `intf.` prefix anywhere -- refer to signals by their bare names.
- Drive ONLY the output ports ({', '.join(drivable) or 'none'}{', ' + design.reset if design.reset else ''}).
  Never assign to an input port such as {never_drive}.
- Plain procedural stimulus only: NO classes, NO `rand`, NO `randomize()`, NO
  constraints. Use `$urandom_range(min, max)`.
- Declare every variable at MODULE scope, before the initial blocks.
- Keep the watchdog block exactly as shown.
- Never write an unbounded `wait (sig == value);`. Use a bounded loop:
      i = 0;
      while (<sig> != <value> && i < 100) begin {advance} i = i + 1; end
- The testbench contains NO COVERAGE CODE AT ALL. Do not write `covergroup`,
  `coverpoint`, `cross`, `bins` or `endgroup` anywhere in it, and do not
  instantiate or reference the coverage module. Coverage lives in its own
  module which the top level wires up and which samples itself. The coverage
  requirement above tells you what stimulus to DRIVE, not what to measure.
- Comment only where the reason is not obvious from the code. Do NOT restate the
  coverage requirement in comments, do NOT paste uncovered-item text into comments,
  and do NOT explain why a line cannot be covered. One short line above a directed
  sequence saying what it targets is enough.
- NEVER write stimulus whose purpose is to execute the TESTBENCH's own code. Coverage
  is measured on the DESIGN. A branch inside the testbench that no stimulus reaches is
  not a coverage hole and must not be chased.
- Do NOT add `else $display("Warning: did not reach X")` after a bounded wait loop.
  Those else-branches are unreachable when the loop succeeds, they add nothing, and they
  become noise. If a value must be reached, drive it directly rather than waiting for it.
- End with `$finish;`.
- Follow all OUTPUT RULES and LANGUAGE RULES from the system prompt.

Generate the testbench now."""


def strip_sv_comments(code: str) -> str:
    """Remove // and /* */ comments, respecting string literals.

    Used only on the PREVIOUS testbench before it is quoted back into a
    refinement prompt. Comments are worth keeping in generated code -- they are
    the model reasoning aloud, and the reasoning tends to be better when it is
    written down. But echoing them back costs input tokens on every later
    iteration and teaches nothing: the model already knows why it wrote what it
    wrote. Measured on the counter's testbench, comments were 53% of the file.
    """
    out = []
    i, n = 0, len(code)
    in_str = False
    while i < n:
        c = code[i]
        if in_str:
            out.append(c)
            if c == "\\" and i + 1 < n:      # escaped char inside a string
                out.append(code[i + 1]); i += 2; continue
            if c == '"':
                in_str = False
            i += 1
        elif c == '"':
            in_str = True; out.append(c); i += 1
        elif code.startswith("//", i):
            while i < n and code[i] != "\n":
                i += 1
        elif code.startswith("/*", i):
            end = code.find("*/", i + 2)
            i = n if end == -1 else end + 2
        else:
            out.append(c); i += 1

    # Drop lines that held nothing but a comment, and trailing whitespace.
    kept = [ln.rstrip() for ln in "".join(out).splitlines()]
    return "\n".join(ln for ln in kept if ln.strip())


def _refinement_context(design: DesignInfo, prev_tb: str, prev_summary: str,
                        trimmed_detail: str, prev_cov: float, prev_err: str,
                        cov_model: str = "") -> str:
    err_block = (
        f"\nSIMULATION ERRORS FROM PREVIOUS ATTEMPT (fix these first if present):\n{prev_err}\n"
        if prev_err else ""
    )

    # When IMC cannot name the empty bins, the model has a score and nothing to
    # aim at. Give it the covergroup itself: the bins are all right there, so it
    # can work out which ones its own stimulus would never have reached. That is
    # a weaker signal than a real hole list, but it is a signal.
    from coverage_parser import detail_is_useless
    holes_block = f"""UNCOVERED ITEMS:
{trimmed_detail}
"""
    if detail_is_useless(trimmed_detail) and cov_model.strip():
        holes_block += f"""
THE COVERAGE MODEL BEING SCORED (no hole list is available, so work it out from here):
```systemverilog
{cov_model}
```
Walk each coverpoint and each cross above and ask: would the previous testbench
ever have produced that value, that transition, or that combination? The bins it
could not reach are where the missing {100 - prev_cov:.2f}% is. Target those.
"""

    return f"""DUT MODULE: {design.name}
Clock: {design.clock}   Reset: {design.reset}
{_spec_line(design)}

PREVIOUS TESTBENCH (comments stripped -- they were yours, you do not need them back):
```systemverilog
{strip_sv_comments(prev_tb)}
```

PREVIOUS COVERAGE SUMMARY:
{prev_summary}

{holes_block}{err_block}"""


def build_constrained_tb_prompt(design: DesignInfo, prev_tb: str, prev_summary: str,
                                trimmed_detail: str, prev_cov: float, prev_err: str,
                                cov_model: str = "") -> str:
    context = _refinement_context(design, prev_tb, prev_summary, trimmed_detail,
                                  prev_cov, prev_err, cov_model)
    return f"""Revise the SystemVerilog testbench below to raise functional coverage above its
current {prev_cov:.2f}%, by biasing constrained-random stimulus toward the uncovered bins listed.

{context}
REQUIREMENTS:
- Keep the module name `{_tb_name(design)}` and its PORT LIST exactly as in the previous
  version -- the top module connects to those ports by name. No virtual interface, no
  `intf.` prefix, no coverage handle.
- Keep the plain procedural style: NO classes, NO `rand`, NO `randomize()`, NO constraints.
  Bias stimulus by narrowing the `$urandom_range()` bounds, by weighting with an
  if/else on `$urandom_range(0,99)`, or by adding explicit directed sequences.
- Do not remove stimulus that was working -- only add to it.
- Follow all OUTPUT RULES and LANGUAGE RULES from the system prompt exactly.

Generate the revised testbench now."""


def build_directed_tb_prompt(design: DesignInfo, prev_tb: str, prev_summary: str,
                             trimmed_detail: str, prev_cov: float, iteration: int,
                             prev_err: str, cov_model: str = "") -> str:
    context = _refinement_context(design, prev_tb, prev_summary, trimmed_detail,
                                  prev_cov, prev_err, cov_model)
    return f"""Constrained-random stimulus has plateaued at {prev_cov:.2f}% coverage after
{iteration} iterations. Switch strategy: write DETERMINISTIC, DIRECTED sequences that
individually target each uncovered item below, appended after the existing random phase.

{context}
REQUIREMENTS:
- Keep the module name `{_tb_name(design)}` and its PORT LIST exactly as in the previous
  version -- the top module connects to those ports by name. No virtual interface, no
  `intf.` prefix, no coverage handle.
- Keep the existing random phase, then append a directed phase: for EACH uncovered item
  listed above, drive the exact sequence of values needed to hit it, back-to-back on
  consecutive clock edges. Plain procedural code only -- no classes or constraints.
- Do not guess at items not listed -- only target what's in the uncovered list.
- Follow all OUTPUT RULES and LANGUAGE RULES from the system prompt exactly.

Generate the revised testbench now."""
