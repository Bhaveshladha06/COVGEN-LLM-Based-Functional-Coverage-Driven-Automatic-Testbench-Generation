# config.py -- Central configuration
import os

# =============================================================================
# LLM
# =============================================================================
GEMINI_API_KEY    = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL      = "gemini-2.5-flash"
MAX_OUTPUT_TOKENS = 65536
TEMPERATURE       = 0.2
API_TIMEOUT_SEC   = 120

# =============================================================================
# EDA Tools
# =============================================================================
# irun is the unified SV compiler/simulator (replaces ncverilog for SV flows)
IRUN_BIN      = os.environ.get("IRUN_BIN", "irun")
IMC_BIN       = os.environ.get("IMC_BIN",  "imc")

# Keep for backward compat (not used in SV flow)
NCVERILOG_BIN = os.environ.get("NCVERILOG_BIN", "ncverilog")

# =============================================================================
# Coverage
# =============================================================================
COV_DUT_MODULE   = ""          # filled from parsed design name

# Measure coverage on the DUT ONLY.
#
# With -coverage all and no restriction, irun also scores the testbench, the
# top module and the coverage module. A testbench's defensive code -- the
# watchdog timeout, the "did not reach value X" else-branches, the loop bound
# guards -- is unreachable by construction: covering it would mean making the
# testbench fail. That dead code caps the reported total well below 100% no
# matter how good the stimulus is, and worse, it appears in the uncovered-items
# feedback, so the refinement loop spends iterations writing stimulus aimed at
# the testbench's own error handlers instead of at the design.
#
# Set False if your irun build rejects -covdut, and fall back to writing a
# coverage configuration file at COV_CONFIG_FILE instead.
COV_DUT_ONLY = True

# ...but -covdut <dut> alone ALSO excludes the covergroups, and that silently
# destroyed the measurement this project exists to make.
#
# The covergroups live in a separate module, <dut>_coverage, instantiated as a
# sibling of the DUT inside top_<dut>. -covdut restricts coverage to the named
# module and its submodules, and <dut>_coverage is NOT a submodule of <dut> --
# so IMC reported "Functional Average: n/a" while happily reporting 100% code
# coverage on 12 items, and the loop stopped, declaring victory on a run in
# which no functional coverage was collected at all.
#
# Naming the coverage module as a second DUT puts it back in scope. irun accepts
# -covdut more than once; IMC then emits one summary row per scope (code numbers
# on the DUT row, functional numbers on the coverage row) and coverage_parser
# recombines them.
#
# Set False if your irun build rejects a repeated -covdut. You will get code
# coverage only, and main.py will say so rather than quietly reporting a number
# that is not functional coverage.
COV_DUT_INCLUDE_COVERAGE_MODULE = True

# Refuse to call a run successful when IMC reported functional coverage as
# "n/a". Set False only if you deliberately want code coverage alone.
REQUIRE_FUNCTIONAL_COVERAGE = True

# irun's coverage-enable flags, as a list.
#
# `-coverage all` produced a database in which IMC reported functional coverage
# as "n/a" on every scope, with an empty "Uncovered CoverGroup Detail Report" --
# i.e. no covergroup data reached the database at all, even though the covergroup
# compiled, sampled, and its module was named in -covdut. Whether "all" excludes
# functional coverage on this irun build, or whether it needs a separate flag, is
# not settled; run `irun -helpargs coverage` on the server to see the accepted
# values, then add the right one here. Candidates seen in Incisive flows:
#   ["-coverage", "all"]                     <- current
#   ["-coverage", "all:functional"]
#   ["-coverage", "block:expr:toggle:fsm:functional"]
#   ["-coverage", "all", "-covergroup"]
#
# The pipeline does not depend on getting this right: the coverage model prints
# its own covergroup score at end of simulation and main.py prefers that reading.
# Fixing this flag only restores IMC's per-bin detail report, which is useful
# feedback for the refinement loop but is not the measurement itself.
COVERAGE_FLAGS = ["-coverage", "all"]

# Cap on RTL source injected into the coverage-model prompt. The model must see
# the design to tell which bins are reachable, but a large RTL file should not
# dominate the prompt. Typical unit-level DUTs are well under this.
RTL_MAX_PROMPT_CHARS = 3000

