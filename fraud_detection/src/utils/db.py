import os
import pandas as pd
from sqlalchemy import create_engine

# Connexion unifiée via DATABASE_URL (Neon PostgreSQL cloud)
# Fallback sur PostgreSQL local pour le développement sans Neon
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost:5433/fraud_detection"
)


def get_engine():
    """Crée et retourne un moteur de connexion SQLAlchemy (Neon PostgreSQL)."""
    return create_engine(DATABASE_URL, connect_args={"sslmode": "require"} if "neon.tech" in DATABASE_URL else {})


def load_data_to_db(df: pd.DataFrame, table_name: str, if_exists: str = "append"):
    """Charge un DataFrame pandas dans la base de données."""
    engine = get_engine()
    with engine.connect() as conn:
        df.to_sql(table_name, conn, if_exists=if_exists, index=False)
        conn.commit()
        print(f"Données chargées avec succès dans {table_name}")


def fetch_data_from_db(query: str) -> pd.DataFrame:
    """Exécute une requête SQL et retourne un DataFrame."""
    engine = get_engine()
    return pd.read_sql(query, engine)
