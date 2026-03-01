from prometheus_api_client import PrometheusConnect
import logging

logger = logging.getLogger(__name__)

class PrometheusClient:
    """
    Client for querying Prometheus for metrics. Wraps PrometheusConnect and exposes a single method
    fetch_metrics which returns a float value (ex- the request count) or 0.0 if no data is returned.
    """
    def __init__(self, server_address: str, timeout: int = 10):
        self.prometheus_client = PrometheusConnect(
            url = server_address,
            disable_ssl=True,
            timeout=timeout
        )
        logger.info(f"Prometheus client initialized with URL: {server_address}")
    
    def fetch_metrics(self, query: str) -> float:
        logger.debug(f"Executing query: {query}")
        metric_data = self.prometheus_client.custom_query(query=query)

        number_of_requests = 0.0

        if metric_data:
            number_of_requests = float(metric_data[0]['value'][1])
            logger.info(f"Prometheus query returned {number_of_requests} number of requests")
        else:
            logger.warning("No data was returned from Prometheus query hence returning 0.0")

        return number_of_requests
