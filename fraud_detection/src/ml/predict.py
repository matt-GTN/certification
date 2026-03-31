import pandas as pd
import numpy as np
import joblib


def load_prediction_model(model_path='models/fraud_model.joblib'):
    """Charge les artefacts du modèle (LightGBM + XGBoost, scaler, encodeur, seuil)."""
    return joblib.load(model_path)


def predict_fraud(df_transaction, artifacts):
    """
    Prend un DataFrame d'une seule transaction (format DB)
    et retourne le score de fraude et le flag.
    Utilise la moyenne des probabilités LightGBM et XGBoost (soft voting),
    puis le seuil optimisé pour maximiser le recall sur la classe fraude.
    """
    df = df_transaction.copy()

    # Ingénierie des features (identique à l'entraînement)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['hour'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.dayofweek

    # Features comportementales : lookup dans les stats calculées à l'entraînement
    client_stats = artifacts.get('client_stats')
    merchant_stats = artifacts.get('merchant_stats')

    if client_stats is not None:
        default_tx_count = client_stats['client_tx_count'].median()
        default_avg_amount = client_stats['client_avg_amount'].median()
        df['client_tx_count'] = df['client_id'].map(
            client_stats['client_tx_count']
        ).fillna(default_tx_count)
        df['client_avg_amount'] = df['client_id'].map(
            client_stats['client_avg_amount']
        ).fillna(default_avg_amount)
        df['client_amount_ratio'] = df['amount'] / (df['client_avg_amount'] + 1e-6)

    if merchant_stats is not None:
        default_merchant_count = merchant_stats['merchant_tx_count'].median()
        df['merchant_tx_count'] = df['merchant_id'].map(
            merchant_stats['merchant_tx_count']
        ).fillna(default_merchant_count)

    features = artifacts['features']
    X = df[features].copy()

    # Encodage des catégories
    cat_encoder = artifacts['cat_encoder']
    X['category'] = cat_encoder.transform(X['category'])

    # Normalisation des features numériques
    scaler = artifacts['scaler']
    numeric_features = artifacts['numeric_features']
    X[numeric_features] = scaler.transform(X[numeric_features])

    # Soft voting : moyenne des probabilités LightGBM et XGBoost
    lgbm = artifacts['lgbm']
    xgb = artifacts['xgb']
    p_lgbm = lgbm.predict_proba(X)[:, 1][0]
    p_xgb = xgb.predict_proba(X)[:, 1][0]
    prediction_prob = (p_lgbm + p_xgb) / 2

    threshold = artifacts.get('threshold', 0.5)
    is_fraud_pred = prediction_prob >= threshold

    return float(prediction_prob), bool(is_fraud_pred)
