#!/bin/bash
# run_bucle.sh

set -euo pipefail

SCRIPT="./run_BIS.sh"
TOTAL=100

for i in $(seq 1 $TOTAL); do
  echo "======================================"
  echo "  Ejecución número $i de $TOTAL"
  echo "======================================"
  $SCRIPT
  echo
done

echo "Las $TOTAL ejecuciones han finalizado."
