"""
Script per ottenere gli outcome di chiusura dei mercati BTC da Polymarket, tramite Gamma API ed esegue il join con i trade:
  markets_btc.csv (market_id) -> Gamma API -> market_outcomes.csv
  market_outcomes.csv + trades_btc.csv -> trades_with_outcome.csv
"""

import pandas as pd
import json
import requests
import time
import os
from tqdm import tqdm

# Configurazione:
MARKETS_FILE = "output_btc/markets_btc.csv"
TRADES_FILE = "output_btc/trades_btc.csv"
OUTCOMES_CACHE = "output_btc/market_outcomes.csv"     # cache
OUTPUT_FILE = "output_btc/trades_with_outcome.csv"

BASE_URL = "https://gamma-api.polymarket.com/markets/"
SLEEP_OK = 0.04     # pausa tra le richieste
SLEEP_RETRY = 5.0     # pausa dopo un errore per troppe richieste
SLEEP_ERROR = 2.0    # pausa dopo altri errori
MAX_RETRIES = 5    # tentativi massimi per ogni mercato


# Carica i markets:
print("Caricamento markets_btc.csv")

markets = pd.read_csv(MARKETS_FILE)
print(f"Mercati totali: {len(markets)}")


# Se la cache esiste, viene caricata e vengono saltati i condition_id già processati
if os.path.exists(OUTCOMES_CACHE):
    cached = pd.read_csv(OUTCOMES_CACHE)
    done_ids = set(cached["condition_id"].tolist())
    print(f"Cache trovata: {len(cached)} outcome già salvati, riprendo da dove ero arrivato")
else:
    cached = pd.DataFrame()
    done_ids = set()
    print("Nessuna cache trovata, inizio da zero")

# Filtra solo i mercati non ancora elaborati
to_process = markets[~markets["condition_id"].isin(done_ids)]   # con il NOT(tilde) escludiamo i mercati già elaborati
print(f"Mercati da elaborare: {len(to_process)}\n")

# Parsing dei campi JSON dell'API, gestisce None e dati malformati
def safe_load(x):
    try:
        return json.loads(x) if x else []
    except:
        return []

outcomes = []
mercati_processati = 0

# Chiamate alla Gamma API per gli outcome mancanti
for _, row in tqdm(to_process.iterrows(), total=len(to_process), desc="Fetching outcomes"):
    condition_id = row["condition_id"]
    market_id = row["id"]
    url = f"{BASE_URL}{market_id}"

    winner_found = False

    for attempt in range(1, MAX_RETRIES+1):
        try:
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()

                # L'API restituisce i token tramite clobTokenIds, outcomes e outcomePrices
                clob_ids = safe_load(data.get("clobTokenIds"))
                outcomes_raw = safe_load(data.get("outcomes"))
                prices_raw = safe_load(data.get("outcomePrices"))

                for i, token_id in enumerate(clob_ids):
                    price = float(prices_raw[i]) if i < len(prices_raw) else None
                    # Il vincitore è il token con prezzo 1.0 (mercato chiuso e risolto)
                    is_winner = (price is not None and price > 0.99)
                    # Salva tutti i token
                    outcomes.append({"market_id": market_id, "condition_id": condition_id, "token_id": token_id,
                        "outcome": outcomes_raw[i] if i < len(outcomes_raw) else None, "winner": is_winner,"price": price})
                winner_found = True
                time.sleep(SLEEP_OK)
                break

            elif response.status_code == 429:
                # Troppe richieste, aspetta e riprova
                print(f"\nRate limit su {condition_id}, aspetto {SLEEP_RETRY}s...")
                time.sleep(SLEEP_RETRY)

            elif response.status_code == 404:
                # Mercato non trovato tramite l'API
                outcomes.append({"market_id": market_id, "condition_id": condition_id, "token_id": None, "outcome": "NOT_FOUND", "winner": None, "price": None})
                winner_found = True
                time.sleep(SLEEP_OK)
                break

            else:
                print(f"\nHTTP {response.status_code} su {condition_id}, tentativo {attempt}/{MAX_RETRIES}")
                time.sleep(SLEEP_ERROR)

        except requests.exceptions.Timeout:
            print(f"\nTimeout su {condition_id}, tentativo {attempt}/{MAX_RETRIES}")
            time.sleep(SLEEP_ERROR)

        except Exception as e:
            print(f"\nErrore su {condition_id}: {e}, tentativo {attempt}/{MAX_RETRIES}")
            time.sleep(SLEEP_ERROR)

    if not winner_found:
        # Terminati i tentativi, si considera il mercato non raggiungibile
        outcomes.append({"market_id": market_id, "condition_id": condition_id, "token_id": None, "outcome": "ERROR", "winner": None, "price": None})

    mercati_processati += 1

    # Salva in cache ogni 500 mercati, così da non perdere i risultati già elaborati
    if mercati_processati % 500 == 0:
        batch = pd.DataFrame(outcomes)
        combined = pd.concat([cached, batch], ignore_index=True)
        combined.to_csv(OUTCOMES_CACHE, index=False)
        print(f"\nSalvati {len(combined)} outcome intermedi..")

