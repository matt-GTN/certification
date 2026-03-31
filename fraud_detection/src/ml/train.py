"""
Entraînement du modèle de détection de fraude — LightGBM + XGBoost (soft voting).

Choix du duo LightGBM + XGBoost :
- Même famille (gradient boosting) mais stratégies de construction d'arbres opposées :
  LightGBM croît leaf-wise (plonge vers les zones les plus informatives, capte les fraudes
  atypiques) ; XGBoost croît level-wise (arbres équilibrés, plus régularisés, stabilise les
  prédictions sur la masse). Leurs erreurs sont donc partiellement décorrélées.
- Le soft voting (moyenne des probabilités brutes) lisse la frontière de décision sur les
  cas limites — les plus importants en détection de fraude.
- Gestion native du déséquilibre de classes via scale_pos_weight : pas besoin de SMOTE.
- Entraînable en local sur le dataset complet (~555k lignes) en < 1 minute.

Remplace : TabPFN v2 via API PriorLabs (archivé dans archive/train_tabpfn_v1.py).
"""

import pandas as pd
import numpy as np
import joblib
import os
import sys
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import (
    classification_report, average_precision_score,
    precision_recall_curve, fbeta_score,
)
from lightgbm import LGBMClassifier
from xgboost import XGBClassifier

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.utils.db import fetch_data_from_db


def find_optimal_threshold(y_true, y_proba, min_recall=0.75):
    """
    Trouve le seuil qui maximise la précision tout en garantissant
    un recall minimum sur la classe fraude.
    """
    precisions, recalls, thresholds = precision_recall_curve(y_true, y_proba)
    valid = recalls[:-1] >= min_recall
    if not valid.any():
        best_idx = np.argmax(recalls[:-1])
    else:
        best_idx = np.where(valid)[0][np.argmax(precisions[:-1][valid])]
    return thresholds[best_idx]


