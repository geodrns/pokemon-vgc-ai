import re
import sys
import statistics
import pandas as pd
from typing import List

def analyze_log(filepath: str):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    winner_elos: List[float] = []
    llm_positions: List[int] = []
    llm_elos: List[float] = []

    # Patrones regex
    winner_pattern = re.compile(r'^\s*1\.\s*\S+.*ELO\s+(\d+\.\d+)')
    llm_pattern    = re.compile(r'^\s*(\d+)\.\s*LLM_Competitor.*ELO\s+(\d+\.\d+)')

    for line in lines:
        m = winner_pattern.match(line)
        if m:
            winner_elos.append(float(m.group(1)))
        m = llm_pattern.match(line)
        if m:
            llm_positions.append(int(m.group(1)))
            llm_elos.append(float(m.group(2)))

    n = len(llm_elos)
    winrate = sum(1 for pos in llm_positions if pos == 1) / n * 100 if n else 0
    best_elo = max(llm_elos) if n else None
    worst_elo = min(llm_elos) if n else None
    mean_elo = statistics.mean(llm_elos) if n else None
    elo_std  = statistics.stdev(llm_elos) if n > 1 else 0
    mean_pos = statistics.mean(llm_positions) if n else None
    pos_std  = statistics.stdev(llm_positions) if n > 1 else 0

    # Diferencia media al ganador
    diffs = [winner_elos[i] - llm_elos[i] for i in range(min(len(winner_elos), n))]
    mean_diff = statistics.mean(diffs) if diffs else None

    # Mostrar resultados en consola
    df = pd.DataFrame({
        'Championship': list(range(1, n+1)),
        'LLM_Position': llm_positions,
        'LLM_ELO': llm_elos,
        'Winner_ELO': winner_elos[:n],
        'ELO_Diff': diffs
    })
    print("\nLLM Performance per Championship:")
    print(df.to_string(index=False))

    # Imprimir estadísticas
    print(f"\nTotal Championships: {n}")
    print(f"Win Rate: {winrate:.2f}%")
    print(f"Best ELO: {best_elo}")
    print(f"Worst ELO: {worst_elo}")
    print(f"Mean ELO: {mean_elo:.2f}")
    print(f"Mean ELO Diff to Winner: {mean_diff:.2f}")
    print(f"ELO Std Dev: {elo_std:.2f}")
    print(f"Mean Position: {mean_pos:.2f}")
    print(f"Position Std Dev: {pos_std:.2f}")

if __name__ == "__main__":
    logfile = sys.argv[1] if len(sys.argv) > 1 else "results.log"
    analyze_log(logfile)
