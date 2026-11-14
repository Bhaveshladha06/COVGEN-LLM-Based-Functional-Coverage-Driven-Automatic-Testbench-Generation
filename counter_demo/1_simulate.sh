#!/bin/bash
# Step 1: run the simulation and write the coverage database.
cd "$(dirname "$0")"
rm -rf work && mkdir work && cd work

irun -access +rwc -sv -timescale 1ns/1ps \
     -coverage all -covoverwrite -covtest test -covscope scope \
     -covdut counter -covdut counter_coverage \
     ../counter.v ../counter_if.sv ../counter_coverage.sv \
     ../tb_counter.sv ../top_counter.sv \
     -top top_counter > sim.log 2>&1

echo "=== errors, if any ==="
grep -E "\*E,|\*F," sim.log | head -10 || echo "  none"

echo
echo "=== the score the SIMULATOR calculated (no database involved) ==="
grep "SV_" sim.log | sed 's/^/  /'

echo
echo "Expected:"
echo "  SV_FUNCTIONAL_COVERAGE: 60.0000"
echo "  count_cp  50    (zero and low hit; high and max not)"
echo "  en_cp    100"
echo "  rst_cp   100"
echo "  wrap_cp    0    (never reached 15, so never wrapped)"
echo "  cross     50    (4 of 8 pairs)"
echo
echo "Full log: counter_demo/work/sim.log"
echo "Next:  bash 2_show_database.sh"
