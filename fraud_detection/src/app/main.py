import streamlit as st
import pandas as pd
import numpy as np
import sys
import os
import plotly.express as px
import plotly.graph_objects as go
import joblib

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.utils.db import fetch_data_from_db

st.set_page_config(page_title="Tableau de Bord - Détection de Fraude", page_icon="🕵️", layout="wide")
st.title("Détection de Fraude - Supervision Globale")
st.markdown("Tableau de bord de suivi des transactions et détection de fraude en temps réel.")

st.sidebar.header("Filtres")
days = st.sidebar.slider("Période (derniers jours)", 1, 30, 7)


@st.cache_data(ttl=60)
def load_dashboard_data(days_limit):
    query = f"""
    SELECT
        t.transaction_id, t.timestamp, t.amount, t.category, t.location,
        p.prediction_score, p.is_alerted
    FROM transactions t
    LEFT JOIN predictions p ON t.transaction_id = p.transaction_id
    WHERE t.timestamp >= NOW() - INTERVAL '{days_limit} days'
    ORDER BY t.timestamp DESC
    """
    return fetch_data_from_db(query)


@st.cache_resource
def load_model_artifacts():
    try:
        return joblib.load('models/fraud_model.joblib')
    except Exception:
        return None


df = load_dashboard_data(days)
artifacts = load_model_artifacts()

if df.empty:
    st.warning("Aucune donnée trouvée pour cette période.")
