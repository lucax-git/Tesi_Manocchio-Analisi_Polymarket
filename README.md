# Analisi dei Mercati Predittivi su Bitcoin nella Piattaforma Polymarket

Repository della tesi di laurea riguardante l'analisi dei mercati predittivi su Bitcoin nella piattaforma [Polymarket](https://polymarket.com/).
Il progetto esamina i dati relativi ai trade effettuati su questi mercati e ne analizza gli esiti, così da comprendere come sono strutturati i mercati, chi vi partecipa e come si distribuiscono i volumi dei trade nel tempo, misurando il livello di concentrazione dell'attività tra mercati e wallet.

## Descrizione

I dati sono stati ottenuti da un dataset open-source contenente milioni di transazioni, filtrato per selezionare i mercati relativi a Bitcoin ed integrato tramite la Gamma API di Polymarket per recuperare l'esito dei mercati chiusi. 
Sul sotto-dataset ottenuto, composto da oltre 16 milioni di trade relativi a più di 10.000 mercati Bitcoin, sono state svolte le analisi sulla distribuzione dei trade tra mercati e wallet, sull'andamento temporale dei volumi e sulla concentrazione dell'attività tramite il coefficiente di Gini.

## Struttura della repository

```
├── Analisi_Dati/
│   └── Analisi_Polymarket_BTC.ipynb   # Notebook con le analisi svolte
├── Codici/
│   ├── filter_btc.sh                  # Filtraggio dei mercati e dei trade relativi a Bitcoin
│   ├── get_outcomes.py                # Recupero degli esiti dei mercati tramite la Gamma API
│   └── remove_duplicates.py           # Rimozione dei trade duplicati
├── LICENSE.md
└── README.md
```

## Dataset

Il sotto-dataset analizzato (`trades_with_outcome_clean.csv`) estende i dati originali dei trade eseguiti sui mercati Bitcoin di Polymarket, aggiungendo l'esito finale di ogni mercato ed è disponibile su Zenodo al seguente DOI:
https://doi.org/10.5281/zenodo.21195941

Il file è fornito in formato compresso (`.7z`) per ridurre i tempi di download.
Puoi decomprimerlo con [7-Zip](https://www.7-zip.org/), gratuito e disponibile per Windows/Mac/Linux.

## Utilizzo

Il processo di raccolta e preparazione dei dati è composto dai seguenti passaggi:

```bash
# 1. Filtraggio dei mercati e dei trade relativi a Bitcoin
bash Codici/filter_btc.sh

# 2. Recupero degli esiti dei mercati tramite la Gamma API di Polymarket
python Codici/get_outcomes.py

# 3. Rimozione dei trade duplicati
python Codici/remove_duplicates.py
```

Il sotto-dataset ottenuto, `trades_with_outcome_clean.csv`, può essere analizzato aprendo il notebook `Analisi_Dati/Analisi_Polymarket_BTC.ipynb`, che contiene tutte le analisi descritte nella tesi.

## Licenza

Questo progetto è distribuito con licenza MIT - vedi il file [LICENSE.md](LICENSE.md) per i dettagli. 
Il codice è liberamente utilizzabile, modificabile e ridistribuibile, anche per scopi commerciali, a condizione che venga mantenuto l'avviso di copyright originale.

Il dataset (`trades_with_outcome_clean.csv`) è fornito separatamente su Zenodo con licenza Creative Commons Attribution 4.0 International (CC-BY 4.0).
