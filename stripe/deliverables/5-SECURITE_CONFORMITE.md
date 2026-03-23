# Sécurité et Conformité

En tant qu'entreprise FinTech traitant des données de paiement sensibles, Stripe doit garantir la sécurité des données à tous les niveaux et se conformer aux réglementations PCI-DSS, GDPR et CCPA.

---

## 1. Chiffrement

### Données au repos

| Système | Méthode |
|---------|---------|
| **OLTP (PostgreSQL)** | TDE/LUKS + AES-256 applicatif pour les PAN |
| **NoSQL (MongoDB)** | WiredTiger Encryption natif |
| **OLAP (Snowflake)** | Chiffrement par défaut |

### Données en transit
Toute communication interne et externe utilise **TLS 1.3**. Le **mTLS** (Mutual TLS) est imposé pour la communication service-à-service, notamment entre les producteurs/consommateurs Kafka.

### Gestion des clés
Un service KMS dédié (AWS KMS ou HashiCorp Vault) gère le cycle de vie des clés avec une rotation automatique tous les 90 jours.

### Chiffrement applicatif (PCI-DSS)
Le chiffrement disque seul ne suffit pas : un attaquant avec un accès root pourrait lire les fichiers déchiffrés. Les numéros de carte (PAN) sont donc chiffrés **au niveau applicatif** (AES-256) avant insertion dans la base. La DB ne stocke que des blobs chiffrés.

### Tokenisation
Pour l'analytique, les PAN sont remplacés par des tokens déterministes dès l'ingestion. Les analystes n'ont jamais besoin du numéro de carte réel pour calculer le chiffre d'affaires. L'entrepôt de données (OLAP) ne stocke **jamais** de PAN bruts.

---

## 2. Contrôle d'Accès (RBAC)

Chaque rôle reçoit le niveau d'accès minimum nécessaire (principe du moindre privilège) :

| Rôle | Accès | Périmètre |
|------|-------|-----------|
| Service Applicatif | R/W | OLTP (tables spécifiques), Kafka (logs) |
| Data Engineer | R/W | Jobs ETL, Airflow, configs pipeline |
| Data Scientist | R | NoSQL (Features ML), OLAP (anonymisé) |
| Analyste BI | R | Data Marts OLAP (pré-agrégés) |
| Admin | Full | Infrastructure, gestion utilisateurs |

La mise en œuvre repose sur des rôles et groupes discrets dans PostgreSQL et MongoDB. Au niveau réseau, le VPC Peering et les Security Groups isolent les bases OLTP d'Internet.

---

## 3. Conformité Réglementaire

### PCI-DSS

| Exigence | Mise en œuvre |
|----------|--------------|
| Isolation du périmètre | CDE (Cardholder Data Environment) dans une zone réseau restreinte |
| Tokenisation | PAN → tokens non sensibles pour l'analytique |
| Pistes d'audit | Journalisation stricte de tous les accès au CDE |

### GDPR / CCPA

| Droit | OLTP | OLAP | NoSQL |
|-------|------|------|-------|
| Accès | API par `customer_id` | Requêtes sur données anonymisées | Recherche par `customer_id` |
| Effacement | Suppression / anonymisation PII | Vecteurs de suppression ou rebuild batch | TTL auto + masquage PII dans les logs |
| Masquage | Dynamique sauf rôle Support | Pré-anonymisé à l'ingestion | Niveau applicatif |

---

## 4. Monitoring et Audit

Toute activité est tracée dans un système de journalisation centralisé : **qui** a accédé à **quelles** données et **quand**. Des alertes temps réel sont déclenchées pour les comportements suspects :

- **Connexions échouées multiples** → Tentative de force brute
- **Volume d'extraction inhabituel** → Risque d'exfiltration de données
- **Modification de schéma en production** → Altération non autorisée

### Outils de monitoring

| Outil | Rôle |
|-------|------|
| **ELK Stack** (Elasticsearch, Logstash, Kibana) | Agrégation centralisée des logs et recherche full-text |
| **Prometheus + Grafana** | Métriques d'infrastructure et applicatives (latence, saturation, erreurs) |
| **SIEM** (Splunk ou équivalent) | Corrélation d'événements de sécurité et détection d'incidents |
| **PagerDuty / OpsGenie** | Routage des alertes et gestion des incidents (on-call) |

### SLA de réponse aux incidents

| Priorité | Description | Temps de réponse | Temps de résolution |
|----------|-------------|------------------|---------------------|
| **P1** | Fuite de données, exfiltration avérée | < 15 min | < 4 h |
| **P2** | Tentative d'accès non autorisé | < 1 h | < 24 h |
| **P3** | Violation de politique interne | < 4 h | < 72 h |
