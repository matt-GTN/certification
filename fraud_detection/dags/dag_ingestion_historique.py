"""
DAG Airflow : Ingestion des données historiques.
Charge le dataset CSV dans PostgreSQL pour l'entraînement du modèle.
Exécution unique (manuelle) ou planifiable.
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import sys
import os

# Ajout du chemin source
sys.path.insert(0, '/opt/airflow')

from src.ingestion.load_historical import load_historical_data

default_args = {
    'owner': 'data-team',
    'retries': 1,
}

with DAG(
    dag_id='ingestion_historique',
    default_args=default_args,
    description='Charge les données historiques CSV dans PostgreSQL',
    schedule_interval=None,  # Déclenchement manuel uniquement
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['ingestion', 'historique'],
) as dag:

    tache_ingestion = PythonOperator(
        task_id='charger_donnees_historiques',
        python_callable=load_historical_data,
        op_args=['/opt/airflow/data/fraudTest.csv'],
    )

    tache_ingestion
