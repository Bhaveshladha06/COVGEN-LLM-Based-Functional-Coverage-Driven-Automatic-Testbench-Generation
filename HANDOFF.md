# Project Handoff — LLM Coverage-Driven Testbench Generation

Give this file **and `EVERYTHING.zip`** to a new assistant. It contains the
project goal, the exact environment, every tool quirk discovered the hard way,
and the current open questions.

---

## 1. What this project is

**BTP at IIIT Delhi, NDCL Lab.** Student: Bhavesh (beginner — wants
copy-pasteable commands, not theory). One teammate. Advisor: Dr. Sneh Saurabh.

**Goal:** From an English coverage requirement + a Verilog RTL file,
automatically generate a SystemVerilog **functional coverage model** and a
**testbench**, simulate them, read the coverage, and iterate on the testbench
until coverage holes close.

**Lineage:** A senior team built *Assergent*
(`github.com/Shivam-Shukla-GIT/Assergent-Agents-for-Automated-Assertion-Mining-in-VLSI-Systems`)
which did the same thing for **SVA assertions** with JasperGold. This project
reuses that architecture for **coverage models + testbenches** with
irun/IMC. The workflow diagram is identical:

```
English coverage requirement ─┐
                              ├─► FAISS best-match ─► Prompt Gen 1 ─► LLM ─► Coverage Model
RTL ──────────────────────────┘                                                    │
Knowledge base (English + RTL + coverage model) ────────────────────────────────────┤
                                                                                    ▼
                         ┌──────────────────────────────► irun simulate ─► IMC ─► coverage holes?
                         │                                       ▲                     │ yes
                    Prompt Gen 2 ─► LLM ─► Testbench ────────────┘                     │
                         ▲                                                             │
                         └─────────────────────── max iterations? ◄────────────────────┘
```

RAG retrieval feeds **only** the coverage-model prompt (Phase 1). The
testbench refinement loop (Phase 2) is driven by IMC coverage holes, not by
retrieval.

---

## 2. Environment (all verified working)

| Item | Value |
|---|---|
| Server | `edatools-server1.iiitd.edu.in`, RHEL 7.9, x86_64, glibc 2.17 |
| Project dir | `~/Desktop/BTP/Coverage_TB` |
| Python | conda env `assergent`, Python 3.9 (miniforge3) |
| Simulator | `/cadence/INCISIVE152/tools.lnx86/bin/irun` (Incisive **15.20-s084**) |
| Coverage tool | `/cadence/INCISIVE152/tools.lnx86/bin/imc` |
| **Licence** | `export CDS_LIC_FILE='5280@14.139.1.126'` ← **essential** |
| LLM | Gemini `gemini-2.5-flash` via REST, key in `$GEMINI_API_KEY` |

### Session setup (every new terminal)

```bash
source "$HOME/miniforge3/etc/profile.d/conda.sh"
conda activate assergent
export CDS_LIC_FILE='5280@14.139.1.126'
export GEMINI_API_KEY='...'
export PATH=/cadence/INCISIVE152/tools.lnx86/bin:$PATH
```

Installed packages: numpy 1.26.4, torch 2.2.2 (CPU), transformers 4.36.0,
sentence-transformers 2.7.0, faiss-cpu 1.7.4, requests, scikit-learn, pyyaml, tqdm.

Notes:
- Gemini free tier **rate-limits (429)** and sometimes returns **503**. The
  client retries after 65 s. If persistent, switch `GEMINI_MODEL` to
  `gemini-2.0-flash` in `config.py`.
- Other Cadence installs exist (`XCELIUM2003`, `VMANAGER2003`) — **use
  INCISIVE152**, the prompts are tuned to its quirks.
- `/cadence/cshrc` is the lab's setup script (tcsh syntax) and is where the
  licence address came from.

---

## 3. Architecture — 5 files compiled per run

```
counter.v              ← user's RTL (input, never modified)
counter_if.sv          ← interface: passive signal bundle          [GOLDEN, cached]
counter_coverage.sv    ← self-sampling coverage MODULE             [GOLDEN, cached]
top_counter.sv         ← wires everything by named ports           [GOLDEN, cached]
tb_counter.sv          ← procedural stimulus                       [REGENERATED each iteration]
```

**Golden files** are generated once, compile-checked, and cached next to the
RTL. `--regen_cov` forces regeneration. Only the testbench iterates.

