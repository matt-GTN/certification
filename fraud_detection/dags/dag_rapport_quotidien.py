"""
DAG Airflow : Rapport quotidien.
Génère chaque matin un résumé des transactions et fraudes de la veille.
Correspond au besoin métier : "chaque matin, vérifier les paiements et fraudes de la journée précédente".
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import sys
import os
import pandas as pd

# Ajout du chemin source
sys.path.insert(0, '/opt/airflow')

from src.utils.db import fetch_data_from_db

default_args = {
    'owner': 'data-team',
    'retries': 1,
}


def generer_rapport_quotidien():
    """
    Extrait les transactions et fraudes de la veille,
    génère un rapport CSV et affiche un résumé dans les logs Airflow.
    """
    query = """
    SELECT
        t.transaction_id, t.timestamp, t.amount, t.category, t.location,
        t.merchant_id, t.client_id,
        p.prediction_score, p.is_alerted, p.model_version
    FROM transactions t
    LEFT JOIN predictions p ON t.transaction_id = p.transaction_id
    WHERE t.timestamp >= NOW() - INTERVAL '1 day'
    ORDER BY t.timestamp DESC
    """
    df = fetch_data_from_db(query)

    if df.empty:
        print("Aucune transaction sur les dernières 24 heures.")
        return

    # Statistiques du résumé
    total = len(df)
    fraudes = df[df['is_alerted'] == True]
    nb_fraudes = len(fraudes)
    taux_fraude = (nb_fraudes / total) * 100 if total > 0 else 0
    volume_total = df['amount'].sum()
    volume_fraudes = fraudes['amount'].sum() if nb_fraudes > 0 else 0

    # Affichage du résumé dans les logs Airflow
    print("=" * 60)
    print("  RAPPORT QUOTIDIEN - DÉTECTION DE FRAUDE")
    print(f"  Date : {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    print(f"  Transactions totales     : {total}")
    print(f"  Fraudes détectées        : {nb_fraudes}")
    print(f"  Taux de fraude           : {taux_fraude:.2f}%")
    print(f"  Volume total             : {volume_total:,.2f} EUR")
    print(f"  Volume frauduleux        : {volume_fraudes:,.2f} EUR")
    print("=" * 60)

    if nb_fraudes > 0:
        print("\n  Détail des fraudes détectées :")
        print("-" * 60)
        for _, row in fraudes.iterrows():
            print(f"  ID: {row['transaction_id']} | Montant: {row['amount']} EUR | Score: {row['prediction_score']:.4f} | Catégorie: {row['category']}")
        print("-" * 60)

    # Export CSV du rapport
    rapport_dir = '/opt/airflow/data/rapports'
    os.makedirs(rapport_dir, exist_ok=True)
    date_str = datetime.now().strftime('%Y-%m-%d')
    chemin_rapport = os.path.join(rapport_dir, f'rapport_{date_str}.csv')
    df.to_csv(chemin_rapport, index=False)
    print(f"\n  Rapport CSV exporté : {chemin_rapport}")


with DAG(
    dag_id='rapport_quotidien',
    default_args=default_args,
    description='Rapport quotidien des transactions et fraudes de la veille',
    schedule_interval='0 8 * * *',  # Chaque matin à 8h
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['reporting', 'quotidien'],
) as dag:

    tache_rapport = PythonOperator(
        task_id='generer_rapport_quotidien',
        python_callable=generer_rapport_quotidien,
    )

    tache_rapport
