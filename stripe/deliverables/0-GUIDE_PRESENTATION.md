# Guide de Présentation - Stripe Data Architecture

**Entreprise :** Stripe — FinTech fondée en 2010 à San Francisco.
**Échelle :** Milliards de transactions par an, millions de marchands dans le monde.
**Produit :** Plateforme de traitement des paiements pour les entreprises.

**Objectif du projet :** Concevoir une architecture de données unifiée intégrant OLTP, OLAP et NoSQL pour supporter les opérations transactionnelles, l'analytique avancée et le Machine Learning (détection de fraude, personnalisation client).

---

## Défis Métier

L'expansion mondiale de Stripe génère cinq défis principaux :

- **Transactions :** Les systèmes OLTP traitent des millions de transactions quotidiennes (paiements, remboursements, rétrofacturations). Le système doit garantir haute disponibilité, conformité ACID et détection de fraude en temps réel.
- **Analytique :** Stripe doit fournir analyses de revenus, segmentation client, reporting de conformité et suivi produit via un système OLAP capable de requêtes complexes en quasi temps réel.
- **Données non structurées :** Logs, clickstream, feedback client — ces données alimentent les modèles ML (fraude, personnalisation, prédictif) et nécessitent une base NoSQL flexible.
- **Intégration :** Assurer un flux cohérent entre OLTP, OLAP et NoSQL avec synchronisation temps réel et batch.
- **Conformité :** Architecture conforme GDPR, PCI-DSS et CCPA — chiffrement, contrôle d'accès et journalisation d'audit.

---

## Sources de Données

| Source | Champs clés |
|--------|------------|
| **OLTP** | Transaction ID, marchand, client, montant, devise, méthode paiement, date/heure, localisation IP, appareil, statut, indicateurs fraude |
| **OLAP** | Métriques revenus (jour/semaine/mois), segmentation client, performance produit, analyse fraude, logs audit |
| **NoSQL** | Logs applicatifs, clickstream/sessions, features ML, feedback client |
| **Référence** | Codes pays/régions, taux de change, infos marchands, catalogues produits |

---

## Livrables

| # | Livrable | Fichier |
|---|----------|---------|
| 1 | Diagramme d'architecture complet | `1-DIAGRAMME_ARCHITECTURE.md` |
| 2 | ERD du système OLTP | `2-DIAGRAMME_ERD_OLTP.md` |
| 3 | Schéma OLAP | `3-DIAGRAMME_OLAP.md` |
| 4 | Modèle NoSQL | `4-MODELE_DONNEES_NOSQL.md` |
| 5 | Sécurité et conformité | `5-SECURITE_CONFORMITE.md` |
| 6 | Intégration ML | `6-STRATEGIE_INTEGRATION_ML.md` |
