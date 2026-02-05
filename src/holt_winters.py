from statsmodels.tsa.holtwinters import ExponentialSmoothing
from typing import Dict, Any, List, Optional
import numpy as np
import logging

logger = logging.getLogger(__name__)

class HoltWintersUncertainty():

    def __init__(
        self,
        seasonal_periods: int,
        trend: str = 'add',
        seasonal: str = 'add',
        alpha: Optional[float] = None,
        beta: Optional[float] = None,
        gamma: Optional[float] = None,
        max_history: int = 43200
    ):
        # Define instance variables
        self.seasonal_periods = seasonal_periods
        self.trend = trend
        self.seasonal = seasonal
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.max_history = max_history

        self.model = None
        self.fitted_model = None
        self.data = None
    
    def fit(self, data: List[float]): 
        """Trains model on training dataset and stores it in fitted_model attribute"""
        self.data = np.array(data)

        # Validate if enough data is present for two seasonal periods
        required_data_points = 2 * self.seasonal_periods
        if len(self.data) < required_data_points:
            logger.error(f"Holt-Winters model requires at least {required_data_points} for two seasonal periods but only got {len(self.data)}")
            raise
        
        try:
            # Create model
            self.model = ExponentialSmoothing(
                self.data,
                seasonal_periods=self.seasonal_periods,
                trend=self.trend,
                seasonal=self.seasonal,
                initialization_method='estimated'
            )
    
            # Fit with train data
            self.fitted_model = self.model.fit(
                smoothing_level=self.alpha,
                smoothing_trend=self.beta,
                smoothing_seasonal=self.gamma,
                optimized=True
            )

            parameters = self.fitted_model.params
            logger.info(f"Holt-Winters fitted: α={parameters['smoothing_level']:.3f}, β={parameters['smoothing_trend']:.3f}, γ={parameters['smoothing_seasonal']:.3f}")

        except Exception as e:
            logger.error(f"An exception occurred while training Holt-Winters model: {e}")
            raise
    
    def is_fitted(self) -> bool:
        """Utility function to check if model is trained and returns a boolean value"""
        return self.fitted_model is not None
    
    def update(self, new_data: List[float]):
        """
        Update model with new data by refitting with frozen parameters (alpha, beta, gamma)
        """
        if not self.is_fitted():
            logger.error("Model must be fitted before updating")
            raise
        
        params = self.fitted_model.params
        learned_alpha = params['smoothing_level']
        learned_beta = params['smoothing_trend']
        learned_gamma = params['smoothing_seasonal']
        
        # Update data with rolling window
        self.data = np.concatenate([self.data, np.array(new_data)])

        # Data will only be stored for a period of a month at maximum
        if len(self.data) > self.max_history:
            self.data = self.data[-self.max_history:]
        
        # Refit with frozen parameters
        self.model = ExponentialSmoothing(
            self.data,
            seasonal_periods=self.seasonal_periods,
            trend=self.trend,
            seasonal=self.seasonal,
            initialization_method='estimated'
        )
        
        self.fitted_model = self.model.fit(
            smoothing_level=learned_alpha,
            smoothing_trend=learned_beta,
            smoothing_seasonal=learned_gamma,
            optimized=False
        )
    
    def predict(self, steps: int = 1) -> Dict[str, Any]:

        # Validate model is trained before predictions
        if not self.is_fitted():
            logger.error("Please fit model using the fit() method first")
            raise
        
        # Get forecast
        prediction = self.fitted_model.forecast(steps=steps)
        mean_pred = float(prediction[0] if steps == 1 else prediction[-1])
        
        # Get residuals (actual_requests - predicted_requests)
        residuals = self.fitted_model.resid

        # Get standard deviation of residuals for prediction intervals
        z_score = 1.96
        std = np.std(residuals)
        lower_bound = mean_pred - z_score * std
        upper_bound = mean_pred + z_score * std
        
        return {
            'mean': mean_pred,
            'std': float(std),
            'lower_bound': float(lower_bound),
            'upper_bound': float(upper_bound),
            'confidence_level': 0.95
        }

def create_holt_winters_model(
    seasonal_periods: int = 1440,
) -> HoltWintersUncertainty:
    """
    Factory function to create Holt-Winters model
    """
    return HoltWintersUncertainty(seasonal_periods=seasonal_periods)