### The shapes that actually work on irun 15.20

Coverage model — a **module** whose ports are the DUT signals, containing an
**argument-free** covergroup that samples itself:

```systemverilog
`timescale 1ns/1ps
module counter_coverage (input logic clk, rst_n, en, input logic [3:0] count);
  covergroup counter_coverage_cg @(posedge clk);
    count_cp : coverpoint count { bins zero = {0}; ... }
    en_cp    : coverpoint en    { bins off = {0}; bins on = {1}; }
    c_x      : cross count_cp, en_cp;
  endgroup
  counter_coverage_cg cg_inst = new();
endmodule
```

Testbench — a **plain module with ports**, no classes, no virtual interface:

```systemverilog
module tb_counter (
  input  logic clk, input logic [3:0] count,   // DUT outputs + clock
  output logic rst_n, output logic en          // DUT inputs
);
  integer i;
  initial begin #200000; $display("watchdog"); $finish; end   // watchdog
  initial begin
    rst_n = 0; repeat (3) @(posedge clk); rst_n = 1;
    for (i = 0; i < 500; i = i + 1) begin ... @(posedge clk); end
    $finish;
  end
endmodule
```

Top — one interface instance, everything connected by **named ports**:

```systemverilog
module top_counter;
  counter_if intf();
  initial begin intf.clk = 0; forever #5 intf.clk = ~intf.clk; end
  counter          dut_inst (.clk(intf.clk), .rst_n(intf.rst_n), ...);
  counter_coverage cov_inst (.clk(intf.clk), ...);
  tb_counter       tb_inst  (.clk(intf.clk), ...);
endmodule
```

Both port lists (`_tb_port_decl`, `_port_conn` in `prompt_builder.py`) are
**generated by Python from the parsed RTL**, not by the LLM, so they cannot
disagree.

---

## 4. irun 15.20 rules — every one learned from a real failure

**Do not relax these.** Each corresponds to a run that failed.

| Error code | Rule |
|---|---|
| `*E,UPITEM` | A covergroup **must** be inside a module. A bare covergroup at file scope does not compile. |
| `*E,CBYREF` | `ref` covergroup arguments are rejected at compilation-unit scope. |
| `*E,EFASAM` | A covergroup may **not** name its own argument in its `@(...)` sampling event. Solution used: module-scoped covergroups take **no arguments** and read module ports, so `@(posedge clk)` and `@(a or b)` are both legal. |
| `*E,ECGECL` | **Every** coverpoint and **every** cross must be labelled: `name : coverpoint sig {...}`. |
| `*E,ECGEGN` | Reported where the parser gave up; the real fault is usually **earlier** in the covergroup. |
| `*E,ECBNOD` | `ignore_bins X = default;` is illegal **inside a cross that defines its own bins** (fine on a plain coverpoint). |
| `*E,FNDKWD` | `small`, `medium`, `large` are Verilog charge-strength **keywords** — never use as bin names. |
| — | `iff` belongs on a coverpoint, never on a `bins` statement. |
| — | Transition bins must use **constants**: `bins wrap = (15 => 0);`. Never variables. |
| — | A coverpoint containing transition bins must **not** appear in a cross. |
| `*E,VIFCVU` | **No virtual interfaces.** irun 15.2 rejects hierarchical assignment (`tb_inst.intf = if_inst;`). This is why the testbench is a ported module. |
| `*E,MISEXX` | All declarations at the **top** of a `begin...end` block, before any statement. |
| `*F,CUMSTS` | RTL often has no `` `timescale ``; **every** irun invocation must pass `-timescale 1ns/1ps` (`config.TIMESCALE`). |
| `*E,CUVPOM` | Port name mismatch between modules — why port lists are Python-generated. |
| `*E,FILEMIS` | irun runs with `cwd=sim_work`, so **all source paths must be absolute**. |
| `*F,NOLICN` | Simulation licence. `ncvlog` and `ncsim` use **different** licence features; compiling can succeed while simulating fails. |

Also avoid in generated code: classes, `rand`, `randomize()`, constraints
(they caused many failures — plain `$urandom_range()` is used instead);
`inside` operator; packages/imports.

---

## 5. Files in the project

