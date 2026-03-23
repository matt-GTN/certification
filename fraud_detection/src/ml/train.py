import pandas as pd
import numpy as np
import joblib
import os
import sys
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import classification_report, average_precision_score, precision_recall_curve
from imblearn.over_sampling import SMOTE
from tabpfn_client import set_access_token, TabPFNClassifier

# Ajout du chemin pour les utilitaires
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.utils.db import fetch_data_from_db

# Token API PriorLabs pour l'inférence serveur
TABPFN_TOKEN = os.getenv("TABPFN_ACCESS_TOKEN")


def find_optimal_threshold(y_true, y_proba, min_recall=0.75):
    """
    Trouve le seuil optimal qui maximise la précision
    tout en garantissant un recall minimum sur la classe fraude.
    """
    precisions, recalls, thresholds = precision_recall_curve(y_true, y_proba)

    # Parmi tous les seuils garantissant le recall minimum, on prend celui avec la meilleure précision
    valid = recalls[:-1] >= min_recall
    if not valid.any():
        # Si aucun seuil n'atteint le recall minimum, on prend le meilleur recall disponible
        best_idx = np.argmax(recalls[:-1])
    else:
        # Meilleure précision parmi les seuils valides
        best_idx = np.where(valid)[0][np.argmax(precisions[:-1][valid])]

    return thresholds[best_idx]


def train_model():
    # Authentification auprès de l'API PriorLabs
    set_access_token(TABPFN_TOKEN)

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

    features = ['amount', 'category', 'hour', 'day_of_week']
    X = df[features].copy()
    y = df['is_fraud'].astype(int)

    # Pré-traitement : encodage des catégories en numérique
    cat_encoder = LabelEncoder()
    X['category'] = cat_encoder.fit_transform(X['category'])

    # Normalisation des features numériques
    scaler = StandardScaler()
    numeric_features = ['amount', 'hour', 'day_of_week']
    X[numeric_features] = scaler.fit_transform(X[numeric_features])

    # Séparation entraînement / test (stratifié)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Échantillonnage stratifié enrichi en fraudes
    # On garde TOUTES les fraudes + on complète avec des transactions normales jusqu'à 50k
    MAX_SAMPLES = 50000
    fraud_mask = y_train == 1
    X_fraud = X_train[fraud_mask]
    y_fraud = y_train[fraud_mask]
    X_normal = X_train[~fraud_mask]
    y_normal = y_train[~fraud_mask]

    n_fraud = len(X_fraud)
    n_normal_to_keep = min(MAX_SAMPLES - n_fraud, len(X_normal))

    print(f"Échantillonnage enrichi : {n_fraud} fraudes (toutes conservées) + {n_normal_to_keep} normales")
    X_normal_sample = X_normal.sample(n=n_normal_to_keep, random_state=42)
    y_normal_sample = y_normal.loc[X_normal_sample.index]

    X_train_enriched = pd.concat([X_fraud, X_normal_sample])
    y_train_enriched = pd.concat([y_fraud, y_normal_sample])

    # Rééquilibrage des classes avec SMOTE
    # SMOTE a maintenant beaucoup plus de vraies fraudes pour générer des synthétiques de qualité
    print(f"Distribution avant SMOTE : {dict(zip(*np.unique(y_train_enriched, return_counts=True)))}")
    smote = SMOTE(random_state=42, k_neighbors=5)
    X_train_balanced, y_train_balanced = smote.fit_resample(X_train_enriched, y_train_enriched)
    print(f"Distribution après SMOTE : {dict(zip(*np.unique(y_train_balanced, return_counts=True)))}")

    # Re-sous-échantillonner si SMOTE a trop gonflé le dataset (limite API : 50k lignes/requête)
    if len(X_train_balanced) > MAX_SAMPLES:
        print(f"Re-sous-échantillonnage post-SMOTE de {len(X_train_balanced)} à {MAX_SAMPLES}...")
        X_train_balanced, _, y_train_balanced, _ = train_test_split(
            X_train_balanced, y_train_balanced,
            train_size=MAX_SAMPLES, random_state=42, stratify=y_train_balanced
        )

    # Entraînement via l'API PriorLabs (inférence serveur distante)
    print(f"Entraînement du modèle TabPFN v2 via API PriorLabs ({len(X_train_balanced)} échantillons)...")
    clf = TabPFNClassifier(n_estimators=8)
    clf.fit(X_train_balanced, y_train_balanced)

    # Évaluation sur le jeu de test (non rééquilibré, reflète la distribution réelle)
    MAX_EVAL = 10000
    if len(X_test) > MAX_EVAL:
        X_eval = X_test.iloc[:MAX_EVAL]
        y_eval = y_test.iloc[:MAX_EVAL]
    else:
        X_eval = X_test
        y_eval = y_test

    print(f"Évaluation en cours ({len(X_eval)} échantillons)...")
    y_proba = clf.predict_proba(X_eval)[:, 1]

    # Recherche du seuil optimal (recall minimum 75% sur la classe fraude)
    optimal_threshold = find_optimal_threshold(y_eval, y_proba, min_recall=0.75)
    y_pred_optimized = (y_proba >= optimal_threshold).astype(int)

    # Rapport avec seuil par défaut (0.5)
    y_pred_default = (y_proba >= 0.5).astype(int)
    print("\n--- Seuil par défaut (0.5) ---")
    print(classification_report(y_eval, y_pred_default))

    # Rapport avec seuil optimisé
    print(f"\n--- Seuil optimisé ({optimal_threshold:.4f}) ---")
    print(classification_report(y_eval, y_pred_optimized))

    # Métriques clés pour la détection de fraude
    auc_pr = average_precision_score(y_eval, y_proba)
    print(f"AUC-PR (Area Under Precision-Recall Curve) : {auc_pr:.4f}")
    print(f"Seuil de décision retenu : {optimal_threshold:.4f}")

    # Sauvegarde du modèle et des transformateurs
    os.makedirs('models', exist_ok=True)
    model_path = 'models/fraud_model.joblib'
    artifacts = {
        'model': clf,
        'scaler': scaler,
        'cat_encoder': cat_encoder,
        'features': features,
        'numeric_features': numeric_features,
        'threshold': optimal_threshold,
    }
    joblib.dump(artifacts, model_path)
    print(f"Modèle sauvegardé dans {model_path} (seuil : {optimal_threshold:.4f})")


if __name__ == "__main__":
    train_model()
