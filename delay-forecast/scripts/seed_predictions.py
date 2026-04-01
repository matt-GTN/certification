"""
Génère 100 appels à l'API /predict avec des combinaisons aléatoires
qui matchent réellement stg_transport_archive (bus 541).

Usage :
    python scripts/seed_predictions.py
    python scripts/seed_predictions.py --url http://localhost:8000 --n 200
"""

import argparse
import asyncio
import os
import random
from datetime import datetime, timedelta

import httpx
import psycopg2
from dotenv import load_dotenv

load_dotenv()

API_URL    = os.getenv("API_URL", "http://localhost:8000")
DB_URL     = os.getenv("DATABASE_URL")
BUS_NBR    = "541"
CONCURRENCY = 10          # appels simultanés max


def get_valid_combinations() -> list[dict]:
    """Récupère les combinaisons (direction_id, stop_sequence, day_of_week, hour)
    qui existent dans stg_transport_archive pour le bus 541."""
    conn = psycopg2.connect(DB_URL)
    cur  = conn.cursor()
    cur.execute("""
        SELECT DISTINCT
            direction_id,
            stop_sequence,
            MOD(EXTRACT(DOW FROM timestamp_rounded)::int + 6, 7) AS day_of_week,
            EXTRACT(HOUR FROM timestamp_rounded)::int              AS hour
        FROM stg_transport_archive
        WHERE bus_nbr::text = %s
        ORDER BY direction_id, stop_sequence, day_of_week, hour;
    """, (BUS_NBR,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [
        {"direction_id": int(r[0]), "stop_sequence": int(r[1]),
         "day_of_week": int(r[2]), "hour": int(r[3])}
        for r in rows
    ]


def day_of_week_to_recent_date(dow: int, hour: int) -> tuple[int, int]:
    """Retourne (month, day) d'une date récente (>= 3 jours passés)
    correspondant au jour de la semaine donné — pour garantir
    que l'API météo utilise l'archive (pas de données futures)."""
    today = datetime.utcnow().date()
    # On part de J-3 pour être sûr que l'archive météo est disponible
    anchor = today - timedelta(days=3)
    # Reculer jusqu'au bon jour de semaine (0=Lun)
    days_back = (anchor.weekday() - dow) % 7
    target = anchor - timedelta(days=days_back)
    return target.month, target.day


async def call_predict(client: httpx.AsyncClient, payload: dict, idx: int) -> dict:
    try:
        r = await client.post(f"{API_URL}/predict", json=payload, timeout=20)
        if r.status_code == 200:
            print(f"[{idx:>3}] OK   — {payload['direction_id']} dir | "
                  f"stop {payload['stop_sequence']:>2} | "
                  f"dow {payload['day_of_week']} h{payload['hour']:>2} "
                  f"→ P50={r.json()['prediction_P50']:.0f}s")
            return {"status": "ok", **r.json()}
        else:
            print(f"[{idx:>3}] ERR {r.status_code} — {r.text[:80]}")
            return {"status": "error", "code": r.status_code}
    except Exception as e:
        print(f"[{idx:>3}] EXC — {e}")
        return {"status": "exception", "error": str(e)}


async def main(api_url: str, n: int):
    print(f"Récupération des combinaisons valides depuis stg_transport_archive...")
    combos = get_valid_combinations()
    print(f"  → {len(combos)} combinaisons distinctes trouvées pour bus {BUS_NBR}\n")

    if not combos:
        print("Aucune donnée dans stg_transport_archive pour ce bus. Abandon.")
        return

    # Échantillonnage avec remplacement si n > len(combos)
    sample = random.choices(combos, k=n)

    payloads = []
    for combo in sample:
        month, day = day_of_week_to_recent_date(combo["day_of_week"], combo["hour"])
        payloads.append({
            "bus_nbr":      BUS_NBR,
            "direction_id": combo["direction_id"],
            "stop_sequence": combo["stop_sequence"],
            "day_of_week":  combo["day_of_week"],
            "hour":         combo["hour"],
            "month":        month,
            "day":          day,
        })

    print(f"Lancement de {n} appels vers {api_url}/predict "
          f"(concurrence : {CONCURRENCY})\n")

    sem = asyncio.Semaphore(CONCURRENCY)

    async def bounded(client, payload, idx):
        async with sem:
            return await call_predict(client, payload, idx)

    async with httpx.AsyncClient() as client:
        tasks   = [bounded(client, p, i + 1) for i, p in enumerate(payloads)]
        results = await asyncio.gather(*tasks)

    ok  = sum(1 for r in results if r["status"] == "ok")
    err = n - ok
    print(f"\n{'─'*50}")
    print(f"Terminé : {ok}/{n} succès, {err} erreurs")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=API_URL, help="URL de l'API")
    parser.add_argument("--n",   default=100, type=int, help="Nombre d'appels")
    args = parser.parse_args()

    asyncio.run(main(args.url, args.n))