| File | Role |
|---|---|
| `main.py` | Orchestrator. Phase 1 (golden files + inline compile/repair), Phase 2 (iteration loop). |
| `prompt_builder.py` | RTL parsing (`parse_design`) + all prompts. Port-list helpers. |
| `retriever.py` | FAISS over `knowledge_base/coverage_kb.json`. Cosine via `IndexFlatIP` on normalised vectors. |
| `gemini_client.py` | Gemini REST client. `SYSTEM_PROMPT` holds the global SV rules. |
| `simulator.py` | Runs `irun`. Absolute paths, `-covdut`, coverage flags. |
| `imc_runner.py` | Runs `imc` via TCL, produces summary + detail reports. |
| `coverage_parser.py` | Parses IMC summary; `filter_detail_to_dut()` strips harness sections. |
| `syntax_check.py` | Compile/elaborate a file set with irun. No Gemini cost. |
| `config.py` | All settings. |
| `kb_tool.py` | Inspect/curate the knowledge base (`--list --query --for-design --add --verify`). |
| `kb_validate.py` | **Text-only** structural lint of KB entries (no simulator). |
| `kb_compile_check.py` | **Really compiles** every KB entry with irun; `--apply` marks them verified. |
| `seed/` | Source for the 87 KB entries; `python seed/build_kb.py` rebuilds the JSON. |
| `designs/` | `<name>/<name>.v` + `<name>.spec.txt` (the English requirement). |

### Knowledge base

`knowledge_base/coverage_kb.json`, **87 entries**, schema:

```json
{ "id": "...", "english_requirement": "...", "coverage_model": "...",
  "rtl": "...", "design_context": {"module":"","data_width":0,"type":""},
  "signals": [], "verified": true, "provenance": "...", "category": "", "notes": "" }
```

