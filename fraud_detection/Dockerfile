FROM apache/airflow:2.8.1-python3.10

# libgomp1 : dépendance système de LightGBM (OpenMP), absente de l'image Airflow de base
USER root
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 && rm -rf /var/lib/apt/lists/*

USER airflow

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
