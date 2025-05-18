#!/bin/bash
# run_LLMCompetition.sh

# Registrar tiempo de inicio (segundos desde epoch)
START_TIME=$(date +%s)

# Crear directorio de logs si no existe
mkdir -p logs

echo "Starting Template Competitor using template/main.py (id 0)..."
cd template
# Lanzar competidor 0 y loguear
python3 main.py --id 0 > ../logs/main_0.log 2>&1 &
PID0=$!

echo "Starting LLM Competitor using template/main_llm_mcts.py (id 1)..."
# Lanzar competidor LLM MCTS y loguear
python3 main_llm_mcts.py --id 1 > ../logs/main_llm_mcts.log 2>&1 &
PID1=$!

# Esperar a que ambos procesos estén inicializados
sleep 5

echo "Starting Championship Track in organization/run_championship_track.py..."
cd ../organization

RESULTS_LOG="../logs/LLM_Results.log"

# Cabecera para distinguir ejecuciones
{
  echo "============================================"
  echo "Ejecución iniciada el: $(date '+%Y-%m-%d %H:%M:%S')"
  echo "--------------------------------------------"
} >> "${RESULTS_LOG}"

# Ejecutar la competición y añadir su salida al log
python3 run_championship_track.py >> "${RESULTS_LOG}" 2>&1

# Registrar tiempo de fin
END_TIME=$(date +%s)
# Calcular duración en segundos
DURATION_SEC=$((END_TIME - START_TIME))
# Convertir a minutos con dos decimales
DURATION_MIN=$(awk "BEGIN {printf \"%.2f\", ${DURATION_SEC}/60}")

# Pie de ejecución con fecha de fin y duración
{
  echo ""
  echo "Log generado el: $(date '+%Y-%m-%d %H:%M:%S')"
  echo "Duración total: ${DURATION_MIN} minutos"
  echo ""
} >> "${RESULTS_LOG}"

# Esperar a que cierren los procesos de los competidores
wait $PID0 $PID1

# Matar cualquier proceso que quede escuchando en los puertos
lsof -ti:5000 | xargs -r kill -9
lsof -ti:5001 | xargs -r kill -9

echo "All processes have finished."