# Salvataggio in cache
new_df = pd.DataFrame(outcomes)
full_outcomes = pd.concat([cached, new_df], ignore_index=True)
full_outcomes.to_csv(OUTCOMES_CACHE, index=False)
print(f"\nOutcome totali salvati: {len(full_outcomes)}")


# Costruzione tabella outcome per i vincitori
winners = full_outcomes[full_outcomes["winner"] == True][["market_id", "condition_id", "outcome", "token_id"]].rename(
    columns={"token_id": "winning_token_id", "outcome":  "winning_outcome"})

print(f"Mercati con winner trovato: {len(winners)}")
mercati_no_winner = len(markets) - len(winners)
print(f"Mercati senza winner (non chiusi o non trovati): {mercati_no_winner}\n")


# Aggiunge token1 e token2 ai winners per poterli confrontare con nonusdc_side(BTC)
markets_slim = markets[["id", "token1", "token2", "answer1", "answer2"]].rename(columns={"id": "market_id"})
winners = winners.merge(markets_slim, on="market_id", how="left")

# Determina quale lato ha vinto, se token1 o token2, confrontando winning_token_id con i valori di token1 e token2
def get_winning_side(row):
    if str(row["winning_token_id"]) == str(row["token1"]):
        return "token1"
    elif str(row["winning_token_id"]) == str(row["token2"]):
        return "token2"
    else:
        return None

winners["winning_side"] = winners.apply(get_winning_side, axis=1)


# Join con i trades:
# lettura/scrittura a chunk, senza caricare l'intero file
CHUNK_SIZE = 500_000
first_chunk = True

for chunk in tqdm(pd.read_csv(TRADES_FILE, chunksize=CHUNK_SIZE), desc="Caricamento trades"):
    # Join con i winners
    chunk = chunk.merge(winners[["market_id", "winning_outcome", "winning_side", "winning_token_id"]], on="market_id", how="left")

    # Determina l'esito del trade per ogni riga
    trades_chunk = chunk.copy()
    trades_chunk["trade_outcome"] = "LOSS"

    mask_win = ((trades_chunk["taker_direction"] == "BUY") & (trades_chunk["nonusdc_side"] == trades_chunk["winning_side"])) | (
        (trades_chunk["taker_direction"] == "SELL") & (trades_chunk["nonusdc_side"] != trades_chunk["winning_side"]))
    mask_unknown = trades_chunk["winning_side"].isna()

    trades_chunk.loc[mask_win, "trade_outcome"] = "WIN"
    trades_chunk.loc[mask_unknown, "trade_outcome"] = "UNKNOWN"

    # Scrittura sequenziale sul file
    if first_chunk:
        trades_chunk.to_csv(OUTPUT_FILE, index=False, mode="w")
        first_chunk = False
    else:
        trades_chunk.to_csv(OUTPUT_FILE, index=False, mode="a", header=False)

print(f"Scritti tutti i trade in: {OUTPUT_FILE}")
