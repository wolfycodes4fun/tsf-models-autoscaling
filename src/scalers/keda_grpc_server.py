from concurrent import futures
import grpc
import logging
import os
from src.scalers import externalscaler_pb2, externalscaler_pb2_grpc

from src.utils.prometheus_client import PrometheusClient
from src.scalers.scaling_logic import UncertaintyAwareScaler
from src.holt_winters import HoltWintersUncertainty

logger = logging.getLogger(__name__)

class UncertaintyAwareHWExternalScaler(externalscaler_pb2_grpc.ExternalScalerServicer):
    """
    KEDA external predictive scaler implementation with uncertainty awareness
    """

    def __init__(self):
        logger.info("Initializing Uncertainty-Aware Holt-Winters Scaler...")
        self.prometheus_client = PrometheusClient(url=os.getenv("PROMETHEUS_URL"))