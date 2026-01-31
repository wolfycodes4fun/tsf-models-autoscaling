import logging
from typing import Dict, Any
import numpy as np

logger = logging.getLogger(__name__)

class UncertaintyAwareScaler:
    
    def __init__(
        self, 
        pod_capacity: float = 100.0,
        min_replicas: int = 1,
        max_replicas: int = 10,
        uncertainty_threshold: float = 100.0,
        risk_tolerance: float = 0.5
    ):

        self.pod_capacity = pod_capacity
        self.min_replicas = min_replicas
        self.max_replicas = max_replicas
        self.uncertainty_threshold = uncertainty_threshold
        self.risk_tolerance = risk_tolerance

        logger.info(f"Scaler initialized: capacity: {pod_capacity}, risk: {risk_tolerance}, \n min_replicas: {min_replicas}, max_replicas: {max_replicas}")
    
    def calculate_replicas(self, prediction: Dict[str, Any],) -> Dict[str, Any]:
        predicted_requests = prediction['mean']
        uncertainty = prediction['std']