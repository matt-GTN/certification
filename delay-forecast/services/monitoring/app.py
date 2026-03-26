import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import time

# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────
API_URL       = os.getenv("API_URL",       "http://api:8000")
MLFLOW_URL    = os.getenv("MLFLOW_URL",    "http://mlflow:5000")
EVIDENTLY_URL = os.getenv("EVIDENTLY_URL", "http://evidently:8001")
AIRFLOW_URL   = os.getenv("AIRFLOW_URL",   "http://airflow-webserver:8080")
DB_URL        = os.getenv("DATABASE_URL",  "")

TEAL  = "#2dd4bf"
TEAL2 = "#0d9488"
BG    = "#0f172a"
CARD  = "#1e293b"
TEXT  = "#e2e8f0"
MUTED = "#94a3b8"

st.set_page_config(
    page_title="Delay Forecast Monitor",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(f"""
<style>
  /* global */
  html, body, [class*="css"] {{ background-color: {BG}; color: {TEXT}; font-family: 'Inter', sans-serif; }}
  .block-container {{ padding-top: 2rem; padding-bottom: 2rem; }}

  /* headings */
  h1, h2, h3 {{ color: {TEXT} !important; }}
  h1 {{ border-bottom: 2px solid {TEAL}; padding-bottom: 0.4rem; margin-bottom: 1.2rem; }}
  h3 {{ color: {TEAL} !important; margin-top: 1.8rem; margin-bottom: 0.6rem; }}

  /* service cards */
  .svc-card {{
    background: {CARD};
    border-radius: 10px;
    padding: 18px 20px;
    border-left: 4px solid {TEAL};
    height: 100%;
  }}
  .svc-card.down {{ border-left-color: #f87171; }}
  .svc-name  {{ font-size: 0.95rem; font-weight: 600; color: {TEXT}; }}
  .svc-port  {{ font-size: 0.78rem; color: {MUTED}; margin: 2px 0 10px; }}
  .badge-up  {{ background: {TEAL}; color: {BG}; border-radius: 5px; padding: 2px 9px;
                font-size: 0.75rem; font-weight: 700; }}
  .badge-down {{ background: #f87171; color: {BG}; border-radius: 5px; padding: 2px 9px;
                 font-size: 0.75rem; font-weight: 700; }}

  /* stat metrics override */
  [data-testid="stMetric"] label {{ color: {MUTED} !important; font-size: 0.82rem; }}
  [data-testid="stMetricValue"] {{ color: {TEAL} !important; font-size: 1.6rem; font-weight: 700; }}

  /* divider */
  hr {{ border: none; border-top: 1px solid #334155; margin: 2rem 0; }}

  /* form inputs */
  [data-testid="stNumberInput"] input,
  [data-testid="stTextInput"] input,
  [data-baseweb="select"] {{ background: {CARD} !important; color: {TEXT} !important; }}

  /* prediction result box */
  .pred-card {{
    background: {CARD};
    border: 1px solid {TEAL};
    border-radius: 10px;
    padding: 24px 28px;
    margin-top: 12px;
  }}
  .pred-val {{
    font-size: 2.4rem;
    font-weight: 800;
    color: {TEAL};
    line-height: 1.1;
  }}
  .pred-label {{
    font-size: 0.8rem;
    color: {MUTED};
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def check_service(url: str, path: str = "/health", timeout: int = 3):
    try:
        r = requests.get(f"{url}{path}", timeout=timeout)
        return r.status_code == 200, r
    except Exception as e:
        return False, str(e)


def get_db_engine():
    if not DB_URL:
        return None
    try:
        from sqlalchemy import create_engine
        return create_engine(DB_URL)
    except Exception:
        return None


@st.cache_data(ttl=60)
def load_prediction_logs(limit: int = 500):
    engine = get_db_engine()
    if engine is None:
        return pd.DataFrame()
    try:
        df = pd.read_sql(
            f"""
            SELECT p.*, g.actual_delay
            FROM prediction_logs p
            LEFT JOIN ground_truth g ON g.prediction_log_id = p.id
            ORDER BY p.timestamp DESC
            LIMIT {limit}
            """,
            engine,
        )
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df
    except Exception as e:
        st.error(f"DB error: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=30)
def get_evidently_reports():
    try:
        r = requests.get(f"{EVIDENTLY_URL}/reports", timeout=5)
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []


def plotly_defaults(fig):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color=TEXT,
        font_size=12,
        margin=dict(l=0, r=0, t=30, b=0),
        xaxis=dict(gridcolor="#1e293b", linecolor="#334155"),
        yaxis=dict(gridcolor="#1e293b", linecolor="#334155"),
    )
    return fig


# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
col_title, col_refresh = st.columns([6, 1])
with col_title:
    st.markdown("# Delay Forecast — Monitoring")
with col_refresh:
    st.markdown("<div style='margin-top:12px'>", unsafe_allow_html=True)
    if st.button("Rafraichir", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SECTION 1 — SERVICES HEALTH
# ─────────────────────────────────────────────
st.markdown("### Services")
services = [
    ("API FastAPI",  API_URL,       "/",       "8000"),
    ("MLflow",       MLFLOW_URL,    "/health", "5000"),
    ("Evidently",    EVIDENTLY_URL, "/health", "8001"),
    ("Airflow",      AIRFLOW_URL,   "/health", "8080"),
]

svc_cols = st.columns(4)
for i, (name, url, path, port) in enumerate(services):
    ok, _ = check_service(url, path)
    badge = f'<span class="badge-{"up" if ok else "down"}">{"✔ UP" if ok else "✘ DOWN"}</span>'
    card_class = "svc-card" if ok else "svc-card down"
    with svc_cols[i]:
        st.markdown(
            f"""<div class="{card_class}">
            <div class="svc-name">{name}</div>
            <div class="svc-port">localhost:{port}</div>
            {badge}
            </div>""",
            unsafe_allow_html=True,
        )

# Quick stats
st.markdown("### Statistiques globales")
df = load_prediction_logs(1000)

m1, m2, m3, m4 = st.columns(4)
if df.empty:
    for c in [m1, m2, m3, m4]:
        with c:
            st.metric("—", "N/A")
else:
    with m1:
        st.metric("Total predictions", f"{len(df):,}")
    with m2:
        if "timestamp" in df.columns:
            today = df[df["timestamp"] >= pd.Timestamp.utcnow().replace(tzinfo=None).normalize()]
            st.metric("Predictions aujourd'hui", len(today))
        else:
            st.metric("Predictions aujourd'hui", "—")
    with m3:
        if "prediction_P50" in df.columns:
            st.metric("Retard median P50", f"{df['prediction_P50'].mean():.1f}s")
        else:
            st.metric("Retard median P50", "—")
    with m4:
        if "actual_delay" in df.columns and df["actual_delay"].notna().any():
            gt = df[df["actual_delay"].notna()]
            mae = (gt["prediction_P50"] - gt["actual_delay"]).abs().mean()
            st.metric("MAE actuelle", f"{mae:.1f}s")
        else:
            st.metric("Ground truth", "—")

st.markdown("<hr>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SECTION 2 — PREDICTION LIVE
# ─────────────────────────────────────────────
st.markdown("### Prediction live")

api_ok, _ = check_service(API_URL, "/")
if not api_ok:
    st.error("API non disponible.")
else:
    with st.form("predict_form"):
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            direction_id  = st.selectbox("Direction", [0, 1], index=1)
            month         = st.slider("Mois", 1, 12, datetime.now().month)
            day           = st.slider("Jour", 1, 31, datetime.now().day)
        with fc2:
            hour          = st.slider("Heure", 0, 23, datetime.now().hour)
            day_of_week   = st.selectbox(
                "Jour de la semaine",
                list(range(7)),
                format_func=lambda x: ["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"][x],
                index=datetime.now().weekday(),
            )
        with fc3:
            bus_nbr        = st.text_input("Numero de bus", value="541")
            stop_sequence  = st.number_input("Sequence d'arret", min_value=1, max_value=50, value=1)

        submitted = st.form_submit_button("Lancer la prediction", use_container_width=True, type="primary")

    if submitted:
        payload = {
            "direction_id": direction_id,
            "month": month,
            "day": day,
            "hour": hour,
            "day_of_week": day_of_week,
            "bus_nbr": bus_nbr,
            "stop_sequence": stop_sequence,
        }
        with st.spinner("Appel API en cours..."):
            try:
                t0 = time.time()
                r  = requests.post(f"{API_URL}/predict", json=payload, timeout=15)
                latency = (time.time() - t0) * 1000

                if r.status_code == 200:
                    res = r.json()
                    p50, p80, p90 = res["prediction_P50"], res["prediction_P80"], res["prediction_P90"]

                    st.markdown(f"<small style='color:{MUTED}'>Reponse en {latency:.0f}ms</small>", unsafe_allow_html=True)

                    rc1, rc2, rc3 = st.columns(3)
                    for col, label, val, delta_base in [
                        (rc1, "P50 — Mediane",    p50, None),
                        (rc2, "P80 — Pessimiste", p80, p50),
                        (rc3, "P90 — Extreme",    p90, p50),
                    ]:
                        with col:
                            delta_str = f"+{val - delta_base:.1f}s vs P50" if delta_base else None
                            st.markdown(
                                f"""<div class="pred-card">
                                <div class="pred-label">{label}</div>
                                <div class="pred-val">{val:.1f}s</div>
                                {"<div style='font-size:0.82rem;color:"+MUTED+"'>"+delta_str+"</div>" if delta_str else ""}
                                </div>""",
                                unsafe_allow_html=True,
                            )

                    fig_pred = go.Figure(go.Bar(
                        x=["P50", "P80", "P90"],
                        y=[p50, p80, p90],
                        marker_color=[TEAL, TEAL2, "#0f766e"],
                        text=[f"{v:.1f}s" for v in [p50, p80, p90]],
                        textposition="outside",
                    ))
                    fig_pred.update_layout(
                        title="Retard predit par quantile (secondes)",
                        yaxis_title="Retard (s)",
                        showlegend=False,
                        height=320,
                    )
                    st.plotly_chart(plotly_defaults(fig_pred), use_container_width=True)

                else:
                    st.error(f"Erreur {r.status_code} : {r.text}")
            except Exception as e:
                st.error(f"Erreur de connexion : {e}")

st.markdown("<hr>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SECTION 3 — GRAPHIQUES
# ─────────────────────────────────────────────
st.markdown("### Analyse des predictions")

if df.empty:
    st.info("Aucune donnee disponible (base de donnees non accessible).")
else:
    n_show = st.slider("Nombre de predictions a afficher", 50, 1000, 200, step=50, key="chart_n")
    df_view = df.head(n_show).copy()

    # Row 1 — activity + quantile distributions
    row1_left, row1_right = st.columns(2)

    with row1_left:
        if "timestamp" in df_view.columns:
            df_hourly = df_view.copy()
            df_hourly["heure"] = df_hourly["timestamp"].dt.floor("H")
            activity = df_hourly.groupby("heure").size().reset_index(name="predictions")
            fig_act = px.bar(
                activity, x="heure", y="predictions",
                title="Activite par heure",
                color_discrete_sequence=[TEAL],
            )
            fig_act.update_layout(xaxis_title="", yaxis_title="Nb predictions", height=320)
            st.plotly_chart(plotly_defaults(fig_act), use_container_width=True)
        else:
            st.info("Pas de timestamp disponible.")

    with row1_right:
        quant_cols = [c for c in ["prediction_P50", "prediction_P80", "prediction_P90"] if c in df_view.columns]
        if quant_cols:
            fig_dist = go.Figure()
            colors = [TEAL, TEAL2, "#0f766e"]
            for col, color in zip(quant_cols, colors):
                fig_dist.add_trace(go.Histogram(
                    x=df_view[col].dropna(),
                    name=col.replace("prediction_", ""),
                    opacity=0.7,
                    marker_color=color,
                    nbinsx=30,
                ))
            fig_dist.update_layout(
                title="Distribution des quantiles de retard",
                barmode="overlay",
                xaxis_title="Retard (s)",
                yaxis_title="Frequence",
                height=320,
                legend=dict(orientation="h", y=1.1),
            )
            st.plotly_chart(plotly_defaults(fig_dist), use_container_width=True)

    # Row 2 — MAE by hour + retard by day of week
    row2_left, row2_right = st.columns(2)

    with row2_left:
        if "actual_delay" in df_view.columns and df_view["actual_delay"].notna().any() and "hour" in df_view.columns:
            gt_df = df_view[df_view["actual_delay"].notna()].copy()
            gt_df["mae"] = (gt_df["prediction_P50"] - gt_df["actual_delay"]).abs()
            mae_by_hour = gt_df.groupby("hour")["mae"].mean().reset_index()
            fig_mae = px.bar(
                mae_by_hour, x="hour", y="mae",
                title="MAE par heure de la journee",
                labels={"hour": "Heure", "mae": "MAE (s)"},
                color_discrete_sequence=[TEAL],
            )
            fig_mae.update_layout(height=300)
            st.plotly_chart(plotly_defaults(fig_mae), use_container_width=True)
        elif "hour" in df_view.columns and "prediction_P50" in df_view.columns:
            avg_by_hour = df_view.groupby("hour")["prediction_P50"].mean().reset_index()
            fig_hour = px.bar(
                avg_by_hour, x="hour", y="prediction_P50",
                title="Retard P50 moyen par heure",
                labels={"hour": "Heure", "prediction_P50": "Retard moyen (s)"},
                color_discrete_sequence=[TEAL],
            )
            fig_hour.update_layout(height=300)
            st.plotly_chart(plotly_defaults(fig_hour), use_container_width=True)

    with row2_right:
        if "day_of_week" in df_view.columns and "prediction_P50" in df_view.columns:
            days = ["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"]
            avg_by_day = df_view.groupby("day_of_week")["prediction_P50"].mean().reset_index()
            avg_by_day["jour"] = avg_by_day["day_of_week"].apply(lambda x: days[x] if x < 7 else str(x))
            fig_day = px.bar(
                avg_by_day, x="jour", y="prediction_P50",
                title="Retard P50 moyen par jour de la semaine",
                labels={"jour": "", "prediction_P50": "Retard moyen (s)"},
                color_discrete_sequence=[TEAL2],
            )
            fig_day.update_layout(height=300)
            st.plotly_chart(plotly_defaults(fig_day), use_container_width=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SECTION 4 — EVIDENTLY
# ─────────────────────────────────────────────
st.markdown("### Evidently — Drift & Qualite")

ev_ok, _ = check_service(EVIDENTLY_URL, "/health")
if not ev_ok:
    st.error("Service Evidently non disponible.")
else:
    # ── Colonnes features utilisées pour le drift ──────────────────────────
    DRIFT_FEATURE_COLS = [
        "direction_id", "month", "day", "hour", "day_of_week", "stop_sequence",
        "temperature_2m", "precipitation", "rain", "snowfall", "cloud_cover",
        "wind_speed_10m", "wind_gusts_10m", "est_weekend", "est_jour_ferie",
        "vacances_scolaires", "risque_gel_pluie", "risque_gel_neige",
    ]

    def df_to_evidently_payload(dataframe: pd.DataFrame) -> list[dict]:
        cols = [c for c in DRIFT_FEATURE_COLS if c in dataframe.columns]
        return dataframe[cols].dropna().to_dict(orient="records")

    # ── Statut reference ───────────────────────────────────────────────────
    try:
        ref = requests.get(f"{EVIDENTLY_URL}/reference/status", timeout=5).json()
        ref_is_set = ref.get("status") == "set"
    except Exception:
        ref = {}
        ref_is_set = False

    if ref_is_set:
        st.success(f"✔ Donnees de reference definies — {ref.get('rows', '?')} lignes, {len(ref.get('columns', []))} colonnes")
    else:
        st.warning("Aucune donnee de reference en memoire. Definissez-en une ci-dessous (perdu au redemarrage du conteneur).")

    # ── Definir les donnees de reference ──────────────────────────────────
    with st.expander("Definir les donnees de reference depuis la base de donnees"):
        ref_n = st.slider("Nombre de predictions historiques a utiliser comme reference", 100, 2000, 500, step=100)
        if st.button("Charger et definir comme reference", use_container_width=True):
            df_ref_src = load_prediction_logs(ref_n * 2)  # charge plus, prend la moitie la plus ancienne
            if df_ref_src.empty:
                st.error("Impossible de charger les donnees depuis la base.")
            else:
                df_ref_data = df_ref_src.tail(ref_n)  # les plus anciennes = reference
                payload_ref = df_to_evidently_payload(df_ref_data)
                if not payload_ref:
                    st.error("Aucune colonne compatible trouvee dans la base.")
                else:
                    try:
                        r = requests.post(f"{EVIDENTLY_URL}/reference", json={"data": payload_ref}, timeout=15)
                        if r.status_code == 200:
                            st.success(f"✔ Reference definie — {len(payload_ref)} lignes")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(f"Erreur : {r.text}")
                    except Exception as e:
                        st.error(str(e))

    # ── Actions ────────────────────────────────────────────────────────────
    act1, act2, act3 = st.columns(3)

    def get_current_data_payload(n: int = 200) -> list[dict] | None:
        df_cur = load_prediction_logs(n)
        if df_cur.empty:
            return None
        return df_to_evidently_payload(df_cur.head(n))

    with act1:
        if st.button("Generer rapport de drift", use_container_width=True, disabled=not ref_is_set):
            data = get_current_data_payload()
            if not data:
                st.error("Pas de donnees courantes disponibles.")
            else:
                with st.spinner("Generation en cours..."):
                    try:
                        r = requests.post(f"{EVIDENTLY_URL}/drift/report", json={"data": data}, timeout=30)
                        if r.status_code == 200:
                            res = r.json()
                            if res.get("drift_detected"):
                                st.error(f"✘ Drift detecte — {res.get('drift_share', 0):.1%} (seuil : {res.get('threshold', 0):.1%})")
                            else:
                                st.success(f"✔ Pas de drift — {res.get('drift_share', 0):.1%}")
                            st.cache_data.clear()
                        else:
                            st.error(r.text)
                    except Exception as e:
                        st.error(str(e))

    with act2:
        if st.button("Generer rapport de qualite", use_container_width=True):
            data = get_current_data_payload()
            if not data:
                st.error("Pas de donnees courantes disponibles.")
            else:
                with st.spinner("Generation en cours..."):
                    try:
                        r = requests.post(f"{EVIDENTLY_URL}/quality/report", json={"data": data}, timeout=30)
                        if r.status_code == 200:
                            st.success(f"✔ {r.json().get('report_filename', 'Rapport genere')}")
                            st.cache_data.clear()
                        else:
                            st.error(r.text)
                    except Exception as e:
                        st.error(str(e))

    with act3:
        if st.button("Lancer les tests de drift", use_container_width=True, disabled=not ref_is_set):
            data = get_current_data_payload()
            if not data:
                st.error("Pas de donnees courantes disponibles.")
            else:
                with st.spinner("Tests en cours..."):
                    try:
                        r = requests.post(f"{EVIDENTLY_URL}/drift/test", json={"data": data}, timeout=30)
                        if r.status_code == 200:
                            res = r.json()
                            if res.get("all_tests_passed"):
                                st.success("✔ Tous les tests ont passe")
                            else:
                                st.error("✘ Certains tests ont echoue")
                            st.cache_data.clear()
                        else:
                            st.error(r.text)
                    except Exception as e:
                        st.error(str(e))

    # Report viewer
    reports = get_evidently_reports()
    reports_list = reports if isinstance(reports, list) else reports.get("reports", [])
    # /reports renvoie une liste de dicts {filename, created_at, size_kb}
    # on normalise pour obtenir une liste de dicts dans tous les cas
    if reports_list and isinstance(reports_list[0], str):
        reports_list = [{"filename": f, "created_at": "", "size_kb": 0} for f in reports_list]

    if reports_list:
        st.markdown(f"<small style='color:{MUTED}'>{len(reports_list)} rapport(s) disponible(s)</small>", unsafe_allow_html=True)
        options = {
            f"{r['filename']}  ({r.get('created_at','')[:19]}  —  {r.get('size_kb',0):.0f} KB)": r["filename"]
            for r in reversed(reports_list)
        }
        selected_label = st.selectbox("Visualiser un rapport", ["— Choisir —"] + list(options.keys()))
        if selected_label and selected_label != "— Choisir —":
            filename = options[selected_label]
            # lien cliquable pour l'utilisateur (URL hôte, pas Docker interne)
            st.markdown(f"[Ouvrir dans un nouvel onglet](http://localhost:8001/reports/{filename})")
            try:
                # fetch server-side (EVIDENTLY_URL interne Docker accessible depuis Streamlit)
                html_content = requests.get(f"{EVIDENTLY_URL}/reports/{filename}", timeout=15).text
                st.components.v1.html(html_content, height=750, scrolling=True)
            except Exception as e:
                st.error(f"Impossible de charger le rapport : {e}")
    else:
        st.info("Aucun rapport disponible. Generez-en un ci-dessus.")
