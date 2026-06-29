# Legge il file trades_with_outcome.csv, rimuove i duplicati e produce trades_with_outcome_clean.csv

import pandas as pd
from tqdm import tqdm

# Configurazione:
INPUT_FILE = "Analisi_Dati/trades_with_outcome.csv"
OUTPUT_FILE = "Analisi_Dati/trades_with_outcome_clean.csv"
CHUNK_SIZE = 500_000
KEY_COLS = ['transactionHash', 'maker', 'taker', 'nonusdc_side']

seen = set()
first_chunk = True
total_in = 0
total_out = 0

# Rimuove i duplicati
for chunk in tqdm(pd.read_csv(INPUT_FILE, chunksize=CHUNK_SIZE), desc="Processing"):
    total_in += len(chunk)
    
    # Crea una chiave univoca per ogni riga
    keys = list(zip(chunk['transactionHash'], chunk['maker'], chunk['taker'], chunk['nonusdc_side']))
    
    # Mantiene solo le righe non ancora elaborate
    mask = []
    for k in keys:
        if k not in seen:
            seen.add(k)
            mask.append(True)
        else:
            mask.append(False)
    
    chunk_clean = chunk[mask]
    total_out += len(chunk_clean)
    
    if first_chunk:
        chunk_clean.to_csv(OUTPUT_FILE, index=False, mode="w")
        first_chunk = False
    else:
        chunk_clean.to_csv(OUTPUT_FILE, index=False, mode="a", header=False)

print(f"\nRighe lette: {total_in}")
print(f"Righe scritte: {total_out}")
print(f"Duplicati rimossi: {total_in - total_out}")

# Controlla il numero di righe sul file realizzato
count_lines = sum(1 for _ in open(OUTPUT_FILE)) - 1    # -1 per l'header
df_check = pd.read_csv(OUTPUT_FILE, usecols=['transactionHash'])

print(f"Corrispondono: {'SI' if count_lines == len(df_check) else 'NO'}")
