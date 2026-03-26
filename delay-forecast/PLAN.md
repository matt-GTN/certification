# Plan de nettoyage — Delay Forecast (Certification Bloc 4)

> **Principe :** les données et modèles restent sur disque. Le code/notebooks inutiles sont supprimés. Le repo git doit être propre et présentable au jury.

---

## Phase 1 — Supprimer le code inutile

- [x] **1.1** Supprimer les notebooks d'exploration jetables (debug/POC, logique déjà dans `src/`)
  - `exploration/transport_call_history_clean.ipynb` — logique absorbée dans `src/pipeline/transport/`
  - `exploration/transport_call_history_days_loop.ipynb` — doublon
  - `exploration/script_test.ipynb` — debug
  - `exploration/script_test_filtred.ipynb` — doublon filtré
  - `exploration/send_to_S3.ipynb` — test upload avec données hardcodées
  - `exploration/send_to_neon.ipynb` — test batch PostgreSQL
  - `exploration/S3_transform_to_neon.ipynb` — ETL one-shot
  - `exploration/ml_first_test.ipynb` — expériences ML obsolètes (modèles finaux dans MLflow)
  - `exploration/call_transport_data.ipynb` — setup API, pas d'insight
  - `exploration/compare_koda.ipynb` — comparaison de formats API
  - `exploration/compare_route_sort_name.ipynb` — mapping route IDs
  - `exploration/compare_real_time.ipynb` — 3000 lignes de JSON brut
  - `exploration/compare_real_time.py` — notebook exporté en .py (4446 lignes de JSON)
  - `test_etl/etl_meteo_calendrier_prevision.ipynb` — stub incomplet

- [x]**1.2** Garder uniquement 3 notebooks valorisants
  - `exploration/EDA_tests_modeles.ipynb` — EDA + évaluation modèles avec Plotly ✅
  - `exploration/call_meteo_api.ipynb` — feature engineering météo ✅
  - `test_etl/etl_meteo_calendrier_archives.ipynb` — feature engineering avancé (risques gel, neige, verglas) ✅

- [x]**1.3** Supprimer les fichiers orphelins
  - `test.txt` (contient "hello" — artefact de debug)

---

## Phase 2 — Réorganiser l'arborescence

- [x]**2.1** Créer `docs/` et y déplacer les assets visuels
  - `poc_delay_forecast.png` → `docs/poc_delay_forecast.png`
  - `schéma v8.png` → `docs/architecture.png` (renommer sans accent/espace)

- [x]**2.2** Déplacer `feature_importance.csv` → `docs/feature_importance.csv`
  - Montre les drivers du modèle (stop_sequence 22.9%, hour_sin 12.8%, etc.) — utile pour le jury

- [x]**2.3** Réorganiser les notebooks restants
  - Déplacer `test_etl/etl_meteo_calendrier_archives.ipynb` → `exploration/etl_meteo_calendrier_archives.ipynb`
  - Supprimer le dossier `test_etl/` (vide après déplacement)

---

## Phase 3 — Corriger le `.gitignore`

- [x]**3.1** Corriger les règles trop larges
  - `*.txt` bloque `requirements.txt` → retirer cette règle
  - `*.yaml` bloque les configs → retirer cette règle
  - Remplacer par des patterns ciblés

- [x]**3.2** Ajouter les exclusions pour les données locales (restent sur disque, hors du git)
  ```gitignore
  # Données locales
  data/
  models/
  mlruns/
  mlruns_artifacts/
  mlartifacts/
  mlflow_data/
  test.db
  ```

---

## Phase 4 — Mettre à jour le README.md

- [x]**4.1** Corriger l'arborescence
  - `services/airflow/tasks/` → n'existe pas, le vrai code est dans `src/pipeline/`

- [x]**4.2** Corriger le tableau "Interactions entre les modules"
  - `tasks/ingest_etl.py` → `src/pipeline/transport/run_transport.py`
  - `tasks/transform.py` → `src/pipeline/weather/run_archive_weather.py`
  - `tasks/train.py` → `src/pipeline/train_model.py`

- [x]**4.3** Mettre à jour la Roadmap
  - "Retraining automatique" → **fait** (`weekly_drift_detector.py`)
  - "Monitoring du drift" → **fait** (service Evidently)

- [x]**4.4** Ajouter le service Evidently
  - Absent du tableau des composants et des URLs (port 8001)

- [x]**4.5** Corriger "bac+7" → "bac+5" (niveau 7 RNCP ≠ bac+7)


---

## Phase 5 — Renforcer le DAG Airflow

- [x]**5.1** `delay_forecast_daily.py` = simple `echo "pong"` (16 lignes)
  - Le transformer en vrai pipeline : ingestion transport → météo → transformation
  - Sinon : le supprimer et ne garder que `weekly_drift_detector.py` qui est fonctionnel

---

## Phase 6 — Vérifications techniques

- [x]**6.1** Vérifier que `docker-compose.yml` inclut le service Evidently
- [x]**6.2** Vérifier la cohérence des imports (`libs/` ↔ `services/` ↔ `src/`)
- [x]**6.3** Vérifier que `pytest` passe sur `tests/`
- [x]**6.4** Vérifier le workflow CI/CD (`.github/workflows/cicd_pipeline.yml`) après nettoyage

---

## Phase 7 — Documentation finale

- [x]**7.1** Relecture finale README — chaque section reflète le code réel
- [x]**7.2** (Optionnel) Créer `docs/cahier_des_charges.md` — valorise la compétence du référentiel

---

## Ordre d'exécution

```
Phase 1 (supprimer code inutile) → Phase 2 (réorganiser) → Phase 3 (.gitignore)
  → Phase 4 (README) → Phase 5 (DAG) → Phase 6 (vérifs) → Phase 7 (docs)
```
