import logging
from prometheus_api_client import PrometheusConnect

logger = logging.getLogger(__name__)

class PrometheusClient:

    def __init__(self, url: str):
        self.url = url
        logger.info(f"Prometheus client initialized with URL: {url}")
    
    def fetch_metrics(self, query: str, timeout: int = 10) -> float:
        try:
            prometheus = PrometheusConnect(
                url=self.url,
                timeout=timeout,
                disable_ssl=True
            )
            # Initialize default number of requests to 0
            num_of_requests = 0.0

            logger.debug(f"Executing query: {query}")
            response = prometheus.custom_query(query=query)
            logger.info(f"Prometheus query returned: {response}")
            if response and len(response) > 0:
                num_of_requests = float(response[0]['value'][1])
                logger.info(f"Prometheus query returned: {num_of_requests} number of requests")
            return num_of_requests

        except Exception as e:
            logger.error(f"Error fetching metrics from Prometheus: {e}")
            return num_of_requests