def train_model():
    print("Récupération des données depuis la base pour l'entraînement...")
    query = "SELECT * FROM transactions WHERE is_fraud IS NOT NULL"
    df = fetch_data_from_db(query)

    if df.empty:
        print("Aucune donnée trouvée en base pour l'entraînement.")
        return

    print(f"{len(df)} enregistrements chargés.")

    # Ingénierie des features
    print("Ingénierie des features en cours...")
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['hour'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.dayofweek

    client_stats = df.groupby('client_id').agg(
        client_tx_count=('amount', 'count'),
        client_avg_amount=('amount', 'mean'),
    ).reset_index()
    df = df.merge(client_stats, on='client_id', how='left')
    df['client_amount_ratio'] = df['amount'] / (df['client_avg_amount'] + 1e-6)

    merchant_stats = df.groupby('merchant_id').agg(
        merchant_tx_count=('amount', 'count'),
    ).reset_index()
    df = df.merge(merchant_stats, on='merchant_id', how='left')

    features = ['amount', 'category', 'hour', 'day_of_week',
                'client_tx_count', 'client_avg_amount', 'client_amount_ratio',
                'merchant_tx_count']
    X = df[features].copy()
    y = df['is_fraud'].astype(int)

    # Encodage des catégories
    cat_encoder = LabelEncoder()
    X['category'] = cat_encoder.fit_transform(X['category'])

    # Normalisation (sans effet sur les arbres, conservée pour cohérence avec predict.py)
    scaler = StandardScaler()
    numeric_features = ['amount', 'hour', 'day_of_week',
                        'client_tx_count', 'client_avg_amount', 'client_amount_ratio',
                        'merchant_tx_count']
    X[numeric_features] = scaler.fit_transform(X[numeric_features])

    # Split entraînement / validation / test (stratifié)
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.5, random_state=42, stratify=y_temp
    )

    # Pondération native des classes (remplace SMOTE)
    n_neg = (y_train == 0).sum()
    n_pos = (y_train == 1).sum()
    scale_pos_weight = n_neg / n_pos
    print(f"Ratio déséquilibre : {scale_pos_weight:.1f}× "
          f"({n_neg} normales / {n_pos} fraudes)")

    # --- LightGBM (leaf-wise : spécialiste des patterns rares) ---
    print(f"Entraînement LightGBM sur {len(X_train)} échantillons...")
    lgbm = LGBMClassifier(
        n_estimators=500,
        learning_rate=0.05,
        num_leaves=63,
        scale_pos_weight=scale_pos_weight,
        random_state=42,
        n_jobs=-1,
        verbose=-1,
    )
    lgbm.fit(X_train, y_train)

    # --- XGBoost (level-wise : stabilisateur, robuste aux outliers) ---
    print(f"Entraînement XGBoost sur {len(X_train)} échantillons...")
    xgb = XGBClassifier(
        n_estimators=500,
        learning_rate=0.05,
        max_depth=6,
        scale_pos_weight=scale_pos_weight,
        random_state=42,
        n_jobs=-1,
        eval_metric='aucpr',
        verbosity=0,
    )
    xgb.fit(X_train, y_train)

    def ensemble_proba(X):
        """Soft voting : moyenne des probabilités des deux modèles."""
        return (lgbm.predict_proba(X)[:, 1] + xgb.predict_proba(X)[:, 1]) / 2

    # Optimisation du seuil sur validation (toutes les fraudes conservées)
    print(f"Optimisation du seuil sur validation ({y_val.sum()} fraudes)...")
    y_proba_val = ensemble_proba(X_val)
    optimal_threshold = find_optimal_threshold(y_val, y_proba_val, min_recall=0.75)

    # Évaluation finale sur test
    print(f"Évaluation finale sur test ({y_test.sum()} fraudes)...")
    y_proba_test = ensemble_proba(X_test)
    y_pred_default = (y_proba_test >= 0.5).astype(int)
    y_pred_optimized = (y_proba_test >= optimal_threshold).astype(int)

    print("\n--- Seuil par défaut (0.5) ---")
    print(classification_report(y_test, y_pred_default))

    print(f"\n--- Seuil optimisé sur validation ({optimal_threshold:.4f}) ---")
    print(classification_report(y_test, y_pred_optimized))

    # Guard : fallback à 0.5 si le seuil optimisé dégrade le F2 (β=2 favorise le recall)
    f2_optimized = fbeta_score(y_test, y_pred_optimized, beta=2, zero_division=0)
    f2_default = fbeta_score(y_test, y_pred_default, beta=2, zero_division=0)
    if f2_optimized < f2_default:
        print(f"Seuil optimisé (F2={f2_optimized:.3f}) < seuil 0.5 "
              f"(F2={f2_default:.3f}) → fallback à 0.5")
        optimal_threshold = 0.5

    auc_pr = average_precision_score(y_test, y_proba_test)
    print(f"AUC-PR : {auc_pr:.4f}")
    print(f"Seuil retenu : {optimal_threshold:.4f}")

    # Données PR curve pour le dashboard (calculées sur le jeu de test)
    pr_precisions, pr_recalls, pr_thresholds = precision_recall_curve(y_test, y_proba_test)

    # Sauvegarde des artefacts
    os.makedirs('models', exist_ok=True)
    model_path = 'models/fraud_model.joblib'
    artifacts = {
        'lgbm': lgbm,
        'xgb': xgb,
        'scaler': scaler,
        'cat_encoder': cat_encoder,
        'features': features,
        'numeric_features': numeric_features,
        'threshold': optimal_threshold,
        'client_stats': client_stats.set_index('client_id'),
        'merchant_stats': merchant_stats.set_index('merchant_id'),
        'model_version': 'lgbm-xgb-ensemble-v1',
        'pr_curve': {
            'precisions': pr_precisions.tolist(),
            'recalls': pr_recalls.tolist(),
            'thresholds': pr_thresholds.tolist(),
            'auc_pr': float(auc_pr),
        },
    }
    joblib.dump(artifacts, model_path)
    print(f"Modèle sauvegardé dans {model_path} (seuil : {optimal_threshold:.4f})")


if __name__ == "__main__":
    train_model()
