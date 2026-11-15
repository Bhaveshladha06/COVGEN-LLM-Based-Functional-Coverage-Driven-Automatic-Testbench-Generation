# COVGEN

**LLM-Based Functional Coverage-Driven Automatic Testbench Generation**

COVGEN is a research framework for translating RTL and English coverage requirements into SystemVerilog coverage models and testbenches. It uses retrieved examples and simulation feedback to refine stimulus through random, constrained-random, and directed phases.

[Project repository](https://github.com/Bhaveshladha06/COVGEN-LLM-Based-Functional-Coverage-Driven-Automatic-Testbench-Generation)

## Workflow

1. Read RTL and an English coverage requirement.
2. Retrieve a matching coverage-model / description / RTL example using embedding similarity and FAISS.
3. Generate the coverage model independently of the testbench.
4. Generate broadly randomized stimulus and compile/simulate it.
5. Use uncovered bins to introduce constraints, then directed sequences if needed.
6. Repair compilation errors, merge compatible coverage databases, and stop at the target or iteration limit.

The supplied paper describes Gemini `gemini-2.5-flash-lite`, Cadence NCSim (`irun`), and Cadence IMC. Exact tool versions and the pipeline entry point must be documented with the implementation release. This README does not assume an unverified script name or command-line interface.

## Coverage-model confidence

The coverage model carries a **retrieval-based confidence indicator** equal to the cosine similarity between the requirement embedding and the selected template-description embedding. It describes semantic alignment; it is not a calibrated probability of correctness and is separate from achieved functional coverage. Raw cosine similarity is not automatically a percentage.

## FIFO case study

The supplied `fifo.v` has eight entries, each eight bits wide, and an active-low asynchronous reset. Occupancy is 0–8. Reads and writes are accepted using the flags before the clock edge:

| Requests | Empty | Partially filled | Full |
| --- | --- | --- | --- |
| Write only | Accept write | Accept write | Block write |
| Read only | Block read | Accept read | Accept read |
| Read and write | Accept write only | Accept both; count unchanged | Accept read only |

Use a scoreboard to check ordering and data, plus checks for occupancy, flags, accepted operations, and resets. Coverage alone does not prove correctness.

### Three-phase evaluation protocol

| Iteration | Stimulus | Purpose |
| --- | --- | --- |
| 1 | Independent randomized requests and input bytes | Establish broad occupancy, operation, and data coverage |
| 2 | Occupancy-aware constrained random traffic and boundary-data bias | Target holes reported by the preceding run |
| 3 | Explicit fill/overflow-attempt, drain/underflow-attempt, and reset-with-data sequences | Reach surviving boundary and reset bins |

The paper contains an **illustrative**, not simulated, 25-bin trajectory: **18/25 (72%) → 22/25 (88%) → 25/25 (100%)**. These values show how a 90% target can require three iterations. They are not evidence of measured COVGEN performance. A real run may close earlier or require more iterations; do not force it to match this example.

The 25-bin example is a proposed revised model, not the bin count of the supplied `fifo_coverage.sv`. It comprises nine occupancy bins, four operation bins, three accepted-data bins, and nine event bins. Preserve the same model and eligible-bin denominator across iterations; merge hit-bin identities without counting repeated hits twice.

### Coverage-model review

Before measurement, address these issues in the supplied coverage model:

- `([2:7] => [2:7])` does not prove equal occupancy on successive cycles. Compare pre- and post-operation count explicitly.
- A reset sampled only at `posedge clk` can miss the previous nonempty state after asynchronous clearing. Capture occupancy at reset assertion, before the reset update.
- The helper occupancy bin overlaps other occupancy bins; inspect the resulting cross denominator and auto bins.
- `iff` gates sampling; it does not remove unreachable bins.
- Sample input-data bins on accepted writes when the intent is stored-data coverage.
- Check the simulator's weighting policy: average covergroup coverage and flat hit-bin coverage can differ.

## Results and evidence status

The following stage values were supplied by the authors. The underlying simulator logs and aggregation definition are not included in the materials used for this revision.

| Stage | Reported coverage | Difference from preceding stage |
| --- | ---: | ---: |
| Randomized | 87.4% | Baseline |
| Constrained random | 92.3% | +4.9 percentage points |
| Directed | 96.6% | +4.3 percentage points |

The random-to-directed difference is **9.2 percentage points**. These values do not establish bin counts, the fraction of designs closed, or mean iterations. Attribution to stages requires the same cohort, model definitions, and aggregation method.

**Reported evaluation count: N = 14.** The supplied screenshot contains **16 folders**, so identify the two designs outside the evaluated cohort before claiming per-design or aggregate results:

`adder16`, `alu4`, `bpred_gshare`, `counter`, `fifo`, `fsm_traffic`, `handshake`, `hdlc_deframer`, `i2c_slave`, `mbist_march`, `mux2`, `sdram_ctrl`, `shift_reg`, `tea_core`, `tlb4`, `width_upsizer`.

The screenshot establishes folder names, not successful completion or measured coverage. Unsupported results are marked **NR (not reported)** in the paper.

## Obtaining and running the implementation

```bash
git clone https://github.com/Bhaveshladha06/COVGEN-LLM-Based-Functional-Coverage-Driven-Automatic-Testbench-Generation.git
cd COVGEN-LLM-Based-Functional-Coverage-Driven-Automatic-Testbench-Generation
```

The repository contents could not be inspected during this revision. The clone command identifies the author-supplied repository; accessibility and completeness are not asserted.

For the complete pipeline, install the dependencies declared by the released implementation, configure its documented Gemini credentials, and load the institution's licensed Cadence environment. Use the actual released entry point. Do not commit API keys or license information.

A standalone simulation requires the RTL, coverage module, and a top-level testbench that instantiates and drives them. **`fifo.v` and `fifo_coverage.sv` alone are not a complete runnable test.** The following is a command template after `fifo_tb.sv` has been created and checked; it was not executed for this revision:

```bash
irun -64bit -sv -coverage all -top fifo_tb \
  fifo.v fifo_coverage.sv fifo_tb.sv
```

Use the installed Cadence release's supported coverage-database/reporting workflow and archive the exact invocation. Confirm that the reported metric is the intended functional coverage, not a combined code/functional coverage score. The proposed 25-bin model requires implementing and validating its monitor before using this template to reproduce the worked example's metric.

## Reproducible reporting

Archive the following for each design and iteration:

- Source revision, evaluated-cohort membership, and coverage-model revision.
- Model name, generation settings, retrieved template, similarity score, and prompts.
- Tool versions, compile command, seed, cycle budget, strategy, and repair logs.
- Eligible-bin identifiers, new hit bins, cumulative hit bins, excluded-bin justifications, and the coverage report/database.
- Scoreboard/checker outcomes, closure threshold, stopping reason, and elapsed time if reported.

Compute closure rate as closed designs divided by evaluated designs. State whether mean iterations includes failures or only successful closures. Compute per-design mean coverage using one final value per design; do not substitute a pooled bin ratio without labeling the different aggregation. Attribute each newly hit bin only to the first phase that hits it.

## Paper

`COVGEN_revised.tex` is the revised IEEE conference source. Compile in a LaTeX environment with `IEEEtran`, TikZ/PGFPlots, `algorithm`, `algpseudocode`, and the packages named in its preamble:

```bash
pdflatex COVGEN_revised.tex
pdflatex COVGEN_revised.tex
```

Before submission, replace the illustrative FIFO trace with measured results, resolve the 14-versus-16 cohort mismatch, fill NR fields from logs, add the final author block, and verify the inherited bibliography and literature-comparison values against their publications.

## License

No project license was supplied with this revision. Add the license selected by the repository owners before describing the code as licensed for redistribution.
