#!/bin/bash
# run_three_times.sh

set -euo pipefail

SCRIPT="./run_BIS.sh"

for i in 1 2 3; do
  echo "======================================"
  echo "  Ejecución número $i de 3"
  echo "======================================"
  $SCRIPT
  echo
done

echo "Las 3 ejecuciones han finalizado."
