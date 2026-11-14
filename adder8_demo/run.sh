#!/bin/bash
# =============================================================================
#  8-bit adder -- the whole flow, by hand. No Python, no Gemini, no corpus.
#
#      bash run.sh          simulate + report
#      bash run.sh --gui    the same, then open the IMC GUI at the end
#
#  Five hand-written files, so the result is identical every time:
#      adder8.v             the design
#      adder8_if.sv         the shared wires
#      adder8_coverage.sv   the covergroup  (what counts as tested)
#      tb_adder8.sv         the stimulus
#      top_adder8.sv        wiring, holds the other three
# =============================================================================
set -u
cd "$(dirname "$0")"
GUI=0
[ "${1:-}" = "--gui" ] && GUI=1

# ---- preflight ---------------------------------------------------------------
# Coming back to a fresh terminal, the Cadence tools are usually not on PATH yet.
for tool in irun imc; do
  if ! command -v "$tool" > /dev/null 2>&1; then
    echo "ERROR: '$tool' not found on PATH."
    echo
    echo "Set up the terminal first:"
    echo "    source \"\$HOME/miniforge3/etc/profile.d/conda.sh\""
    echo "    conda activate assergent"
    echo "    source ~/.bashrc"
    exit 1
  fi
done
echo "irun : $(command -v irun)"
echo "imc  : $(command -v imc)"
echo

rm -rf work && mkdir work && cd work

# =============================================================================
echo "=============================================================="
echo " STEP 1 -- SIMULATE"
echo "=============================================================="
# One line per flag so it is readable; the shell joins them itself.
#   -coverage all      turn coverage collection on
#   -covoverwrite      replace the previous database instead of erroring
#   -covscope/-covtest name the folders inside the database
#   -covdut            score only these modules, not the testbench
irun -access +rwc -sv -timescale 1ns/1ps \
     -coverage all -covoverwrite -covtest test -covscope scope \
     -covdut adder8 -covdut adder8_coverage \
     ../adder8.v ../adder8_if.sv ../adder8_coverage.sv \
     ../tb_adder8.sv ../top_adder8.sv \
     -top top_adder8 > sim.log 2>&1

if grep -qE "\*E,|\*F," sim.log; then
  echo "SIMULATION FAILED:"
  grep -E "\*E,|\*F," sim.log | head -10 | sed 's/^/  /'
  echo
  echo "Full log: adder8_demo/work/sim.log"
  exit 1
fi
echo "  compiled and ran, no errors."
echo
echo "--- functional coverage, straight from the simulator ---"
grep "SV_" sim.log | sed 's/^/  /'
echo
echo "  The total is the AVERAGE of the seven coverpoints, not"
echo "  (bins hit / total bins). One weak coverpoint drags it down."

# =============================================================================
echo
echo "=============================================================="
echo " STEP 2 -- WHAT irun WROTE TO DISK"
echo "=============================================================="
find cov_work -type f | sed 's/^/  /'
echo
echo "  *.ucm  the MODEL -- what bins exist"
echo "  *.ucd  the DATA  -- which bins were hit"
echo "  IMC needs both. Neither should be 0 bytes."

# =============================================================================
echo
echo "=============================================================="
echo " STEP 3 -- IMC TURNS THAT INTO REPORTS"
echo "=============================================================="
cat > report.tcl <<'TCL'
load -run scope/test
report -summary -out summary.rpt
report -detail -uncovered -out detail.rpt
exit
TCL
imc -exec report.tcl -logfile imc.log > /dev/null 2>&1

if [ ! -s summary.rpt ]; then
  echo "IMC produced no summary. See adder8_demo/work/imc.log"
  exit 1
fi
cat summary.rpt
echo
echo "  Row 'adder8'           -> Functional n/a is CORRECT. The design itself"
echo "                            contains no covergroups."
echo "  Row 'adder8_coverage'  -> this is the one to read. It should match the"
echo "                            simulator number from step 1."

# =============================================================================
echo
echo "=============================================================="
echo " STEP 4 -- WHICH BINS ARE EMPTY"
echo "=============================================================="
sed -n '/Uncovered CoverGroup Detail Report/,$p' detail.rpt
echo
echo "  EXPECTED: the cross bin <max,max> of a_x_b is uncovered."
echo "  tb_adder8.sv drives a=255 with b=0, and b=255 with a=0, but never"
echo "  both at 255 together -- so 24 of the 25 a_x_b bins fill and one"
echo "  does not. That hole is deliberate, so this report has something"
echo "  real in it."
echo
echo "  THIS LIST is what the pipeline feeds back to the LLM, so it knows"
echo "  which bins to write new stimulus for."

# =============================================================================
echo
echo "=============================================================="
echo " DONE"
echo "=============================================================="
echo "  logs and reports : adder8_demo/work/"
echo "      sim.log         everything irun printed"
echo "      summary.rpt     the coverage table"
echo "      detail.rpt      the uncovered bins"
echo
if [ "$GUI" -eq 1 ]; then
  echo "Opening the IMC GUI. Needs X forwarding -- reconnect with ssh -X if blank."
  echo "  In the GUI: click adder8_coverage -> switch to the Functional /"
  echo "  Covergroups view -> expand a_x_b -> find <max,max> sitting at 0."
  imc -gui -load cov_work/scope/test &
else
  echo "To see the same thing clickable (needs ssh -X):"
  echo "    bash run.sh --gui"
fi
