import logging
from datetime import datetime, date
from dotenv import load_dotenv

from pipeline.transport.utils.call_api_transport import call_rt_history_api, call_rt_reference_api
from pipeline.transport.utils.read_data_transport import read_koda_reference_data
from pipeline.transport.utils.filter_route_transport import filter_by_bus_route
from pipeline.transport.utils.transform_data_transport import transform_S3_to_neon
from pipeline.transport.utils.load_to_neon_transport import load_parquet_to_neon

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("RUN_TRANSPORT")

bus_number = "541"
max_bus_per_hour = 3

load_dotenv()

from google.transit import gtfs_realtime_pb2

# Realtime
r_history = call_rt_history_api()
feed = gtfs_realtime_pb2.FeedMessage()
feed.ParseFromString(r_history.content)
history_entities = list(feed.entity)

# Reference
r_reference = call_rt_reference_api()
reference_routes = read_koda_reference_data(r_reference, "routes")
reference_trips = read_koda_reference_data(r_reference, "trips")

# Filtrage par ligne de bus
filtered_data = filter_by_bus_route(
    bus_number, reference_routes, reference_trips, history_entities, max_bus_per_hour
)

logger.info("Entités GTFS-RT : %d", len(history_entities))
logger.info("Données filtrées : %d", len(filtered_data))

# Transformation et chargement
data_transformed = transform_S3_to_neon(filtered_data)
logger.info("Données transformées : %d lignes", len(data_transformed))

load_parquet_to_neon("stg_transport_realtime", data_transformed, realtime=True)
logger.info("Chargement vers Neon terminé")
