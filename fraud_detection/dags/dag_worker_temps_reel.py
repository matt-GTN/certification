"""
DAG Airflow : Worker d'ingestion et prédiction temps réel.
Simule l'arrivée de transactions en continu, effectue la prédiction
et déclenche une alerte si fraude détectée.
Planifié toutes les minutes pour simuler le flux temps réel.
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
import os
import random
import time
import pandas as pd

# Ajout du chemin source
sys.path.insert(0, '/opt/airflow')

from src.utils.db import get_engine
from src.ml.predict import load_prediction_model, predict_fraud
from src.ingestion.worker import load_source_data, transform_record

default_args = {
    'owner': 'data-team',
    'retries': 2,
}


def traiter_transactions_batch(n_transactions=5):
    """
    Traite un lot de N transactions simulées :
    ingestion, prédiction, notification.
    """
    filepath = '/opt/airflow/data/fraudTest.csv'
    df_source = load_source_data(filepath)
    engine = get_engine()
    artifacts = load_prediction_model('/opt/airflow/models/fraud_model.joblib')

    for i in range(n_transactions):
        try:
            # Sélection aléatoire
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
                'model_version': 'lgbm-xgb-ensemble-v1',
                'prediction_score': score,
                'is_alerted': is_fraud
            }
            pd.DataFrame([pred_data]).to_sql('predictions', engine, if_exists='append', index=False)

            # 4. Log dans Airflow
            status = "OK"
            if is_fraud:
                status = "FRAUDE DETECTEE"
                print(f"ALERTE : {status} | Transaction : {pred_data['transaction_id']} | Montant : {df_new['amount'].values[0]} EUR | Score : {score:.4f}")
            else:
                print(f"Transaction {pred_data['transaction_id']} | Score : {score:.4f} | {status}")

        except Exception as e:
            print(f"Erreur lors du traitement de la transaction {i+1} : {e}")


with DAG(
    dag_id='worker_temps_reel',
    default_args=default_args,
    description='Ingestion et prédiction temps réel des transactions',
    schedule_interval=timedelta(seconds=10),  # Toutes les 10 secondes
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,  # Éviter les exécutions concurrentes
    tags=['ingestion', 'prediction', 'temps-reel'],
) as dag:

    tache_traitement = PythonOperator(
        task_id='traiter_lot_transactions',
        python_callable=traiter_transactions_batch,
        op_kwargs={'n_transactions': 5},
    )

    tache_traitement
