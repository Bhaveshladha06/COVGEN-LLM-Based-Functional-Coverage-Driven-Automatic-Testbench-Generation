#!/bin/bash
# Step 3: turn the database into a summary and a detail report.
cd "$(dirname "$0")/work" || { echo "run 1_simulate.sh first"; exit 1; }

cat > report.tcl <<'TCL'
load -run scope/test
report -summary -out summary.rpt
report -detail -uncovered -out detail.rpt
exit
TCL

imc -exec report.tcl -logfile imc.log > /dev/null 2>&1

echo "=== SUMMARY REPORT ==="
cat summary.rpt

echo
echo "READ IT LIKE THIS:"
echo "  row 'counter'          -> Functional n/a is CORRECT. The design itself"
echo "                            holds no covergroups; they live next door."
echo "  row 'counter_coverage' -> Functional should say 60.00%, matching step 1."
echo
echo "  If counter_coverage also says n/a, the covergroup lost its"
echo "  'option.per_instance = 1;' line. That one line is what makes irun"
echo "  write covergroup data into the database at all."
echo
echo "Next:  bash 4_show_bins.sh"
