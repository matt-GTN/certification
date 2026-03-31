"""
DAG Airflow : Entraînement du duo de modèles d'ensemble.
Ré-entraîne le modèle de détection de fraude sur les données historiques.
Planifié hebdomadairement pour intégrer les nouvelles données labellisées.
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import sys

# Ajout du chemin source
sys.path.insert(0, '/opt/airflow')

from src.ml.train import train_model

default_args = {
    'owner': 'data-team',
    'retries': 1,
}

with DAG(
    dag_id='entrainement_modele',
    default_args=default_args,
    description='Entraîne le duo de modèles de détection de fraude',
    schedule_interval='@weekly',  # Ré-entraînement hebdomadaire
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['ml', 'entrainement', 'model_duo'],
) as dag:

    tache_entrainement = PythonOperator(
        task_id='entrainer_model_duo',
        python_callable=train_model,
    )

    tache_entrainement
