# Modèle de Données NoSQL

MongoDB est choisi comme base documentaire pour sa flexibilité avec les données JSON, sa scalabilité horizontale (sharding) et sa capacité à gérer des schémas évolutifs sans interruption de service. Il sert trois cas d'usage : stockage de logs, analyse comportementale et Feature Store ML.

---

## Collections

### 1. `ApplicationLogs`
Logs bruts pour le dépannage et l'audit. Un index TTL supprime automatiquement les données de plus de 30 jours, optimisant les coûts de stockage sans scripts de maintenance.

```json
{
  "_id": "ObjectId",
  "timestamp": "ISODate",
  "level": "ERROR",
  "service_name": "payment-gateway",
  "message": "Timeout de connexion",
  "metadata": { "request_id": "uuid", "stack_trace": "..." },
  "expire_at": "ISODate"
}
```

| Index | Champ(s) | Objectif |
|-------|----------|----------|
| Temporel | `{ timestamp: -1 }` | Logs récents |
| Composite | `{ service_name: 1, level: 1 }` | Filtrage service/sévérité |
| TTL | `{ expire_at: 1 }` | Purge auto 30 jours |

### 2. `UserSessions` (Clickstream)
Agrège les actions utilisateur au sein d'une session. Les événements sont **embarqués** directement dans le document (pattern Embedding) pour garantir la localité des données : une seule lecture disque suffit pour récupérer tout le contexte d'une session.

```json
{
  "_id": "session_uuid",
  "user_id": "customer_uuid",
  "start_time": "ISODate",
  "device_info": { "os": "iOS", "version": "15.0" },
  "events": [
    { "event_type": "view_item", "timestamp": "ISODate", "details": { "product_id": "xyz" } },
    { "event_type": "add_to_cart", "timestamp": "ISODate", "details": { "product_id": "xyz" } }
  ]
}
```

| Index | Champ(s) | Objectif |
|-------|----------|----------|
| Historique | `{ user_id: 1, start_time: -1 }` | Recherche utilisateur |

### 3. `CustomerFeedback`
Avis et réponses aux enquêtes, liés aux transactions OLTP via `transaction_id`.

```json
{
  "_id": "ObjectId",
  "customer_id": "customer_uuid",
  "transaction_id": "transaction_uuid",
  "rating": 5,
  "comment": "Excellent service !",
  "tags": ["rapide", "fiable"],
  "sentiment_score": 0.98
}
```

| Index | Champ(s) | Objectif |
|-------|----------|----------|
| Transaction | `{ transaction_id: 1 }` | Lien OLTP |
| Tags | `{ tags: 1 }` | Index multi-clés |

### 4. `MLFeatures` (Feature Store)

Features pré-calculées garantissant la cohérence entre entraînement et inférence. Le schéma de l'objet `features` est volontairement flexible pour permettre aux data scientists d'ajouter de nouvelles features sans migration de base de données.

```json
{
  "_id": "entity_id_timestamp_hash",
  "entity_id": "customer_uuid",
  "timestamp": "ISODate",
  "features": { "avg_spend_30d": 150.00, "tx_count_7d": 5, "last_login_country": "FR" }
}
```

| Index | Champ(s) | Objectif |
|-------|----------|----------|
| Lookup | `{ entity_id: 1, timestamp: -1 }` | Dernières features par entité |
| Shard Key | `{ entity_id: "hashed" }` | Distribution uniforme |
| TTL | `{ timestamp: 1 }` expireAfterSeconds: 180 jours | Purge des anciennes versions |

**Stratégie de sharding :** La shard key `{ entity_id: "hashed" }` garantit une distribution uniforme des documents sur les shards, évitant les hotspots liés aux clients très actifs. Combinée à un index TTL de 180 jours sur les anciennes versions de features, cette stratégie assure la scalabilité horizontale tout en maîtrisant les coûts de stockage.

---

## DBML (approximation visuelle)

```dbml
Table ApplicationLogs {
  _id ObjectId [pk]
  timestamp ISODate
  level String
  service_name String
  message String
  metadata Object
  expire_at ISODate
}

Table UserSessions {
  _id session_uuid [pk]
  user_id customer_uuid
  start_time ISODate
  device_info Object
  events "Array<Object>" [note: 'Événements embarqués']
}

Table CustomerFeedback {
  _id ObjectId [pk]
  customer_id customer_uuid
  transaction_id transaction_uuid [ref: - Transactions.transaction_id]
  rating int
  comment String
  tags "Array<String>"
  sentiment_score float
}

Table MLFeatures {
  _id entity_timestamp_hash [pk]
  entity_id customer_uuid
  timestamp ISODate
  features Object [note: 'Schéma flexible']
}
```

---

## Requêtes de Validation

**Q1 — Erreurs par service** (DevOps)
```javascript
db.ApplicationLogs.aggregate([
  { $match: { timestamp: { $gte: ISODate("2024-02-01T00:00:00Z") }, level: "ERROR" } },
  { $group: { _id: "$service_name", nb_erreurs: { $sum: 1 }, messages: { $push: "$message" } } },
  { $sort: { nb_erreurs: -1 } }
]);
```

**Q2 — Vélocité utilisateur** (feature ML fraude)
```javascript
db.UserSessions.aggregate([
  { $match: { user_id: "cst_12345", start_time: { $gte: ISODate("2024-02-03T16:00:00Z") } } },
  { $project: { tx: { $filter: { input: "$events", as: "e", cond: { $eq: ["$$e.event_type", "purchase"] } } } } },
  { $unwind: "$tx" },
  { $count: "tx_count_1h" }
]);
```
