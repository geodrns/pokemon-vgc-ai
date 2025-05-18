#!/bin/bash
# run_MCTSCompetition.sh

# Registrar tiempo de inicio
START_TIME=$(date +%s)

# Crear directorio de logs si no existe
mkdir -p logs

# Array para guardar los PIDs
declare -a PIDS

#
# 1) Levantamos 20 bots (IDs 0..19).
#    ID 1 lo lanzamos con main_mcts.py, los demás con main.py
#
for ID in $(seq 0 19); do
  if [ "$ID" -eq 1 ]; then
    SCRIPT="main_mcts.py"
  else
    SCRIPT="main.py"
  fi

  echo "Starting competitor id=$ID using template/$SCRIPT …"
  (
    cd template
    python3 "$SCRIPT" --id "$ID" \
      > "../logs/$LOGFILE" 2>&1 &
    echo $!  # devolvemos PID
  ) &
  # recogemos el PID real del subshell que lanzó el python
  PIDS[$ID]=$!
done

# Damos 5 s para que todos se levanten
sleep 5

#
# 2) Ejecutamos el Championship Track con 20 agentes
#
RESULTS_LOG="logs/MCTS_Results.log"

{
  echo "============================================"
  echo "Ejecución iniciada el: $(date '+%Y-%m-%d %H:%M:%S')"
  echo "--------------------------------------------"
} >> "${RESULTS_LOG}"

python3 organization/run_championship_track.py \
  --n_agents 20 \
  --epochs 10 \
  --n_moves 100 \
  --roster_size 50 \
  --max_team_size 3 \
  --n_active 2 \
  --max_pkm_moves 4 \
  --n_battles 3 \
  --base_port 5000 \
  >> "${RESULTS_LOG}" 2>&1

# Registrar tiempo de fin y duración
END_TIME=$(date +%s)
DURATION_SEC=$((END_TIME - START_TIME))
DURATION_MIN=$(awk "BEGIN {printf \"%.2f\", ${DURATION_SEC}/60}")

{
  echo ""
  echo "Log generado el: $(date '+%Y-%m-%d %H:%M:%S')"
  echo "Duración total: ${DURATION_MIN} minutos"
  echo ""
} >> "${RESULTS_LOG}"

#
# 3) Cerramos los puertos 5000..5019
#
for PORT in $(seq 5000 5019); do
  lsof -ti:"$PORT" | xargs -r kill -9
done

#
# 4) Esperamos a que mueran los bots
#
for PID in "${PIDS[@]}"; do
  [ -n "$PID" ] && wait "$PID"
done

echo "All processes have finished."
