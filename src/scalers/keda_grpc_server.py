from src.utils.prometheus_client import PrometheusClient
from src.scalers.scaling_logic import UncertaintyAwareScaler
from src.config import Config
from . import externalscaler_pb2
from . import externalscaler_pb2_grpc
from concurrent import futures
from typing import List
import pickle
import grpc
import logging


# Configure logging
logger = logging.getLogger(__name__)

# gRPC server implementation for KEDA
class ExternalScalerServicer(externalscaler_pb2_grpc.ExternalScalerServicer):

    def __init__(self):
        # Initialize Prometheus client
        self.prom_client = PrometheusClient(server_address=Config.PROMETHEUS_URL)

        # Load trained model
        logger.info("Loading trained model...")
        try: 
            with open('models/holt_winters_uncertainty.pkl', 'rb') as f:
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

        # Set maximum history to be stored in list
        self.max_history_size = Config.MAX_HISTORY_SIZE

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
            metadata = request.scaledObjectRef.scalerMetadata
            query = metadata.get("query")
            pod_capacity = float(metadata.get("podCapacity", "1000"))
            activation_value = float(metadata.get("activationValue", "10"))

            # Fetch metrics from Prometheus
            current_requests = self.prom_client.fetch_metrics(query=query)

            # Add to history
            self.history.append(current_requests)
            if len(self.history) > self.max_history_size:
                self.history = self.history[-self.max_history_size:]
            
            logger.info(f"History size: {len(self.history)}")

            # Avoid scaling when requests numbers are below activation value
            if current_requests < activation_value:
                prediction = {
                    'mean': current_requests,
                    'std': 0.0,
                    'lower_bound': current_requests,
                    'upper_bound': current_requests,
                    'confidence_level': 0.95
                }
                logger.info(f"Traffic ({current_requests:.1f}) below activation ({activation_value}); scaling based on current requests")
            else:
                self.model.update([current_requests]) 
                prediction = self.model.predict(steps=1)
                logger.info(f"Prediction: {prediction['mean']:.1f}, uncertainty: {prediction['std']:.1f}; scaling based on predictions by model")
            
            target_replicas = self.scaler.calculate_replicas(prediction)
            logger.info(f"Target replicas: {target_replicas}")
            
            return externalscaler_pb2.GetMetricsResponse(
                metricValues=[
                    externalscaler_pb2.MetricValue(
                        metricName="custom_metric",
                        metricValue=int(target_replicas),
                        metricValueFloat=float(target_replicas)
                    )
                ]
            )
        except Exception as e:
            logger.error(f"Error getting metrics: {e}", exc_info=True)
            return externalscaler_pb2.GetMetricsResponse(
                metricValues=[
                    externalscaler_pb2.MetricValue(
                        metricName="custom_metric",
                        metricValue=Config.MIN_REPLICAS,
                        metricValueFloat=float(Config.MIN_REPLICAS)
                    )
                ]
            )

def serve():
    
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Starting gRPC server...")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    externalscaler_pb2_grpc.add_ExternalScalerServicer_to_server(ExternalScalerServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    logger.info("Server started, listening on port 50051")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
