-- Création des tables pour le projet de détection de fraude

-- Table stockant les transactions brutes (historiques et temps réel)
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(255) UNIQUE NOT NULL, -- Identifiant unique de la transaction source
    timestamp TIMESTAMP NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'EUR',
    merchant_id VARCHAR(255),
    client_id VARCHAR(255),
    ip_address VARCHAR(45), -- IPv4 ou IPv6
    location VARCHAR(255),
    category VARCHAR(100),
    is_fraud BOOLEAN, -- NULL si inconnu (temps réel), TRUE/FALSE si labellisé
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table stockant les prédictions du modèle
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(255) REFERENCES transactions(transaction_id) ON DELETE CASCADE,
    model_version VARCHAR(50) NOT NULL, -- Version du modèle (ex : 'tabpfn-v2')
    prediction_score FLOAT NOT NULL, -- Probabilité de fraude (0.0 à 1.0)
    is_alerted BOOLEAN DEFAULT FALSE, -- Si une notification a été envoyée
    prediction_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour accélérer les recherches par date (reporting) et par client
CREATE INDEX idx_transactions_timestamp ON transactions(timestamp);
CREATE INDEX idx_transactions_client_id ON transactions(client_id);
