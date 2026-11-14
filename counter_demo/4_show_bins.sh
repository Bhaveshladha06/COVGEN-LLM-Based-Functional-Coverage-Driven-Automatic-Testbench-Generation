#!/bin/bash
# Step 4: the part that matters -- exactly which bins are empty.
cd "$(dirname "$0")/work" || { echo "run 3_make_reports.sh first"; exit 1; }

echo "=== UNCOVERED COVERGROUP BINS ==="
sed -n '/Uncovered CoverGroup Detail Report/,$p' detail.rpt

echo
echo "ANSWER KEY -- these 7 of 17 bins should be listed, and nothing else:"
echo "    count_cp.high          (8..14, never reached)"
echo "    count_cp.max           (15, never reached)"
echo "    wrap_cp.wrap           (15 => 0, never happened)"
echo "    count_x_en <high,off>  <high,on>  <max,off>  <max,on>"
echo
echo "THIS LIST is what the pipeline feeds back to the LLM, so it knows which"
echo "bins to write stimulus for."
echo
echo "Next:  bash 5_gui.sh     (needs ssh -X)"
echo "  or:  bash 6_prove_per_instance.sh"
