from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BasePredictorModel(ABC):

    @abstractmethod
    def fit(self, data: List[float], timestamps: List[Any] = None):
        """Train model on past data by looking at time"""
        pass

    @abstractmethod
    def predict(self, steps: int =1) -> Dict[str, Any]:
        """
        Make and return a prediction for the next `steps` time steps with uncertainty quantification
        Returns:
            dict: {
                'mean': float,
                'std': float,
                'lower_bound': float,  # 95% CI lower
                'upper_bound': float,  # 95% CI upper
                'method': str  # Uncertainty method used
            }
        """
        pass
