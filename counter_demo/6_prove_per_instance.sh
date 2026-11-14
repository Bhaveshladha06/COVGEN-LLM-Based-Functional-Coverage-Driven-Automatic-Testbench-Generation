#!/bin/bash
# Step 6: delete option.per_instance = 1 and watch functional coverage vanish.
# Same design, same flags, same IMC. Only that one line changes.
cd "$(dirname "$0")"

sed 's/option.per_instance = 1;//' counter_coverage.sv > /tmp/cov_nopi.sv
rm -rf work_nopi && mkdir work_nopi && cd work_nopi

irun -access +rwc -sv -timescale 1ns/1ps \
     -coverage all -covoverwrite -covtest test -covscope scope \
     -covdut counter -covdut counter_coverage \
     ../counter.v ../counter_if.sv /tmp/cov_nopi.sv \
     ../tb_counter.sv ../top_counter.sv \
     -top top_counter > sim.log 2>&1

printf 'load -run scope/test\nreport -summary -out summary.rpt\nexit\n' > r.tcl
imc -exec r.tcl -logfile imc.log > /dev/null 2>&1

echo "=== WITHOUT option.per_instance = 1 ==="
echo
echo "IMC says:"
cat summary.rpt | cut -c1-190 | sed 's/^/  /'
echo
echo "The simulator still says:"
grep "SV_FUNCTIONAL" sim.log | sed 's/^/  /'
echo
echo "The Functional column falls back to n/a, but the simulator's number is"
echo "unchanged. The coverage was never wrong -- it just was not being recorded."
echo
echo "Compare with step 3, which had the line and showed 60.00%."
