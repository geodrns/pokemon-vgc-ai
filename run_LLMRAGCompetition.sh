#!/bin/bash
# run_LLMRAGCompetition.sh

set -euo pipefail

# Número total de agentes y puerto base
NUM_AGENTS=20
BASE_PORT=5000
# El ID que ejecutará tu agente RAG
RAG_ID=1

START_TIME=$(date +%s)
mkdir -p logs

declare -a PIDS

echo "Lanzando $NUM_AGENTS competidores en puertos $BASE_PORT…$((BASE_PORT+NUM_AGENTS-1))"

# 1) Levantamos los bots ID=0..19
for ID in $(seq 0 $((NUM_AGENTS-1))); do
  PORT=$((BASE_PORT + ID))
  if [ "$ID" -eq "$RAG_ID" ]; then
    echo "ID=$ID → template/main_RAG.py en puerto $PORT (log: logs/main_RAG.log)"
    cd template
    python3 main_RAG.py --id "$ID" \
      > "../logs/main_RAG.log" 2>&1 &
    pid=$!
    cd - >/dev/null
  else
    echo "ID=$ID → template/main.py en puerto $PORT"
    cd template
    python3 main.py --id "$ID" \
      > /dev/null 2>&1 &
    pid=$!
    cd - >/dev/null
  fi
  PIDS[$ID]=$pid
done

# Damos un breve margen para que todos los agentes arranquen
sleep 5

# 2) Lanzamos el Championship Track
echo "Arrancando Championship Track…"
RESULTS_LOG="logs/RAG_Results.log"
{
  echo "============================================"
  echo "Ejecución iniciada el: $(date '+%Y-%m-%d %H:%M:%S')"
  echo "Competidores: $NUM_AGENTS (RAG en ID=$RAG_ID)"
  echo "--------------------------------------------"
} >> "$RESULTS_LOG"

python3 organization/run_championship_track_BIS.py \
  --n_agents "$NUM_AGENTS" \
  --base_port "$BASE_PORT" \
  --epochs 10 \
  --n_moves 100 \
  --roster_size 50 \
  --max_team_size 3 \
  --n_active 2 \
  --max_pkm_moves 4 \
  --n_battles 3 \
  >> "$RESULTS_LOG" 2>&1

  # ── NUEVO BLOQUE: extraer posición + ELO de RAG_Competitor ──
  #
  # suponemos que en results.log aparece una línea así:
  # " 7. RAG_Competitor     ELO 1196.72"
  #
  # 1) buscamos la línea
  LINE=$(grep -m1 'RAG_Competitor' "$RESULTS_LOG")
  # 2) extraemos la posición (número antes del punto)
  POS=$(echo "$LINE" | sed -E 's/^ *([0-9]+)\..*/\1/')
  # 3) extraemos el ELO
  ELO=$(echo "$LINE" | sed -E 's/.*ELO *([0-9]+(\.[0-9]+)?).*/\1/')
  # 4) volcamos TODO en template/RAG.txt (sobreescribiendo)
  cat > template/RAG.txt <<EOF
# ROSTER UTILIZADO:
$(grep -E '^[0-9]+: PkmTemplate' template/RAG.txt)

# ÚLTIMO EQUIPO (índices):
$(grep '^LAST TEAM INDICES:' template/RAG.txt)

# ÚLTIMO EQUIPO (species):
$(grep -A3 '^LAST TEAM SPECIES:' template/RAG.txt | tail -n +2)

# RESULTADO FINAL:
POSITION: $POS
ELO     : $ELO
EOF

  #
  # ── fin del bloque de post-procesado ──
  #

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
DURATION_MIN=$(awk "BEGIN{printf \"%.2f\", $DURATION/60}")

{
  echo ""
  echo "Finalizado : $(date '+%Y-%m-%d %H:%M:%S')"
  echo "Duración   : ${DURATION_MIN} minutos"
  echo ""
} >> "$RESULTS_LOG"

# 3) Cerramos cualquier servicio que aún escuche en los puertos 5000..5019
echo "Cerrando puertos ${BASE_PORT}…$((BASE_PORT+NUM_AGENTS-1))"
for P in $(lsof -ntiTCP:"$BASE_PORT"-"$((BASE_PORT+NUM_AGENTS-1))"); do
  kill -9 "$P" || true
done

# 4) Terminamos los procesos Python que lanzamos
echo "Matando procesos competidores…"
for pid in "${PIDS[@]}"; do
  kill -TERM "$pid" 2>/dev/null || true
  wait "$pid" 2>/dev/null || true
done

echo "All processes have finished."
