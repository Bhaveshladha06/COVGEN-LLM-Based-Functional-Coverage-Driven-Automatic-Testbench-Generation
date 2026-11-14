#!/bin/bash
# Step 5: the same bins, in the IMC GUI. Needs X forwarding (ssh -X).
cd "$(dirname "$0")/work" || { echo "run 1_simulate.sh first"; exit 1; }

echo "Opening IMC. If nothing appears, reconnect with:  ssh -X user@server"
echo
echo "ONCE IT OPENS:"
echo "  1. Left panel: click  counter_coverage"
echo "  2. Switch the view to Functional / Covergroups"
echo "     (a tab or dropdown near the top -- the label varies by version)"
echo "  3. You will see counter_cg. Expand it:"
echo "       count_cp, en_cp, rst_cp, wrap_cp, count_x_en"
echo "  4. Expand count_cp -> four rows with hit counts."
echo "     zero and low have counts > 0."
echo "     high and max show 0 and are coloured as uncovered."
echo "  5. Expand count_x_en -> all 8 pairs, four of them empty."
echo
echo "Same information as step 4, just clickable. Good for report screenshots."
echo

imc -gui -load cov_work/scope/test &