else:
    # KPIs
    total_ts = len(df)
    frauds = df[df['is_alerted'] == True]
    nb_frauds = len(frauds)
    fraud_rate = (nb_frauds / total_ts) * 100 if total_ts > 0 else 0
    total_amount = df['amount'].sum()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Transactions", f"{total_ts:,}")
    col2.metric("Fraudes détectées", nb_frauds, delta=f"{nb_frauds} alertes", delta_color="inverse")
    col3.metric("Taux de fraude", f"{fraud_rate:.2f}%")
    col4.metric("Volume total", f"{total_amount:,.0f} EUR")

    tab1, tab2, tab3 = st.tabs(["Vue opérationnelle", "Performance modèle", "Rapports journaliers"])

    # ── Tab 1 : Vue opérationnelle ──────────────────────────────────────────
    with tab1:
        st.subheader("Évolution des transactions")
        df['date'] = pd.to_datetime(df['timestamp']).dt.date
        daily_stats = df.groupby('date').size().reset_index(name='count')
        fig_line = px.line(daily_stats, x='date', y='count',
                           title="Transactions par jour", template="plotly_dark")
        st.plotly_chart(fig_line, use_container_width=True)

        c1, c2 = st.columns(2)

        with c1:
            st.subheader("Top catégories à risque")
            df_cat = df.dropna(subset=['is_alerted']).copy()
            cat_stats = df_cat.groupby('category').agg(
                total=('is_alerted', 'count'),
                alertes=('is_alerted', 'sum')
            ).reset_index()
            cat_stats['taux_fraude'] = cat_stats['alertes'] / cat_stats['total'] * 100
            cat_stats = cat_stats.sort_values('taux_fraude', ascending=False)
            fig_cat = px.bar(
                cat_stats, x='category', y='taux_fraude',
                title="Taux de fraude par catégorie (%)",
                template="plotly_dark", color='taux_fraude',
                color_continuous_scale='Reds',
                labels={'taux_fraude': 'Taux fraude (%)', 'category': 'Catégorie'}
            )
            fig_cat.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig_cat, use_container_width=True)

        with c2:
            st.subheader("Dernières alertes de fraude")
            if nb_frauds > 0:
                st.dataframe(
                    frauds[['timestamp', 'amount', 'category', 'prediction_score']].head(10),
                    use_container_width=True
                )
            else:
                st.info("Aucune fraude détectée sur cette période.")

        st.subheader("Toutes les transactions")
        st.dataframe(df.head(100), use_container_width=True)

    # ── Tab 2 : Performance modèle ──────────────────────────────────────────
    with tab2:
        c1, c2 = st.columns(2)

        with c1:
            st.subheader("Courbe Précision-Recall")
            if artifacts and 'pr_curve' in artifacts:
                pr = artifacts['pr_curve']
                threshold = artifacts.get('threshold', 0.5)

                fig_pr = go.Figure()
                fig_pr.add_trace(go.Scatter(
                    x=pr['recalls'], y=pr['precisions'],
                    mode='lines', name='PR Curve',
                    line=dict(color='#00b4d8', width=2)
                ))

                # Point de fonctionnement : seuil retenu
                thresholds_arr = np.array(pr['thresholds'])
                idx = int(np.argmin(np.abs(thresholds_arr - threshold)))
                fig_pr.add_trace(go.Scatter(
                    x=[pr['recalls'][idx]], y=[pr['precisions'][idx]],
                    mode='markers',
                    name=f"Seuil retenu ({threshold:.2f})",
                    marker=dict(color='red', size=12, symbol='x-thin',
                                line=dict(width=3, color='red'))
                ))

                fig_pr.add_annotation(
                    text=f"AUC-PR = {pr['auc_pr']:.4f}",
                    xref="paper", yref="paper", x=0.97, y=0.06,
                    showarrow=False, font=dict(size=13, color="white"),
                    bgcolor="rgba(0,0,0,0.6)", borderpad=6
                )
                fig_pr.update_layout(
                    template="plotly_dark",
                    xaxis_title="Recall", yaxis_title="Précision",
                    xaxis=dict(range=[0, 1]), yaxis=dict(range=[0, 1]),
                    title="Courbe PR — jeu de test (évaluation hors entraînement)"
                )
                st.plotly_chart(fig_pr, use_container_width=True)
            else:
                st.info("Données PR curve non disponibles — relancer l'entraînement pour les générer.")

        with c2:
            st.subheader("Distribution des scores de fraude")
            df_scores = df.dropna(subset=['prediction_score', 'is_alerted']).copy()
            if not df_scores.empty:
                threshold = artifacts.get('threshold', 0.5) if artifacts else 0.5

                fig_hist = go.Figure()
                fig_hist.add_trace(go.Histogram(
                    x=df_scores[df_scores['is_alerted'] == False]['prediction_score'],
                    name='Normal', opacity=0.7,
                    marker_color='#2ecc71', nbinsx=50
                ))
                fig_hist.add_trace(go.Histogram(
                    x=df_scores[df_scores['is_alerted'] == True]['prediction_score'],
                    name='Fraude alertée', opacity=0.7,
                    marker_color='#e74c3c', nbinsx=50
                ))
                fig_hist.add_vline(
                    x=threshold, line_dash="dash", line_color="white",
                    annotation_text=f"Seuil ({threshold:.2f})",
                    annotation_position="top right"
                )
                fig_hist.update_layout(
                    barmode='overlay', template="plotly_dark",
                    xaxis_title="Score de fraude (probabilité)",
                    yaxis_title="Nombre de transactions",
                    title="Distribution des scores par classe"
                )
                st.plotly_chart(fig_hist, use_container_width=True)
            else:
                st.info("Scores non disponibles pour cette période.")

    # ── Tab 3 : Rapports journaliers ────────────────────────────────────────
    with tab3:
        RAPPORTS_DIR = '/opt/airflow/data/rapports'
        if not os.path.isdir(RAPPORTS_DIR):
            RAPPORTS_DIR = 'data/rapports'  # fallback local

        rapports = sorted(
            [f for f in os.listdir(RAPPORTS_DIR) if f.endswith('.csv')],
            reverse=True
        ) if os.path.isdir(RAPPORTS_DIR) else []

        if not rapports:
            st.info("Aucun rapport disponible — déclencher le DAG `rapport_quotidien` pour en générer un.")
        else:
            rapport_choisi = st.selectbox("Sélectionner un rapport", rapports)
            df_rapport = pd.read_csv(os.path.join(RAPPORTS_DIR, rapport_choisi))

            total_r = len(df_rapport)
            fraudes_r = df_rapport[df_rapport['is_alerted'] == True]
            nb_fraudes_r = len(fraudes_r)
            taux_r = (nb_fraudes_r / total_r * 100) if total_r > 0 else 0
            volume_r = df_rapport['amount'].sum()
            volume_fraudes_r = fraudes_r['amount'].sum() if nb_fraudes_r > 0 else 0

            # KPIs du rapport
            k1, k2, k3, k4, k5 = st.columns(5)
            k1.metric("Transactions", f"{total_r:,}")
            k2.metric("Fraudes détectées", nb_fraudes_r)
            k3.metric("Taux de fraude", f"{taux_r:.2f}%")
            k4.metric("Volume total", f"{volume_r:,.0f} EUR")
            k5.metric("Volume frauduleux", f"{volume_fraudes_r:,.0f} EUR")

            st.divider()
            c1, c2 = st.columns(2)

            with c1:
                # Fraudes par catégorie
                cat_r = df_rapport.groupby('category').agg(
                    total=('is_alerted', 'count'),
                    fraudes=('is_alerted', 'sum')
                ).reset_index()
                cat_r = cat_r[cat_r['fraudes'] > 0].sort_values('fraudes', ascending=False)
                cat_r['taux'] = cat_r['fraudes'] / cat_r['total'] * 100
                if not cat_r.empty:
                    fig_cat_r = px.bar(
                        cat_r, x='category', y='fraudes',
                        title="Fraudes détectées par catégorie",
                        template="plotly_dark", color='taux',
                        color_continuous_scale='Reds',
                        labels={'fraudes': 'Nb fraudes', 'category': 'Catégorie', 'taux': 'Taux (%)'}
                    )
                    fig_cat_r.update_layout(coloraxis_showscale=False)
                    st.plotly_chart(fig_cat_r, use_container_width=True)
                else:
                    st.info("Aucune fraude détectée dans ce rapport.")

            with c2:
                # Distribution des scores
                df_r_scores = df_rapport.dropna(subset=['prediction_score', 'is_alerted'])
                if not df_r_scores.empty:
                    fig_hist_r = go.Figure()
                    fig_hist_r.add_trace(go.Histogram(
                        x=df_r_scores[df_r_scores['is_alerted'] == False]['prediction_score'],
                        name='Normal', opacity=0.7, marker_color='#2ecc71', nbinsx=40
                    ))
                    fig_hist_r.add_trace(go.Histogram(
                        x=df_r_scores[df_r_scores['is_alerted'] == True]['prediction_score'],
                        name='Fraude', opacity=0.7, marker_color='#e74c3c', nbinsx=40
                    ))
                    fig_hist_r.update_layout(
                        barmode='overlay', template="plotly_dark",
                        xaxis_title="Score de fraude",
                        yaxis_title="Fréquence",
                        title="Distribution des scores"
                    )
                    st.plotly_chart(fig_hist_r, use_container_width=True)
