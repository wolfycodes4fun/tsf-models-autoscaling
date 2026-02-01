import logging
from typing import Optional
from prometheus_api_client import PrometheusConnect

logger = logging.getLogger(__name__)

class PrometheusClient:

    def __init__(self, url: Optional[str] = None):
        self.url = url
        logger.info(f"Prometheus client initialized with URL: {url}")