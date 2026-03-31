# Détection Automatique de Fraude

Ce projet est une infrastructure complète de détection de fraude en temps réel, utilisant un **ensemble LightGBM + XGBoost** comme modèle de classification et **Apache Airflow** comme orchestrateur de pipeline.

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
    - **airflow-db** : PostgreSQL local (métadonnées Airflow uniquement)
    - **Airflow Webserver** sur le port `8081` (identifiants : admin / admin)
    - **Airflow Scheduler** pour l'orchestration des DAGs
    - **Dashboard Streamlit** sur le port `8501`
    > Les données métier (transactions, prédictions) sont hébergées sur **Neon** (cloud), configuré via `DATABASE_URL` dans `.env`.


4.  **Execution du pipeline via Airflow** :
    - Accéder à l'interface Airflow : `http://localhost:8081`
    - Déclencher le DAG `ingestion_historique` pour charger les données CSV
    - Déclencher le DAG `entrainement_modele` pour entraîner le modèle ensemble
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
*   **Détection proactive** : Inférence ML immédiate sur chaque transaction entrante via l'ensemble LightGBM + XGBoost.
*   **Système d'alerte** : Notification dans la console et les logs Airflow en cas de fraude.
*   **Reporting quotidien** : DAG Airflow générant un rapport CSV et un résumé des fraudes chaque matin.
*   **Supervision métier** : Interface Streamlit pour visualiser les KPI (taux de fraude, volume) et explorer les transactions.

## Modèle

Le modèle actuel est un **ensemble LightGBM + XGBoost (soft voting)**, entraînable en local sur le dataset complet (~555k transactions) en moins d'une minute.

**Pourquoi ce duo ?** LightGBM et XGBoost sont tous deux du gradient boosting mais avec des stratégies de construction d'arbres opposées : LightGBM croît *leaf-wise* (plonge vers les zones les plus informatives, idéal pour détecter les fraudes atypiques) et XGBoost croît *level-wise* (arbres équilibrés, stabilise les prédictions sur la majorité des transactions normales). Leurs erreurs étant partiellement décorrélées, la moyenne de leurs probabilités (*soft voting*) donne un score plus robuste sur les cas limites — précisément ceux où la détection de fraude est la plus critique.

Features utilisées :
*   Montant de la transaction (`amount`)
*   Catégorie de dépense (`category`)
*   Heure de la transaction (`hour`)
*   Jour de la semaine (`day_of_week`)
*   Statistiques comportementales par client (`client_tx_count`, `client_avg_amount`, `client_amount_ratio`)
*   Volume de transactions par marchand (`merchant_tx_count`)

> **Approche initiale** : TabPFN v2 via API PriorLabs a été évaluée en premier. Abandonnée en raison de la limite de 100M cellules/jour (quota épuisé en un seul entraînement) et de la dépendance à une API externe. Code archivé dans `archive/train_tabpfn_v1.py`.

## Orchestration Airflow

| DAG | Planification | Description |
|-----|--------------|-------------|
| `ingestion_historique` | Manuel | Charge le CSV historique en base |
| `entrainement_modele` | Hebdomadaire | Entraîne/ré-entraîne l'ensemble LightGBM + XGBoost |
| `worker_temps_reel` | Toutes les minutes | Ingestion + prediction en continu |
| `rapport_quotidien` | Chaque jour a 8h | Rapport des fraudes de la veille |
