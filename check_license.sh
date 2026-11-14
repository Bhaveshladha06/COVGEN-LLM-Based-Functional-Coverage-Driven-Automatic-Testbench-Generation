#!/bin/bash
# Collects everything needed to diagnose the Cadence simulation licence error.
echo "===== 1. licence environment variables ====="
env | grep -Ei 'cds_lic|lm_license' || echo "(none set  <-- this is often the problem)"

echo; echo "===== 2. licence files found under /cadence ====="
find /cadence -maxdepth 3 \( -name "*.lic" -o -name "license*" \) 2>/dev/null | head -10 || true

echo; echo "===== 3. lmstat tool ====="
LMSTAT=$(find /cadence -maxdepth 5 -name lmstat -type f 2>/dev/null | head -1)
echo "lmstat: ${LMSTAT:-not found}"

echo; echo "===== 4. who is holding licences ====="
if [ -n "$LMSTAT" ] && [ -n "$CDS_LIC_FILE" ]; then
  "$LMSTAT" -a -c "$CDS_LIC_FILE" 2>&1 | head -40
else
  echo "(skipped: need both lmstat and CDS_LIC_FILE)"
fi

echo; echo "===== 5. can ncsim start at all? ====="
which ncsim irun 2>/dev/null
ncsim -version 2>&1 | head -5

echo; echo "===== done ====="