COV_DB_DIR       = "cov_work"
COV_CONFIG_FILE  = "cov.ccf"

# Extra report written by imc_runner from a covergroup-scoped IMC query, used
# as a fallback source of functional coverage when the per-DUT summary hides it.
IMC_FUNCTIONAL_REPORT = "coverage_functional.rpt"

# Coverage database naming under cov_work/<scope>/<test> -- must match the
# "load -run scope/test" TCL command hardcoded in imc_runner.py. If your irun
# install names things differently, change these two and imc_runner.py's
# _IMC_TCL string together.
COV_SCOPE = "scope"
COV_TEST  = "test"

# =============================================================================
# IMC
# =============================================================================
IMC_TCL_SCRIPT    = "imc_report.tcl"
IMC_DETAIL_REPORT = "coverage_detail.rpt"
IMC_LOG           = "imc.log"

# =============================================================================
# Simulation
# =============================================================================
SIM_TIMEOUT_SEC  = 600
IMC_TIMEOUT_SEC  = 120

# Extra irun flags (add +define, +incdir, library flags here)
# Applied to every irun invocation. RTL files often carry no `timescale of
# their own, and irun 15.20 makes that a fatal elaboration error
# (*F,CUMSTS) unless a default is supplied here.
TIMESCALE = "1ns/1ps"

EXTRA_SIM_FLAGS = []

# =============================================================================
# Loop control
# =============================================================================
# 90 was too lenient once per-bin feedback started working: the FIFO stopped at
# 90.18% with real bins still empty and called it a pass. For a tool whose job
# is finding coverage holes, that is the wrong place to stop. 95 keeps the loop
# working without chasing bins that may be genuinely unreachable -- and the
# loop still short-circuits early when the DUT has no uncovered items at all.
COVERAGE_THRESHOLD = 95.0
MAX_ITERATIONS     = 5

# How many times to regenerate a golden file that fails its inline compile
# check before giving up and letting the full run surface the error.
GOLDEN_MAX_REPAIRS = 2

# =============================================================================
# Output
# =============================================================================
OUTPUT_BASE_DIR = "runs"
LOG_LEVEL       = "INFO"

# =============================================================================
# Mock
# =============================================================================
MOCK_SIMULATOR = False

# =============================================================================
# RAG / Knowledge base (FAISS retrieval over past spec -> coverage-model runs)
# =============================================================================
RAG_ENABLED         = True
KB_DIR              = "knowledge_base"
# Single-file corpus: (english_requirement, rtl, coverage_model) triples.
KB_JSON             = os.path.join(KB_DIR, "coverage_kb.json")
EMBEDDING_MODEL     = "all-MiniLM-L6-v2"
# One strong example teaches the style; three mostly inflate the prompt.
RAG_TOP_K           = 1

# Which entries are eligible for retrieval.
#
# `verified` means one thing: the coverage model compiled and produced coverage
# in a real irun/IMC run. Entries recorded automatically from a pipeline run
# (provenance "auto") are LLM output and MUST clear that bar before they can be
# retrieved -- admitting them earlier is what let a covergroup that never
# compiled come back as a "known-good example" and get its errors imitated.
#
# Human-curated and hand-authored entries are different: they were written
# deliberately and pass kb_validate.py's structural checks, so they are
# retrievable without a tool run. Remove "hand_authored" here to be stricter.
RAG_ALLOWED_PROVENANCE = ("curated_seed", "hand_authored")
# Cap on RTL/coverage-model text injected per retrieved example, to keep
# prompt size (and Gemini token spend) bounded on large designs.
RAG_MAX_EXAMPLE_CHARS = 900
# Confidence gate (tau). Below this cosine similarity, retrieval returns
# nothing and the prompt falls back to general best-practice guidance instead
# of injecting a weak/irrelevant example.
# Confidence gate (tau). Measured on the seed corpus: a genuinely related design
# scores ~0.8+ (adder16 -> adder8 = 0.882, -> full_adder = 0.808) while unrelated
# entries sit at 0.2-0.42, so there is a clean cliff between the two. 0.5 sits in
# that gap: relevant precedent gets through, noise does not. Inspect any design's
# scores with:  python kb_tool.py --for-design <rtl> --tau <value>
RAG_MIN_SIMILARITY  = 0.5