- `provenance`: `curated_seed` (6, from the project's PDF) | `hand_authored`
  (81, written for this project) | `auto` (recorded from real runs).
- `verified` means **it compiled in a real irun run** — nothing sets it on
  inspection alone. `auto` entries are withheld from retrieval until verified.
  This guard exists because a earlier bug let uncompiled models be retrieved as
  "known-good examples", and the LLM imitated their errors.
- All 87 pass `kb_compile_check.py` on the real tool.
- Categories: 24 combinational, 22 sequential, 12 memory, 23 control, 6 curated.
- Retrieval: top-1, τ = 0.5. Measured: adder16→adder8 = 0.882, counter→counter_up8
  = 0.842; unrelated designs sit at 0.2–0.42, so 0.5 is a clean gate.

---

## 6. Bug history (do not regress these)

1. **`*E,FILEMIS`** — relative paths passed to irun while `cwd=sim_work`. Fixed: resolve to absolute.
2. **Port hallucination** — `build_top_prompt` said "connect every DUT port" without listing them; the LLM invented `load`, `load_val`, `count_out`. Fixed: embed the exact port table and instantiation.
3. **RAG self-poisoning** — coverage models were added to the KB at *generation* time, before compiling. Broken models were then retrieved as good examples and their errors imitated; the loop stalled at 0% with identical errors each iteration. Fixed: `verified`/`provenance` gating.
4. **Port parser dropped signals** — `input a, b, sel;` yielded only `a`. Fixed: split comma-separated names, share the width.
5. **Phantom clocks** — clock/reset defaulted to literal `clk`/`rst_n` even for combinational designs. Fixed: empty string ⇒ treated as combinational.
6. **`*E,EFASAM`** — 27 of 87 KB entries used covergroup args in the sampling event. Note: **three of the six original PDF examples (mux2, mux4, decoder2to4) do not compile on this tool** — worth telling the seniors.
7. **`*E,VIFCVU`** — the virtual-interface architecture is impossible here. Fixed: ported testbench.
8. **Missing licence** — `CDS_LIC_FILE` unset. Found in `/cadence/cshrc`.
9. **`*F,CUMSTS` phantom** — `syntax_check` didn't pass `-timescale` while the real run did, so phase 1 failed a file that was actually correct and burned two repair calls. Fixed: shared `config.TIMESCALE`.
10. **Coverage measured the testbench** — see §7.
11. **Functional coverage was never in the database** — reported as `n/a`, and
    `coverage_parser` read the row's last percentage as 100% *overall*, so a run
    with zero functional coverage was reported as a complete success. My first
    diagnosis (`-covdut` scoping) was wrong; see §7. Fixed for real by having the
    coverage model print its own score. Original wording of the wrong diagnosis:
    **`-covdut` hid the covergroups** — the fix for #10 excluded the `<dut>_coverage` module from the coverage scope, so IMC reported `Functional Average: n/a` and `coverage_parser` read the row's last percentage as 100% *overall*. A run with zero functional coverage was reported as a complete success. See §7.

Two post-processors in `main.py` (`_fix_clock_refs`, `_fix_top_module`) are now
**deliberate no-ops**; they rewrote code for the old virtual-interface design
and would corrupt files today. Kept only so call sites stay stable.

---

## 7. Current state — as of the last run

**The pipeline works end to end.** Last full run:

```
PHASE 1: interface / coverage_model / top_module — all "compiles cleanly"
FAISS  : counter_up8_8bit_001 (8-bit up counter) similarity=0.842
Iter 0 (random)      : 0.00% -> 86.02%
Iter 1 (constrained) : 86.02% -> 86.41%
Iter 2 (directed)    : 86.41% -> 86.67%
Knowledge base updated (verified=True)   ← first auto entry, corpus 88
```

**Why it stopped at 86.67%, diagnosed from `imc_detail.rpt`:** all 7 uncovered
blocks and all 7 uncovered expressions were in `top_counter.tb_inst` — **the
testbench**. The DUT had zero uncovered items and the covergroup section was
empty, i.e. functional coverage was already complete. `-coverage all` was
scoring the testbench's watchdog, its `else $display("did not reach X")`
branches and its `i < 100` loop guards — all unreachable by construction.

Worse, those items reached the refinement prompt, and the generated testbench
contains comments showing the model writing stimulus aimed at covering **its
own error handlers**. That is why iterations 1 and 2 gained only 0.39% and 0.26%.

### The `-covdut` fix (applied, and then found to be half-wrong)

- `simulator.py` passes **`-covdut <dut_module>`** so only the design is scored.
  Toggle: `config.COV_DUT_ONLY`.
- `coverage_parser.filter_detail_to_dut()` keeps only the DUT's report sections.
- The loop stops when the DUT has no holes, printing `[DONE] DUT FULLY COVERED`.
- Coverage prompt now requires pruning **unreachable cross bins** and qualifying
  conditional transition bins with `iff`.

**Result: counter reached "100%". That number was wrong.** The real
`imc_summary.rpt` from that run:

```
name     Overall Average  Overall Covered  Code Average  Code Covered     Fsm  Functional Average  Functional Covered
counter  100.00%          100.00% (12/12)  100.00%       100.00% (12/12)  n/a  n/a                 n/a
```

Read it carefully:

- Only one row — `-covdut` did scope the report to the DUT, so bug #10 is fixed.
- 12/12 code coverage items — genuinely covered.
- **`Functional Average: n/a`.** Not 100%. Not 0%. *Not measured.*

`-covdut <module>` restricts coverage to that module **and its submodules**.
The covergroups live in `<dut>_coverage`, which is instantiated in `top_<dut>`
as a **sibling** of the DUT, not inside it. So the covergroups fell outside the
coverage scope and were never scored. The pipeline then reported 100% —
code coverage over 12 items — and stopped.

`coverage_parser.parse_summary` made it worse: its regex did not match that row
(the line ends in `n/a`, not `%`), so it fell back to "last percentage anywhere
in the text" and returned 100.0. Nothing in the run said functional coverage
was missing.

### The functional-coverage fix (current)

1. **`simulator.py`** passes `-covdut` **twice** — `<dut>` and `<dut>_coverage` —
   putting the covergroups back in scope. Toggle:
   `config.COV_DUT_INCLUDE_COVERAGE_MODULE`.
2. **`coverage_parser.py`** was rewritten to parse the real per-DUT table (the
   layout above, now confirmed against an actual report) as well as the old
   per-metric layout. A functional cell of `n/a` yields `functional=None` —
   deliberately not `0.0` and never `100.0`. When IMC emits one row per scope,
   the columns are recombined across rows.
3. **`imc_runner.py`** asks IMC separately for a covergroup-scoped report
   (`coverage_functional.rpt`), as an independent check on the summary. IMC
   option spellings vary across 15.x builds, so the TCL tries five known forms
   inside `catch` and logs which one was accepted — grep `imc.log` for
   `FUNCTIONAL-REPORT TRY`. `generate_reports()` now returns a **3-tuple**.
4. **`main.py`** optimises functional coverage when it is available, falls back
   to code coverage only with a loud warning, prints `[BLOCKED] NO FUNCTIONAL
   COVERAGE MEASURED` instead of `[DONE]`, exits non-zero, and records
   `coverage_metric` / `functional_measured` in `summary.json`.
5. **KB admission now requires functional coverage.** A coverage model whose
   covergroups were never scored can sit at 100% code coverage and still be
   worthless; admitting it as `verified=True` is exactly how the corpus poisoned
   itself in bug #3.

### Run 2: the `-covdut` theory was wrong

Repeated `-covdut` **was accepted** — the summary now has two rows:

```
counter           100.00%  100.00% (12/12)  ...  Functional: n/a
counter_coverage  100.00%  100.00% (7/7)    ...  Functional: n/a
```

The coverage module was inside the scope, and functional coverage was **still
`n/a`**. So the scope was never the cause. Three further facts from that run:

- The detail report's `Uncovered CoverGroup Detail Report, Instance Based`
  section is present and **empty** — not "all covered", but no covergroup data.
- `report -summary -metrics functional` was accepted by IMC (only one
  `FUNCTIONAL-REPORT TRY` line in `imc.log`, so the first form did not throw)
  and wrote **0 bytes**.
- The 7/7 on `counter_coverage` is its *code* coverage, not its covergroups.

Conclusion: **no covergroup data reaches the coverage database at all** on this
irun/IMC build, even though the covergroup compiles, is instantiated, and samples
on `@(posedge clk)`. The likely cause is that `-coverage all` on this build does
not enable functional coverage collection, but that is not confirmed. Run
`irun -helpargs coverage` on the server to see the accepted values;
`config.COVERAGE_FLAGS` exists so the answer is a one-line change.

### The fix that does not depend on the database

The coverage model now ends with:

```systemverilog
  final begin
    $display("SV_FUNCTIONAL_COVERAGE: %0.4f", $get_coverage());
    $display("SV_CG_INST_COVERAGE: %0.4f", cg_inst.get_inst_coverage());
  end
```

This is the simulator's own covergroup engine reporting its score at end of
simulation — it cannot be affected by `-coverage` flags, `-covdut` scoping or
IMC report syntax. `coverage_parser.parse_sv_functional()` reads it out of the
irun output and `main.py` prefers it over anything IMC says, warning if the two
disagree. `prompt_builder` requires the block verbatim and says its text is
parsed. **Cached coverage models predate this, so `--regen_cov` is required.**

Also fixed in the same pass: `dut_clean` (no uncovered *code* items in the DUT)
no longer stops the loop on its own. Code coverage saturates on a small design
long before the covergroup bins are full, so it now also requires functional
coverage to have reached the threshold — otherwise the loop would have declared
`[DONE]` at whatever functional coverage iteration 0 happened to reach.

**What is still lost:** IMC's per-bin covergroup detail, which is what told the
refinement loop *which* bins are empty. Until `COVERAGE_FLAGS` is corrected the
model is told its score but not which bins are missing, so refinement iterations
are weaker than they should be. Fixing that flag is the highest-value next step.

---

### Run 3: functional coverage works — counter 100%, fifo 90.18%

`grep SV_FUNCTIONAL_COVERAGE`:

```
run_20260822_200137/iter_00  100.0000   (counter)
run_20260822_200434/iter_01   90.1843   (fifo)
```

That is the first genuine functional coverage this project has produced. Three
problems the FIFO run exposed, all now fixed.

**1. The coverage model never saw the RTL.** `build_coverage_model_prompt` sent
the port table and the English spec, but not the design. So on the FIFO the model
binned `count` off its declared width:

```systemverilog
bins full_c = {15};                          // count never exceeds 8
bins to_full = (14 => 15);                   // never happens
```

The RTL says `assign full = (count == 4'd8);` and `reg [7:0] mem [0:7]` — depth 8.
Occupancy tops out at 8; every bin above it is dead. That is the missing 9.82%,
and no stimulus could ever have closed it. The prompt has always told the model
to prune unreachable bins; it just never gave it the information to do so. The
RTL is now in the prompt (capped by `config.RTL_MAX_PROMPT_CHARS`) with a rule
that bin boundaries come from what the RTL produces, not from the signal width.

**2. Dependency errors were blamed on the wrong file.** `fifo_if.sv` failed to
parse, and because every syntax check compiles the interface as a dependency,
the coverage model and the top module were each told *they* had failed and sent
for repair — against errors in a file they did not contain. Nine Gemini calls for
one broken interface, with prompts ballooning to 15.8k chars. `_gen_checked` now
keeps only the error lines naming the file under repair and stops if none do.

**3. The interface was LLM-generated for no reason.** It is one `logic` per port
plus two mirrored modports — entirely mechanical, entirely derivable from the
port table that is already parsed. `prompt_builder.build_interface_code()` now
writes it directly. One less API call per design, and that failure mode is gone.
`repair_golden_files` rewrites it from the port table rather than asking the
model, and `interface` was removed from `_REPAIR_SPEC`.

Measured on a stubbed run where every compile fails with a dependency error:
9 Gemini calls before, 3 after.

---

### Run 4: three more defects found by tracing the flow

**1. The top module was being copied, not written.** `build_top_prompt` handed
the model the complete finished file and said "Emit EXACTLY this structure,
changing nothing but the comments" -- every line was already assembled in Python
from the port table. An API call to have a template echoed back.
`prompt_builder.build_top_code()` now writes it, and does one thing the prompt
could not: it reads the coverage module's ACTUAL port list from the file the
model wrote, so a coverage model covering a subset of ports is wired correctly
instead of failing elaboration. `top_module` is out of `_REPAIR_SPEC`;
`repair_golden_files` rewrites it like the interface.

**Phase 1 is now one API call** (the coverage model). Interface and top are
generated locally. On the dependency-error test: 9 calls originally, 2 now.

**2. The combinational testbench prompt referenced a clock that does not exist.**
`clk = design.clock or "clk"` fell back to a literal `clk`, and the skeleton the
model was told to copy still said `@(posedge clk)` -- directly under a header
announcing "COMBINATIONAL design (no clock or reset port)". Any mux2 run would
have produced a testbench referencing a phantom signal. Combinational designs now
advance with `#10` and the word `clk` does not appear in the prompt at all.
**This is why mux2 never worked; it was never going to.**

**3. The generated testbench was chasing its own code coverage.** The counter's
FINAL_tb_counter.sv contains stimulus, and comments, aimed at covering the
testbench's own `else` branch and its watchdog `#200000`. Two new rules forbid
writing stimulus to execute testbench code, and forbid the
`else $display("did not reach X")` pattern that manufactures dead branches which
then show up as uncovered items.

### RTL parser: tested, mostly fine

`_parse_ports` was stress-tested against 10 declaration styles. Nine pass: ANSI,
non-ANSI with shared widths, parameterised widths, `inout`, comments between
ports, `signed`, ports whose names contain "input", multi-line port lists, and
declarations after `localparam`. One fails: **2-D packed dimensions**
(`input [3:0][7:0] mat`) drop the port entirely. Parameterised widths parse as
text (`[W-1:0]`), which is correct but leaves the coverage model unable to know
the numeric width.

Not worth replacing with a real parser (pyslang/pyverilog) at this scale. The
cheaper guard is to cross-check the parsed port list against elaboration.

---

### manual_test/ confirmed both halves, on real hardware

Run on the server, 22 Aug:

```
SV_FUNCTIONAL_COVERAGE: 87.5000        <- simulator: works
tiny             ... Functional: n/a   <- IMC: no data
tiny_coverage    ... Functional: n/a
Uncovered CoverGroup Detail Report --> section present, EMPTY
```

**87.5% is exactly right**, and the arithmetic proves the number is a real
measurement rather than anything hardcoded:

| coverpoint | bins | hit | score |
|---|---|---|---|
| `count_cp` | 0,1,2,3 | 0,1,2 (testbench stops at 2) | 75% |
| `en_cp` | 0,1 | both | 100% |

A covergroup's score is the **average of its coverpoints** (IEEE 1800), not
bins-hit/total-bins. average(75,100) = 87.5%. Bins-hit/total would have been
5/6 = 83.33%. The script's original "expect 75%" comment was wrong -- it forgot
`en_cp` contributes -- and has been corrected.

The script's covergroup check was also too loose: it grepped the whole detail
report for "Type name:", which uncovered *code* items also produce, so it
printed "YES -- IMC has per-item data" while the CoverGroup section was empty.
It now looks only inside the CoverGroup section.

Confirmed conclusion: the simulator scores covergroups correctly; the coverage
database does not receive them. `tiny` reported 80% (8/10) and `tiny_coverage`
60% (3/5) **code** coverage in the same run, so the database and report are
working -- it is specifically covergroup data that never arrives.

---

### The per-coverpoint API compiles -- the probe was run wrong

`cg_inst.<coverpoint>.get_coverage()` **elaborated and ran with no errors** on
irun 15.20. It returned 0 only because the probe's irun command omitted the
coverage flags:

```
ncsim: *N,COVNSM: Sampling of covergroup type "tiny_cg" is not enabled.
As a result, coverage methods get_coverage(), get_inst_coverage(),
get_hit_count(), and get_inst_hit_count() will return 0 coverage.
```

Two things follow, and both matter:

1. **`-coverage all` DOES enable covergroup sampling.** TEST 1 passes those
   flags and gets a correct 87.5%; the probe omitted them and got 0 with this
   warning. So the flag is not the reason IMC's database has no covergroup data
   -- sampling is on and scoring is right; only the *recording* into the
   database is missing. Chasing a different `-coverage` value is unlikely to
   help.
2. **The syntax is supported.** No `*E`. The probe now passes the coverage
   flags and should report count_cp=75%, en_cp=100%, total=87.5%.

If that confirms, per-coverpoint scores replace IMC entirely for the refinement
loop's hole list, and `COVERAGE_FLAGS`/`imc_runner` stop being on the critical
path.

`irun -helpargs coverage` is also not a valid spelling -- irun treated
"coverage" as a source file ("Files on the command line ... coverage unknown").

---

### Is `n/a` just because we write no SVA? No.

A reasonable theory: IMC's "Functional" column might mean *assertions*, and since
this project writes covergroups rather than SVA, `n/a` would be correct and
expected. IMC's own detail report rules it out -- it prints these sections:

```
Uncovered Assertion Detail Report, Instance Based
Uncovered CoverGroup Detail Report, Instance Based
```

Assertions and covergroups get **separate sections**. The CoverGroup section is
printed and empty. If the theory held, that section would still be populated
from our covergroup regardless of the summary column's meaning. It is not, so
covergroup data is genuinely absent from the database.

### SOLVED: `option.per_instance = 1` was the whole problem

A covergroup's results can be kept merged across all instances of the type, or
kept per instance. Some simulators only write *per-instance* results into the
coverage database and record nothing when the option is left at its default.
That is a plausible and cheap explanation that has not been tried.

**Confirmed on the server, 23 Aug.** With that one line added, the same design,
same flags, same IMC:

```
tiny_coverage_pi  ... Functional Average: 87.50%   Functional Covered: 83.33% (5/6)

Uncovered CoverGroup Detail Report, Instance Based
  Instance name: tiny_coverage_pi
  Number of uncovered cover bins: 1 of 6
  cg_inst          87.50%, 83.33% (5/6)   covergroup tiny_cg @(posedge clk);
  |--count_cp      75.00% (3/4)           count_cp : coverpoint count {
  | |--three        0.00% (0/1)           bins three = {2'd3};
```

IMC names the exact empty bin. That is the per-bin hole list the refinement
loop never had, and every earlier theory -- `-covdut` scoping, the `-coverage`
flag value, IMC report syntax, "Functional means SVA" -- was wrong. The cause
was a missing covergroup option.

Experiment A also passed: `cg_inst.<coverpoint>.get_coverage()` returns
count_cp=75, en_cp=100, total=87.5. Both routes work; the pipeline keeps the
simulator printout as its score (it cannot be affected by tool flags) and uses
IMC's per-bin list to tell the model which bins to target.

**Applied to the pipeline:**
- `prompt_builder.ensure_per_instance()` inserts the line into every covergroup
  that lacks it, applied on generation AND on repair. The prompt asks for it
  too, but a missing line fails *silently* -- the model still compiles, still
  samples, and quietly costs the bin detail -- so it is enforced in Python
  rather than trusted to the model.
- The covergroup template and a hard rule both carry it.
- `manual_test/tiny_coverage.sv` now has it, so TESTS 1 and 2 both pass.

Verified: `parse_summary` picks 87.5 out of the two-row summary as the headline
(not the meaningless 76.9 overall average), and `filter_detail_to_dut` keeps the
`counter_coverage` covergroup section while dropping testbench sections.

---

### Combinational covergroups had a sampling race

`_sampling_rule` told the model to write, for a design with no clock:

    covergroup mux2_coverage_cg @(a or b or sel);

That event fires in the same simulation region as the DUT's continuous
assignments, and the LRM does not order the two. So an output coverpoint could
sample the **previous** vector's result. Every bin still gets hit eventually, so
the score still reads 100% -- the error is invisible in the percentage and shows
up only as bins credited to the wrong input vector.

mux2 and adder16 both reported 100% under this rule. Their numbers are not
trustworthy and both should be re-run.

The docstring above the function had said all along that a combinational
covergroup "must carry no sampling event at all and be sampled by an explicit
.sample() call" -- the implementation had drifted from it. Now fixed to match:

    covergroup <name>_cg;                 // no event
      option.per_instance = 1;
      ...
    endgroup
    <name>_cg cg_inst = new();

    always @(a or b or sel) begin
      #1 cg_inst.sample();                // after the outputs settle
    end

Sequential designs are unaffected -- `@(posedge clk)` samples in a region where
the DUT's non-blocking assignments have not yet taken effect, which is the
conventional and correct behaviour.

`adder8_demo/` is a hand-written five-file example in the pipeline's exact
shape, with both this and the per_instance detail commented in place.

---

## 8. Open items for the next session

1. **Find the irun flag that puts covergroups in the coverage database.**
   `irun -helpargs coverage` lists the accepted values; put the right one in
   `config.COVERAGE_FLAGS`. Functional coverage is already measured without this
   (the `final` block), so this is not blocking — but it is what restores IMC's
   per-bin detail, and without that the refinement loop is guessing at which
   bins to target. Verify with `grep -A5 CoverGroup imc_detail.rpt`: bins should
   be listed there.
   - `-covdut` is NOT the problem — repeated `-covdut` works and made no
     difference. Do not spend time on `bind` or on `cov.ccf` for this.
2. **`imc_summary.rpt` layout is now confirmed** (see §7) and `parse_summary`
   parses it directly. The old "last percentage in the text" fallback survives
   only for unrecognised layouts.
3. **Directed strategy for iteration ≥ 2** exists but has only been exercised once.
4. **`designs/mux2` and `designs/adder16` are still untried.** The combinational
   path in particular (`@(a or b or sel)` sampling, no clock, no reset) has never
   been simulated. counter and fifo both run end to end.
5. **`COVERAGE_THRESHOLD` is 90.0**, and the FIFO stopped at 90.18% with real
   bins still empty. For a tool whose purpose is finding coverage holes, 90 is
   generous — consider 95 or 100 with `--max_iter 4`, now that the metric being
   thresholded is actually functional coverage.
6. **Gemini quota** is a practical limit; a full `--regen_cov` run is now ~6
   calls (the interface no longer costs one).

## 9. How to run

```bash
python main.py --design designs/counter/counter.v --max_iter 3 --regen_cov
```

| Flag | Meaning |
|---|---|
| `--regen_cov` | Regenerate the cached golden files (needed after prompt changes) |
| `--max_iter N` | Testbench iterations (default 5) |
| `--mock` | Skip Cadence entirely; still calls Gemini |
| `--purge_kb` | Delete the knowledge base (if it gets contaminated) |

Free checks (no Gemini credits):

```bash
python kb_validate.py                                  # text lint, instant
python kb_compile_check.py                             # real irun, needs licence
python kb_tool.py --for-design designs/counter/counter.v   # what FAISS retrieves
```

Outputs land in `runs/run_<timestamp>/` — prompts, generated files, sim output,
`imc_summary.rpt`, `imc_detail.rpt`, and `summary.json` per iteration.

---

## 10. How to work with this user

- Beginner. Wants **numbered copy-paste commands**, not explanations of options.
- Ships one `EVERYTHING.zip` per change; he replaces the whole folder each time.
  Piecemeal file drops confused him — don't do that.
- A `Stop hook` message about "unpushed commits" appears constantly. It is
  irrelevant: this session's GitHub connection is **read-only** (403 on push and
  on repo creation). Tell him to ignore it; deliver via zip.
- He pastes full terminal output and uploads generated `.sv` files — read them,
  they are the best diagnostic available.
- Do not claim something works without evidence. Several rounds were lost to
  assumptions about flags and syntax that the tool then rejected.
