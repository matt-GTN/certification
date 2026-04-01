# Certification AIA - Architecte en Intelligence Artificielle

Ce repository contient l'ensemble des projets réalisés dans le cadre de la certification **RNCP38777 - Architecte en Intelligence Artificielle** (niveau 7, équivalent BAC+5).

La certification se compose de 4 blocs de compétences, chacun évalué à travers un projet dédié.

---

## Structure du repository

```
certification/
├── spotify/          # Bloc 1 - Gouvernance des données
├── stripe/           # Bloc 2 - Architecture des données
├── fraud_detection/  # Bloc 3 - Pipelines de données
├── delay-forecast/   # Bloc 4 - Solutions d'IA
└── CERTIFICATION.md  # Details de la certification
```

---

## Projets

### Bloc 1 - Gouvernance des données : Spotify

Conception et pilotage d'un framework de Data Governance pour Spotify, couvrant la conformité GDPR/CCPA/PCI-DSS, la qualité des données et l'efficacité opérationnelle.

**Livrables** : Plan unique de gouvernance, slides de présentation, rôles et responsabilités, et implémentation

→ [Voir le projet](spotify/)

---

### Bloc 2 - Architecture des données : Stripe

Conception d'une architecture de données intégrant des systèmes OLTP, OLAP et NoSQL pour Stripe, avec un focus sur l'intégrité transactionnelle, l'analytique avancée et la conformité réglementaire.

**Livrables** : Diagramme d'architecture, ERD OLTP, schema OLAP, modèle NoSQL, architecture pipeline, plan sécurité, stratégie ML.

→ [Voir le projet](stripe/)

---

### Bloc 3 - Pipelines de données : Fraud Detection

Infrastructure complète de détection de fraude en temps réel, utilisant un ensemble de soft-voting comme modèle de classification et **Apache Airflow** comme orchestrateur.

**Stack** : Python, Docker, Airflow, Neon PostgreSQL, Streamlit, ensemble LightGBM + XGBoost

**Livrables** : Code source, schema d'infrastructure, video de démonstration.

[Démonstration](https://youtu.be/a4j-gr6q8tU)

→ [Voir le projet](fraud_detection/)

---

### Bloc 4 - Solutions d'IA : Delay Forecast

POC MLOps de prédiction de retards de transports en commun (Stockholm) en fonction de contextes externes — météo, jours fériés, temporalité. Couvre l'intégralité du cycle de vie ML : ingestion, ETL, entraînement, versioning, serving et monitoring.

**Stack** : Python, Docker, Airflow, MLflow, FastAPI, Evidently, Neon PostgreSQL, AWS S3, Streamlit

**Livrables** : Code source, architecture, video de démonstration.

[Démonstration](https://youtu.be/wguotXaYO0Q)

→ [Voir le projet](delay-forecast/)

---

## Blocs de compétences

| Bloc | Intitulé | Projet | Durée examen |
|------|----------|--------|--------------|
| 1 | Gouvernance des données | Spotify | 30 min |
| 2 | Architecture des données | Stripe | 20 min |
| 3 | Pipelines de données | Fraud Detection | 20 min |
| 4 | Solutions d'IA | Delay Forecast | 15 min |

---

## Formation

**Lead Data Science & Engineering** - Jedha 
