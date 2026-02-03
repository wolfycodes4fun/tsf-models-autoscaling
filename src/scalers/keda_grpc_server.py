from concurrent import futures
import grpc
import logging
import os
import time
from src.scalers import externalscaler_pb2, externalscaler_pb2_grpc

from src.utils.prometheus_client import PrometheusClient
from src.scalers.scaling_logic import UncertaintyAwareScaler
from src.holt_winters import create_holt_winters_model

logger = logging.getLogger(__name__)

class UncertaintyAwareHWExternalScaler(externalscaler_pb2_grpc.ExternalScalerServicer):
    """
    KEDA external predictive scaler implementation with uncertainty awareness
    """

    def __init__(self):
        logger.info("Initializing Uncertainty-Aware Holt-Winters Scaler...")
        self.prometheus_client = PrometheusClient(url=os.getenv("PROMETHEUS_URL"))
        self.model = create_holt_winters_model(seasonal_periods=int(os.getenv("SEASONAL_PERIODS")))
        self.scaler = UncertaintyAwareScaler(
            pod_capacity=int(os.getenv("POD_CAPACITY")),
            risk_tolerance=float(os.getenv("RISK_TOLERANCE")),
            uncertainty_threshold=float(os.getenv("UNCERTAINTY_THRESHOLD")),
            min_replicas=int(os.getenv("MIN_REPLICAS")),
            max_replicas=int(os.getenv("MAX_REPLICAS"))
        )
    
    def IsActive(self, request, context):
        return externalscaler_pb2.IsActiveResponse(result=True)
    
    def StreamIsActive(self, request, context):
        while True:
            yield externalscaler_pb2.IsActiveResponse(result=True)
            time.sleep(5)
    
    def GetMetricSpec(self, request, context):
        metric_spec = externalscaler_pb2.MetricSpec(
            metricName="custom_metric",
            targetSize=1,
        )
        return externalscaler_pb2.GetMetricSpecResponse(metricSpecs=[metric_spec])
    
    def GetMetrics(self, request, context):
        try:
            metadata = request.scaledObjectRef.scalerMetadata
            server_url = os.getenv("PROMETHEUS_URL")
            query = metadata.get("query", "")
            current_replicas = int(metadata.get("currentReplicas", "1"))

            pod_capacity = float(metadata.get("podCapacity", os.getenv("POD_CAPACITY")))
            scale_factor = float(metadata.get("scaleFactor", os.getenv("SCALE_FACTOR")))
        except Exception as e:
            pass   