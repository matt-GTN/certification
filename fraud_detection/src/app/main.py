import streamlit as st
import pandas as pd
import sys
import os
import plotly.express as px
from datetime import datetime, timedelta

# Chemin pour les utilitaires
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.utils.db import fetch_data_from_db

st.set_page_config(page_title="Tableau de Bord - Détection de Fraude", page_icon="🕵️", layout="wide")

st.title("🛡️ Détection de Fraude - Supervision Globale")
st.markdown("Tableau de bord de suivi des transactions et détection de fraude en temps réel.")

# Filtres dans la barre latérale
st.sidebar.header("Filtres")
days = st.sidebar.slider("Période (derniers jours)", 1, 30, 7)


@st.cache_data(ttl=60)  # Rafraîchissement toutes les 60 secondes
def load_dashboard_data(days_limit):
    """Charge les données du tableau de bord avec jointure transactions/prédictions."""
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


df = load_dashboard_data(days)

if df.empty:
    st.warning("Aucune donnée trouvée pour cette période.")
else:
    # Indicateurs clés de performance (KPI)
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

    # Graphiques
    st.subheader("Évolution des transactions")
    df['date'] = pd.to_datetime(df['timestamp']).dt.date
    daily_stats = df.groupby('date').size().reset_index(name='count')
    fig_line = px.line(daily_stats, x='date', y='count', title="Transactions par jour", template="plotly_dark")
    st.plotly_chart(fig_line, use_container_width=True)

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Répartition par catégorie")
        cat_stats = df.groupby('category').size().reset_index(name='count').sort_values('count', ascending=False)
        fig_pie = px.pie(cat_stats, values='count', names='category', title="Catégories principales", template="plotly_dark")
        st.plotly_chart(fig_pie, use_container_width=True)

    with c2:
        st.subheader("Dernières alertes de fraude")
        if nb_frauds > 0:
            st.dataframe(frauds[['timestamp', 'amount', 'category', 'prediction_score']].head(10), use_container_width=True)
        else:
            st.info("Aucune fraude détectée sur cette période.")

    # Tableau complet des données
    st.subheader("Toutes les transactions")
    st.dataframe(df.head(100), use_container_width=True)
