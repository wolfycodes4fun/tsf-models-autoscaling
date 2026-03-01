from typing import Dict, Any
import numpy as np
import logging

logger = logging.getLogger(__name__)

class UncertaintyAwareScaler:
    """
    Converts predictions from Holt-Winters model into the target replica count.
    Uses variables uncertainty_threshold and risk_tolerance to determine how much of a safety buffer needs
    to be added.
    """
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

        logger.info(f"Scaler initialized: capacity: {pod_capacity}, min_replicas: {min_replicas}, max_replicas: {max_replicas}, uncertainty threshold: {uncertainty_threshold}, risk tolerance: {risk_tolerance}")

    def calculate_replicas(self, prediction: Dict[str, Any]) -> int:
        """
        High prediction uncertainty (std >= uncertainty_threshold): add safety buffer closer to upper bound (conservative)
        Low prediction uncertainty: add 0.5 * uncertainty if risk_tolerance <= 0.3, else use mean
        Scaling based on risk_tolerance, if 0 scale to prevent SLA violations at all costs else closer to 1
        scale by taking cloud costs to consideration
        """
        predicted_requests = prediction['mean']
        uncertainty = prediction['std']
        req_upper_bound = prediction['upper_bound']

        if uncertainty >= self.uncertainty_threshold:
            safety_multiplier = 2.0 - self.risk_tolerance
            adjusted_prediction = min(req_upper_bound,predicted_requests + safety_multiplier * uncertainty)
        else:
            if self.risk_tolerance <= 0.3:
                adjusted_prediction = predicted_requests + 0.5 * uncertainty
            else:
                adjusted_prediction = predicted_requests

        adjusted_prediction = max(0, adjusted_prediction)
        target_replicas = int(np.ceil(adjusted_prediction / self.pod_capacity))
        target_replicas = max(self.min_replicas, min(self.max_replicas, target_replicas))

        logger.info(
            f"Scaling decision: Target replicas: {target_replicas}, adjusted load prediction: {adjusted_prediction}, "
            f"original load prediction: {predicted_requests}, uncertainty: {uncertainty}"
        )

        return target_replicas
