import logging
import pickle
import grpc
import externalscaler_pb2
import externalscaler_pb2_grpc
from concurrent import futures
from typing import List
from src.utils.prometheus_client import PrometheusClient
from src.scalers.scaling_logic import UncertaintyAwareScaler
from src.config import Config

logger = logging.getLogger(__name__)

class ExternalScalerServicer(externalscaler_pb2_grpc.ExternalScalerServicer):

    def __init__(self):
        # Initialize Prometheus client
        self.prom_client = PrometheusClient(url=Config.PROMETHEUS_URL)

        # Load trained model
        logger.info("Loading trained model...")
        try:
            with open('models/holt_winters_uncertainty.pk1', 'rb') as f:
                self.model = pickle.load(f)
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise

        # Initialize scaler object
        self.scaler = UncertaintyAwareScaler(
            pod_capacity=Config.POD_CAPACITY,
            min_replicas=Config.MIN_REPLICAS,
            max_replicas=Config.MAX_REPLICAS,
            uncertainty_threshold=Config.UNCERTAINTY_THRESHOLD,
            risk_tolerance=Config.RISK_TOLERANCE
        )

        # Maintain history of requests
        self.history: List[float] = []

    def IsActive(self, request, context):
        """KEDA uses this to check if scaling should be active"""
        return externalscaler_pb2.IsActiveResponse(result=1)
    
    def StreamIsActive(self, request, context):
        while True:
            yield externalscaler_pb2.IsActiveResponse(result=1)
    
    def GetMetricSpec(self, request, context):
        metric_spec = externalscaler_pb2.MetricSpec(
            metricName="custom_metric",
            targetSizeFloat=1.0
        )
        return externalscaler_pb2.GetMetricSpecResponse(metricSpecs=[metric_spec])
    
    def GetMetrics(self, request, context):
        try:
            query = request.scaledObjectRef.scalerMetaData["query"]
            pod_capacity = request.scaledObjectRef.scalerMetaData["podCapacity"]
            activation_value = request.scaledObjectRef.scalerMetaData["activationValue"]
            max_history_size = request.scaledObjectRef.scalerMetaData["maxHistorySize"]

            # Fetch metrics from Prometheus
            current_requests = self.prom_client.fetch_metrics(query=query)

            # Add to history
            self.history.append(current_requests)
            if len(self.history) > max_history_size:
                self.history = self.history[-max_history_size:]

            # Avoid scaling when requests numbers are below activation value
            if current_requests < activation_value:
                target_replicas = Config.MIN_REPLICAS

            else:
                self.model.update([current_requests]) 
                prediction = self.model.predict(steps=1)
                target_replicas = self.scaler.calculate_replicas(prediction)
            
            return externalscaler_pb2.GetMetricResponse(
                metricValues=[
                    externalscaler_pb2.MetricValue(
                        metricName="custom_metric",
                        metricValue=int(target_replicas)
                    )
                ]
            )
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return externalscaler_pb2.GetMetricsResponse(
                metricValues=[
                    externalscaler_pb2.MetricValue(
                        metricName="custom_metric",
                        metricValue=Config.MIN_REPLICAS
                    )
                ]
            )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    externalscaler_pb2_grpc.add_ExternalScalerServicer_to_server(ExternalScalerServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    logging.info("Server started, listening on port 50051")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
