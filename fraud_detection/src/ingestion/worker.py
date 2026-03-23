import time
import pandas as pd
import random
from datetime import datetime
import sys
import os

# Ajout du chemin pour les imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.utils.db import get_engine
from src.ml.predict import load_prediction_model, predict_fraud


def load_source_data(filepath):
    """Charge les données source pour la simulation temps réel."""
    print("Chargement des données source pour la simulation...")
    return pd.read_csv(filepath, index_col=0)


def transform_record(record):
    """Transforme une ligne du CSV en format compatible avec le schéma DB."""
    data = {
        'transaction_id': f"{record['trans_num']}_{int(time.time())}",
        'timestamp': datetime.now(),
        'amount': record['amt'],
        'currency': 'EUR',
        'merchant_id': record['merchant'],
        'client_id': str(record['cc_num']),
        'category': record['category'],
        'is_fraud': None,  # Inconnu au moment de la transaction temps réel
        'location': f"{record['city']}, {record['state']}",
        'ip_address': None
    }
    return pd.DataFrame([data])


def run_worker(filepath, interval=5):
    """Boucle principale du worker : ingestion -> prédiction -> notification."""
    df_source = load_source_data(filepath)
    engine = get_engine()

    print("Chargement du modèle ML...")
    artifacts = load_prediction_model()

    print(f"Démarrage de la simulation temps réel & détection (Intervalle : {interval}s)")

    while True:
        try:
            # Sélection aléatoire d'un enregistrement
            random_index = random.randint(0, len(df_source) - 1)
            record = df_source.iloc[random_index]

            # 1. Transformation & Ingestion
            df_new = transform_record(record)
            with engine.connect() as conn:
                df_new.to_sql('transactions', conn, if_exists='append', index=False)

            # 2. Prédiction
            score, is_fraud = predict_fraud(df_new, artifacts)

            # 3. Sauvegarde de la prédiction
            pred_data = {
                'transaction_id': df_new['transaction_id'].values[0],
                'model_version': 'tabpfn-v2',
                'prediction_score': score,
                'is_alerted': is_fraud
            }
            pd.DataFrame([pred_data]).to_sql('predictions', engine, if_exists='append', index=False)

            # 4. Notification
            status = "OK"
            if is_fraud:
                status = "FRAUDE DETECTEE !"
                print(f"\n{'='*40}\nALERTE : {status}\nTransaction : {pred_data['transaction_id']}\nMontant : {df_new['amount'].values[0]} EUR\nScore : {score:.4f}\n{'='*40}\n")
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Ingérée {df_new['transaction_id'].values[0]} | Score : {score:.4f} | {status}")

            time.sleep(interval)

        except Exception as e:
            print(f"Erreur dans la boucle du worker : {e}")
            time.sleep(interval)


if __name__ == "__main__":
    # Fichier source par défaut
    FILEPATH = "data/fraudTest.csv"
    if len(sys.argv) > 1:
        FILEPATH = sys.argv[1]

    if not os.path.exists(FILEPATH):
        print(f"Fichier {FILEPATH} introuvable. Veuillez le télécharger d'abord.")
        sys.exit(1)

    run_worker(FILEPATH)
