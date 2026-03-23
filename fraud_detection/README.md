# Détection Automatique de Fraude

Ce projet est une infrastructure complète de détection de fraude en temps réel, utilisant **[TabPFN v2](https://priorlabs.ai/)** (par [Prior Labs](https://priorlabs.ai/)) comme modèle de classification et **Apache Airflow** comme orchestrateur de pipeline.

## Installation rapide

1.  **Environnement Conda** :
```bash
    conda create -n fraud_detection python=3.10 -y
    conda activate fraud_detection
    pip install -r requirements.txt
```

2.  **Configuration de la base de données Neon** :
    - Créer un projet sur [neon.tech](https://neon.tech)
    - Copier `.env.example` vers `.env` et renseigner vos propres credentials :
```bash
    cp .env.example .env
    ```
    - Exécuter le schéma initial dans la console SQL de Neon :
    ```bash
    psql $DATABASE_URL -f database/init.sql
```

3.  **Lancement de l'infrastructure (Docker)** :
```bash
    docker-compose up -d
```
    Cela démarre :
    - **Airflow Webserver** sur le port `8081` (identifiants : admin / admin)
    - **Airflow Scheduler** pour l'orchestration des DAGs
    - **Dashboard Streamlit** sur le port `8501`
    > La base de données est hébergée sur **Neon** (cloud), aucun conteneur de base de données n'est démarré localement.


4.  **Execution du pipeline via Airflow** :
    - Accéder à l'interface Airflow : `http://localhost:8081`
    - Déclencher le DAG `ingestion_historique` pour charger les données CSV
    - Déclencher le DAG `entrainement_modele` pour entraîner TabPFN v2
    - Activer le DAG `worker_temps_reel` pour la simulation en continu
    - Le DAG `rapport_quotidien` s'exécute automatiquement chaque matin à 8h

5.  **Execution manuelle (sans Airflow)** :
```bash
    # Charger les variables d'environnement
    source .env

    # Charger les données historiques
    python src/ingestion/load_historical.py data/fraudTest.csv

    # Entraîner le modèle
    python src/ml/train.py

    # Lancer le worker temps réel
    python src/ingestion/worker.py data/fraudTest.csv

    # Lancer le tableau de bord
    streamlit run src/app/main.py
```

## Architecture

Le détail des choix techniques et le schéma d'infrastructure sont disponibles dans :
*   `ARCHITECTURE.md` : Schéma de flux, justifications techniques et structure des dossiers.
*   `PIPELINE_QUALITY.md` : Qualité des données et observabilité du pipeline.

## Fonctionnalités

*   **Ingestion temps réel** : Simulation d'une API de paiement avec stockage dans **Neon PostgreSQL** (cloud), orchestrée par Airflow.
*   **Détection proactive** : Inference ML immédiate sur chaque transaction entrante via [TabPFN v2](https://priorlabs.ai/).
*   **Système d'alerte** : Notification dans la console et les logs Airflow en cas de fraude.
*   **Reporting quotidien** : DAG Airflow générant un rapport CSV et un résumé des fraudes chaque matin.
*   **Supervision métier** : Interface Streamlit pour visualiser les KPI (taux de fraude, volume) et explorer les transactions.

## Modèle

Le modèle actuel est **[TabPFN v2](https://priorlabs.ai/)**, un modèle fondation pré-entraîné via mécanisme d'attention pour les données tabulaires. Il est développé par [Prior Labs](https://priorlabs.ai/), et utilise les caractéristiques suivantes :
*   Montant de la transaction (`amount`)
*   Categorie de dépense (`category`)
*   Heure de la transaction (`hour`)
*   Jour de la semaine (`day_of_week`)

## Orchestration Airflow

| DAG | Planification | Description |
|-----|--------------|-------------|
| `ingestion_historique` | Manuel | Charge le CSV historique en base |
| `entrainement_modele` | Hebdomadaire | Entraine/re-entraine TabPFN v2 |
| `worker_temps_reel` | Toutes les minutes | Ingestion + prediction en continu |
| `rapport_quotidien` | Chaque jour a 8h | Rapport des fraudes de la veille |
