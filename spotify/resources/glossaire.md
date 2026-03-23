---
**Titre :** Glossaire de la Gouvernance des Données — Spotify
**Version :** 1.0 | **Date :** 7 Avril 2026
**Auteur :** Mathis GENTHON
**Statut :** Référence interne — applicable à tous les livrables du projet
**Framework de référence :** DMBOK v2 (DAMA International)
---

## Termes organisationnels

| Terme | Acronyme | Définition (conforme DMBOK) |
|:---|:---:|:---|
| **Chief Data Officer** | CDO | Responsable exécutif de la stratégie globale de la donnée chez Spotify. Sponsor du programme de gouvernance. Rôle existant au sein du COMEX Spotify. |
| **Data Governance Office** | DGO | Équipe dédiée (3-5 personnes) chargée d'opérer le programme de gouvernance : maintien des standards, support aux Stewards, reporting au DGC. Dirigée par un **Directeur de Gouvernance** recruté en Phase 1. |
| **Directeur de la Gouvernance des Données** | DGD | Responsable opérationnel du DGO, rattaché au CDO. Première embauche critique de la Phase 1. Ne pas confondre avec le CDO (rôle stratégique existant). |
| **Data Protection Officer** | DPO | Responsable indépendant de la conformité au RGPD/CCPA. Obligation légale pour Spotify (Art. 37 RGPD). Rattaché à la Direction Juridique. |
| **Data Governance Committee** | DGC | Instance de décision transversale : CDO (président), DPO, Head of Engineering, Marketing Director, Product Leadership. Se réunit mensuellement. |
| **Data Steward** | DS | Expert métier responsable de la qualité, de la définition et des accès aux données de son domaine. Rôles par domaine : Utilisateurs, Métadonnées Contenu, Finance, Marketing. |
| **Centre d'Excellence** | CoE | Modèle organisationnel hybride : standards et outils centralisés (le "Centre"), expertise métier décentralisée dans les BU (l'"Excellence"). Recommandé pour Spotify. |

---

## Termes réglementaires

| Terme | Acronyme | Définition |
|:---|:---:|:---|
| **Règlement Général sur la Protection des Données** | RGPD | Régulation européenne (UE 2016/679) encadrant le traitement des données personnelles. Articles clés : Art. 5 (principes), Art. 6 (base légale), Art. 17 (droit à l'effacement), Art. 25 (Privacy by Design), Art. 33 (notification de violation sous 72h). |
| **California Consumer Privacy Act** | CCPA | Loi californienne (1798.100 et seq.) donnant aux résidents californiens des droits sur leurs données personnelles, dont le droit d'opt-out de la vente de données. |
| **Payment Card Industry Data Security Standard** | PCI-DSS | Standard de sécurité pour les organisations traitant des données de paiement par carte. Obligatoire pour Spotify (abonnements Premium). |
| **EU AI Act** | — | Réglementation européenne sur l'intelligence artificielle (entrée en vigueur 2024-2026). Classifie les systèmes de recommandation algorithmique comme "risque limité" — obligations de transparence applicables à Spotify. |
| **Personal Data Protection Act (Singapour)** | PDPA | Loi singapourienne sur la protection des données personnelles. Applicable aux opérations Spotify en Asie-Pacifique. |
| **Data Subject Access Request** | DSAR | Demande d'un utilisateur d'exercer ses droits RGPD/CCPA (accès, rectification, effacement). Spotify a l'obligation de répondre dans un délai d'1 mois (RGPD Art. 12). |

---

## Termes techniques et qualité des données

| Terme | Définition (conforme DMBOK) |
|:---|:---|
| **Catalogue de données** | Inventaire centralisé des actifs de données de l'organisation, incluant métadonnées techniques et métier, lignage et glossaire. Outil retenu : Alation. |
| **Lignage de données** | Traçabilité de la donnée de sa source jusqu'à sa destination, en passant par toutes les transformations. Outil retenu : Monte Carlo. |
| **Privacy by Design** | Principe (RGPD Art. 25) exigeant que la confidentialité soit intégrée dans la conception des systèmes, pas ajoutée à posteriori. |
| **Classification des données** | Taxonomie à 4 niveaux : **Public** (aucune restriction), **Interne** (collaborateurs uniquement), **Confidentiel** (accès restreint par rôle), **Restreint** (accès nominalisé, données les plus sensibles). |
| **RACI** | Matrice de responsabilités : **R**esponsable (exécutant), **A**ccountable (responsable final), **C**onsulté (avis nécessaire), **I**nformé (notification). |
| **DMBOK** | Data Management Body of Knowledge — référentiel de bonnes pratiques de la gestion des données publié par DAMA International. Référence normative de ce projet. |
| **DSAR SLA** | Engagement de niveau de service sur les demandes d'accès : 72h pour accuser réception, 30 jours pour réponse complète (RGPD Art. 12). |
| **Data Quality Score** | Indicateur composite mesurant les dimensions de qualité DMBOK : exactitude, complétude, cohérence, actualité, unicité, validité. |

---

## Convention de nommage des fichiers

| Type de document | Convention |
|:---|:---|
| Livrables de certification | `ETAPE_[N]_[NOM].md` |
| Documents de synthèse finaux | `SPOTIFY_[SUJET]_FINAL.md` |
| Ressources de support | `resources/[nom].md` ou `resources/[nom].csv` |
| Documents de pilotage | `[NOM_EN_MAJUSCULES].md` (racine du projet) |
