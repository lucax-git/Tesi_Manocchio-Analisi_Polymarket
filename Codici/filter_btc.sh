#!/bin/bash

# Filtrare i mercati Bitcoin/BTC e matchare i trade corrispondenti

# Configurazione percorsi:
MARKETS="DatasetIniziale/markets/markets.csv"
TRADES="DatasetIniziale/processed/trades.csv"

OUT_DIR="output_btc"
MARKETS_OUT="$OUT_DIR/markets_btc.csv"
TRADES_OUT="$OUT_DIR/trades_btc.csv"
# Creazione cartella Output
mkdir -p "$OUT_DIR"


echo "Filtro markets per BTC / Bitcoin"

# Estrazione dell'header per definire la struttura del nuovo file CSV
HEADER_MARKETS=$(head -1 "$MARKETS")
echo "$HEADER_MARKETS" > "$MARKETS_OUT"

# Grep su "bitcoin" e "btc"
grep -i -w "btc\|bitcoin" "$MARKETS" >> "$MARKETS_OUT"

N_MARKETS=$(( $(wc -l < "$MARKETS_OUT") - 1 ))
# Conta il numero di righe presenti nel nuovo file, escludendo l'intestazione
echo "Mercati trovati: $N_MARKETS"
echo "Salvato in: $MARKETS_OUT"


echo "Estrazione degli ID dei mercati BTC"

# Trova la colonna 'id' nel file markets, che corrisponde al campo 2, saltando l'header
tail -n +2 "$MARKETS_OUT" | cut -d',' -f2 | sort -u > "$OUT_DIR/btc_ids.txt"
# sort -u: rimuove eventuali duplicati

N_IDS=$(wc -l < "$OUT_DIR/btc_ids.txt")
echo "ID unici trovati: $N_IDS"


echo "Filtro trades per ID matchati"

HEADER_TRADES=$(head -1 "$TRADES")
echo "$HEADER_TRADES" > "$TRADES_OUT"

# Prepara il file di pattern, con la virgola prima e dopo ogni ID, così da evitare falsi match (es. ,103 non matcha ,1034 o ,10312)
sed 's/^/,/; s/$/,/' "$OUT_DIR/btc_ids.txt" > "$OUT_DIR/btc_ids_pattern.txt"

# Effettua una scansione del file
pv "$TRADES" | grep -F -f "$OUT_DIR/btc_ids_pattern.txt" >> "$TRADES_OUT"
# -f: Carica tutti gli ID dal file btc_ids_pattern.txt
# -F: Considera gli ID come testo semplice

N_TRADES=$(( $(wc -l < "$TRADES_OUT") - 1 ))
echo "Trade trovati: $N_TRADES"
echo "Salvato in: $TRADES_OUT"

echo "File generati:"
echo "  - $MARKETS_OUT ($N_MARKETS mercati)"
echo "  - $TRADES_OUT ($N_TRADES trade)"
echo "  - $OUT_DIR/btc_ids.txt (lista ID)"
# btc_ids_pattern.txt --> file temporaneo con delimitatori ( ,ID, ) per il matching
