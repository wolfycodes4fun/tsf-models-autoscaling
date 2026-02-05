import logging
from typing import Dict, Any
import numpy as np

logger = logging.getLogger(__name__)

class UncertaintyAwareScaler:
    
    def __init__(
        self, 
        pod_capacity: float,
        min_replicas: int,
        max_replicas: int,
        uncertainty_threshold: float,
        risk_tolerance: float
    ):

        self.pod_capacity = pod_capacity
        self.min_replicas = min_replicas
        self.max_replicas = max_replicas
        self.uncertainty_threshold = uncertainty_threshold
        self.risk_tolerance = risk_tolerance

        logger.info(f"Scaler initialized: capacity: {pod_capacity}, risk: {risk_tolerance}, \n min_replicas: {min_replicas}, max_replicas: {max_replicas}")

    def calculate_replicas(self, prediction: Dict[str, Any]) -> Dict[str, Any]:
        predicted_requests = prediction['mean']
        uncertainty = prediction['std']
        req_upper_bound = prediction['upper_bound']

        # Conservative adjustment when uncertainty is high
        if uncertainty >= self.uncertainty_threshold:
            # Safety bufferr added based on risk tolerance
            # risk_tolerance = 0.0 = using upper bound to scale
            # risk_tolerance = 1.0 = using prediction and a small buffer of a single standard deviation
            safety_multiplier = 2.0 - self.risk_tolerance
            adjusted_prediction = min(req_upper_bound,predicted_requests + safety_multiplier * uncertainty)
            logger.info(f"High prediction uncertainty: {uncertainty:.1f}, adding safety buffer to avoid underprovisioning")
        else:
            if self.risk_tolerance <= 0.3:
                # Scale based on prediction and a small buffer of half a standard deviation
                adjusted_prediction = predicted_requests + 0.5 * uncertainty
                logger.info(f"Low prediction uncertainty: {uncertainty:.1f}, scaling with small buffer")
            else:
                # Trust the prediction
                adjusted_prediction = predicted_requests
                logger.info(f"Low uncertainty: {uncertainty:.1f}, scaling based on prediction")

        adjusted_prediction = max(0, adjusted_prediction)
        target_replicas = int(np.ceil(adjusted_prediction / self.pod_capacity))
        target_replicas = max(self.min_replicas, min(self.max_replicas, target_replicas))

        logger.info(f"Calculated target replicas: {target_replicas}")

        return target_replicas
