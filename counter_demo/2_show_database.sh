#!/bin/bash
# Step 2: look at the database irun just wrote.
cd "$(dirname "$0")/work" || { echo "run 1_simulate.sh first"; exit 1; }

echo "=== everything under cov_work/ ==="
ls -R cov_work

echo
echo "=== file sizes ==="
find cov_work -type f -exec du -h {} \;

echo
echo "WHAT THESE ARE:"
echo "  cov_work/scope/*.ucm        the MODEL  -- what bins exist"
echo "  cov_work/scope/test/*.ucd   the DATA   -- which bins were hit"
echo
echo "  'scope' comes from -covscope, 'test' comes from -covtest."
echo "  IMC needs both files. Neither should be 0 bytes."
echo
echo "Next:  bash 3_make_reports.sh"
