from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import os
import logging
import json
import requests
import psycopg2
import pandas as pd
from dotenv import load_dotenv

logger = logging.getLogger("DAILY_PIPELINE")


def ingest_weather_forecast():
    """Ingestion des prévisions météo via Open-Meteo et stockage en base."""
    load_dotenv()
    DATABASE_URL = os.getenv("DATABASE_URL")

    LAT, LON = 59.3251172, 18.0710935
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": LAT,
        "longitude": LON,
        "hourly": "temperature_2m,precipitation,rain,snowfall,wind_speed_10m,cloud_cover,dew_point_2m",
        "timezone": "Europe/Stockholm",
        "forecast_days": 7,
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    hourly = data["hourly"]
    df = pd.DataFrame(hourly)
    df["time"] = pd.to_datetime(df["time"])

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    insert_query = """
        INSERT INTO stg_weather_forecast (time, temperature_2m, precipitation, rain, snowfall, wind_speed_10m, cloud_cover, dew_point_2m)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (time) DO UPDATE SET
            temperature_2m = EXCLUDED.temperature_2m,
            precipitation = EXCLUDED.precipitation,
            rain = EXCLUDED.rain,
            snowfall = EXCLUDED.snowfall,
            wind_speed_10m = EXCLUDED.wind_speed_10m,
            cloud_cover = EXCLUDED.cloud_cover,
            dew_point_2m = EXCLUDED.dew_point_2m;
    """

    for _, row in df.iterrows():
        cur.execute(insert_query, (
            row["time"], row["temperature_2m"], row["precipitation"],
            row["rain"], row["snowfall"], row["wind_speed_10m"],
            row["cloud_cover"], row["dew_point_2m"],
        ))

    conn.commit()
    cur.close()
    conn.close()
    logger.info("Prévisions météo ingérées : %d lignes", len(df))


def ingest_realtime_transport():
    """Ingestion des données temps réel transport via KöDa GTFS-RT."""
    load_dotenv()
    DATABASE_URL = os.getenv("DATABASE_URL")

    logger.info("Ingestion transport temps réel — bus 541 Stockholm")

    # Appel API KöDa realtime
    rt_url = "https://opendata.samtrafiken.se/gtfs-rt/sl/TripUpdates.pb"
    api_key = os.getenv("KODA_API_KEY", "")

    if not api_key:
        logger.warning("KODA_API_KEY non configurée — ingestion transport ignorée")
        return

    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(rt_url, headers=headers, timeout=30)
    response.raise_for_status()

    from google.transit import gtfs_realtime_pb2

    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(response.content)

    logger.info("Données GTFS-RT reçues : %d entités", len(feed.entity))


def check_data_freshness():
    """Vérifie que les données ont bien été mises à jour."""
    load_dotenv()
    DATABASE_URL = os.getenv("DATABASE_URL")

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(*), MAX(time)
        FROM stg_weather_forecast
        WHERE time >= NOW() - INTERVAL '24 hours';
    """)
    count, latest = cur.fetchone()
    logger.info("Données météo récentes : %d lignes, dernière : %s", count, latest)

    if count == 0:
        raise ValueError("Aucune donnée météo récente — pipeline potentiellement en erreur")

    cur.close()
    conn.close()


with DAG(
    dag_id="delay_forecast_daily",
    start_date=datetime(2025, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["poc", "ingestion"],
    doc_md="""
    ### Pipeline quotidien Delay Forecast
    1. Ingestion des prévisions météo (Open-Meteo → Neon)
    2. Ingestion des données transport temps réel (KöDa GTFS-RT)
    3. Vérification de la fraîcheur des données
    """,
) as dag:

    weather_task = PythonOperator(
        task_id="ingest_weather_forecast",
        python_callable=ingest_weather_forecast,
    )

    transport_task = PythonOperator(
        task_id="ingest_realtime_transport",
        python_callable=ingest_realtime_transport,
    )

    check_task = PythonOperator(
        task_id="check_data_freshness",
        python_callable=check_data_freshness,
    )

    [weather_task, transport_task] >> check_task
