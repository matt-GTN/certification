import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.utils.db import get_engine

try:
    engine = get_engine()
    with engine.connect() as conn:
        print("Connexion réussie !")
except Exception as e:
    print(f"Échec de la connexion : {e}")
