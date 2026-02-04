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
    
    def conservative_adjustment(self, mean: float, std: float, upper_bound: float) -> float:
        return min(upper_bound, mean + 3 * std)

    def calculate_replicas(self, prediction: Dict[str, Any]) -> Dict[str, Any]:
        predicted_requests = prediction['mean']
        uncertainty = prediction['std']
        req_upper_bound = prediction['upper_bound']

        # Conservative adjustment when uncertainty is high
        if uncertainty > self.uncertainty_threshold:
            adjusted_prediction = self.conservative_adjustment(predicted_requests, uncertainty, req_upper_bound)
            logger.info(f"High uncertainty: {uncertainty:.1f}")
        
        # Scale based on predicted requests
        elif self.risk_tolerance == 0.5:
            adjusted_prediction = predicted_requests
        
        # Avoid SLA violations by scaling aggressively
        elif self.risk_tolerance < 0.3:
            adjusted_prediction = predicted_requests + 2 * uncertainty
        
        # Scale by minimizing chance of over-provisioning
        elif self.risk_tolerance > 0.7:
            adjusted_prediction = predicted_requests
              
        adjusted_prediction = max(0, adjusted_prediction)
        target_replicas = int(np.ceil(adjusted_prediction / self.pod_capacity))
        target_replicas = max(self.min_replicas, min(self.max_replicas, target_replicas))

        logger.info(
            f"Calculated target replicas: {target_replicas}"
            f"(predicted: {predicted_requests}, prediction_uncertaity:{uncertainty})"
        )

        return target_replicas