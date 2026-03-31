# Qualité des données et observabilité du pipeline

Ce document détaille les procédures de contrôle qualité et de monitoring implémentées dans le pipeline de détection de fraude pour répondre aux exigences du **Bloc 3** de la certification AIA.

## 1. Contrôles qualité automatisés (Data Quality)

Le pipeline intègre des mécanismes de validation à chaque étape pour garantir l'intégrité des prédictions :

### Ingestion (Source -> Brut)
*   **Validation du schéma** : Le script `worker.py` s'assure que les champs obligatoires (`transaction_id`, `amount`, `category`, `timestamp`) sont présents avant toute insertion.
*   **Conversion de types** : Conversion forcée des types (ex : timestamp en `datetime`, montants en `float`) pour éviter les erreurs de calcul en aval.
*   **Orchestration** : Airflow détecte et relance automatiquement les tâches échouées (retries configurables par DAG).

### Évaluation du modèle
*   **Jeux de validation et test stratifiés** : La séparation train/val/test (80/10/10) conserve le taux de fraude réel (≈ 0,38 %) dans chaque split. Le jeu de test final contient 214 fraudes — suffisant pour que les métriques (recall, précision, AUC-PR) soient statistiquement fiables.
*   **Optimisation du seuil sans leakage** : Le seuil de décision est optimisé sur le jeu de validation (215 fraudes), puis évalué sur le jeu de test (214 fraudes) pour éviter tout surapprentissage du seuil.
*   **Guard F2** : Si le seuil optimisé dégrade le F2-score (β=2, favorise le recall) par rapport au seuil neutre 0.5, le pipeline revient automatiquement à 0.5 — garantissant qu'une optimisation mal contrainte ne peut pas régresser les performances en production.

### Transformation (Ingénierie des features)
*   **Gestion des valeurs manquantes** : Le pipeline de prédiction vérifie l'absence de valeurs nulles sur les features critiques (`amount`, `category`).
*   **Référentiel temporel** : Synchronisation de l'heure système avec l'heure de la transaction pour garantir la cohérence des features temporelles (`hour`, `day_of_week`).
*   **Cohérence des transformateurs** : Le scaler et l'encodeur de catégories sont sauvegardés avec le modèle pour garantir un pré-traitement identique entre entraînement et inférence.

## 2. Observabilité et surveillance

Le pipeline est piloté par trois outils complémentaires :

### Monitoring opérationnel (Airflow)
L'interface web Airflow fournit :
*   **État des DAGs** : Visualisation en temps réel du statut de chaque tâche (succès, échec, en cours).
*   **Historique des exécutions** : Traçabilité complète de chaque run avec durée, logs, et résultat.
*   **Alertes d'échec** : Notification automatique en cas d'échec d'une tâche (configurable par email ou Slack).
*   **Dépendances** : Graphe visuel des dépendances entre les tâches du pipeline.

### Monitoring métier (Streamlit)
Le tableau de bord fournit une vue consolidée de la "santé" des données :
*   **Taux de fraude anomal** : Une augmentation soudaine du taux de fraude peut indiquer un problème de dérive du modèle ou une corruption des données d'entrée.
*   **Volume de transactions** : Permet de vérifier que le pipeline d'ingestion ne subit pas d'interruption (baisse de cadence).

### Monitoring technique (Logs et alertes)
*   **Traçage des prédictions** : Chaque prédiction est enregistrée dans la table `predictions` de **Neon PostgreSQL** avec la version du modèle utilisée (`lgbm-xgb-ensemble-v1`), permettant un audit a posteriori en cas de faux positifs.
*   **Logs Airflow** : Les détections de fraude sont journalisées dans les logs de chaque exécution de DAG, accessibles via l'interface web.

## 3. Gestion des erreurs et reprise (Error Correction)

*   **Reprises automatiques (Airflow)** : Chaque DAG est configuré avec un nombre de tentatives (`retries`). En cas d'échec réseau ou base de données, la tâche est automatiquement relancée.
*   **Blocs Try/Except** : La boucle du worker est protégée contre les erreurs, assurant la résilience du flux.
*   **Exécution unique** : Le DAG `worker_temps_reel` est configuré avec `max_active_runs=1` pour éviter les doublons et les conditions de concurrence.
*   **Logs d'erreurs** : En cas d'échec d'une insertion, l'erreur est capturée et journalisée sans arrêter le pipeline global (principe de tolérance aux pannes).

## 4. Reporting et traçabilité

*   **Rapport quotidien automatisé** : Le DAG `rapport_quotidien` génère chaque matin un fichier CSV contenant toutes les transactions et fraudes de la veille, archivé dans `data/rapports/`.
*   **Versionnement du modèle** : Chaque prédiction est associée à la version du modèle (`lgbm-xgb-ensemble-v1`), permettant de tracer l'évolution des performances.
*   **Historique complet** : L'interface Airflow conserve l'historique de toutes les exécutions, offrant une vue d'ensemble de la fiabilité du pipeline.

## 5. Conformité à la gouvernance

Toutes les données ingérées respectent la politique de gouvernance définie (anonymisation des données sensibles comme le numéro de carte bancaire, qui est haché ou tronqué).
