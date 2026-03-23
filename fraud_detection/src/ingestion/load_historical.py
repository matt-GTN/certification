import argparse
import pandas as pd
import sys
import os

# Ajout du dossier parent au path pour importer src.utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.utils.db import load_data_to_db, get_engine


def load_historical_data(filepath: str):
    """
    Charge les données historiques depuis un CSV vers la base de données.
    Effectue un mapping des colonnes pour correspondre au schéma 'transactions'.
    """
    if not os.path.exists(filepath):
        print(f"Erreur : Fichier {filepath} introuvable.")
        return

    print(f"Chargement des données depuis {filepath}...")
    try:
        # Lecture du CSV (on ignore la première colonne d'index si elle existe)
        df = pd.read_csv(filepath, index_col=0)

        # Mapping des colonnes CSV -> Schéma DB
        df_mapped = pd.DataFrame()
        df_mapped['transaction_id'] = df['trans_num']
        df_mapped['timestamp'] = pd.to_datetime(df['trans_date_trans_time'])
        df_mapped['amount'] = df['amt']
        df_mapped['currency'] = 'EUR'  # Devise par défaut pour ce projet
        df_mapped['merchant_id'] = df['merchant']
        df_mapped['client_id'] = df['cc_num'].astype(str)
        df_mapped['category'] = df['category']
        df_mapped['is_fraud'] = df['is_fraud'].astype(bool)

        # Construction de la localisation
        df_mapped['location'] = df['city'] + ', ' + df['state']

        # Adresse IP absente du dataset
        df_mapped['ip_address'] = None

        print(f"{len(df_mapped)} enregistrements préparés pour l'insertion.")

        # Insertion par lots pour optimiser la mémoire
        chunk_size = 10000
        total_chunks = (len(df_mapped) // chunk_size) + 1

        engine = get_engine()
        with engine.connect() as conn:
            for i in range(0, len(df_mapped), chunk_size):
                chunk = df_mapped.iloc[i:i+chunk_size]
                chunk.to_sql('transactions', conn, if_exists='append', index=False, method='multi')
                print(f"Lot {i//chunk_size + 1}/{total_chunks} inséré")

        print("Ingestion des données historiques terminée avec succès.")

    except Exception as e:
        print(f"Erreur lors du chargement : {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Charger les données historiques en base")
    parser.add_argument("filepath", type=str, help="Chemin vers le fichier CSV")
    args = parser.parse_args()

    load_historical_data(args.filepath)
