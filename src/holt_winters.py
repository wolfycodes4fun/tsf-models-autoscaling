from statsmodels.tsa.holtwinters import ExponentialSmoothing
from .basemodel import BasePredictorModel
from typing import Dict, Any, List, Optional
import numpy as np
import logging

logger = logging.getLogger(__name__)

class HoltWintersUncertainty(BasePredictorModel):

    def __init__(
        self,
        seasonal_periods: int = 60,
        trend: str = 'add',
        seasonal: str = 'add',
        alpha: Optional[float] = None,
        beta: Optional[float] = None,
        gamma: Optional[float] = None,
    ):
        self.seasonal_periods = seasonal_periods
        self.trend = trend
        self.seasonal = seasonal
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma

        self.model = None
        self.fitted_model = None
        self.data = None
    
    def fit(self, data: List[float], timestamps: Optional[List[Any]] = None):
        self.data = np.array(data)

        # Validate if enough data is present for two seasonal periods
        required_data_points = 2 * self.seasonal_periods
        if len(self.data) < required_data_points:
            raise ValueError(f"Holt-Winters model requires at least {required_data_points} for two seasonal periods but only got {len(self.data)}")
        
        try:
            self.model = ExponentialSmoothing(
                self.data,
                seasonal_periods=self.seasonal_periods,
                trend=self.trend,
                seasonal=self.seasonal,
                initialization_method='estimated'
            )

            self.fitted_model = self.model.fit(
                smoothing_level=self.alpha,
                smoothing_trend=self.beta,
                smoothing_seasonal=self.gamma,
                optimized=True
            )

            parameters = self.fitted_model.params
            logger.info(
                f"Holt-Winters fitted: α={parameters['smoothing_level']:.3f}, β={parameters['smoothing_trend']:.3f}, γ={parameters['smoothing_seasonal']:.3f}"
            )
        except Exception as e:
            logger.error(f"An exception occurred while training Holt-Winters model: {e}")
            raise
    
    def predict(self, steps: int = 1) -> Dict[str, Any]:

        if not self.is_fitted():
            raise ValueError("Please fit model using the fit() method first")
        
        # Get forecast
        forecast = self.fitted_model.forecast(steps=steps)
        mean_pred = float(forecast[0] if steps == 1 else forecast[-1])
        
        # Get prediction intervals (95% confidence)
        pred_obj = self.fitted_model.get_prediction(
            start=len(self.data),
            end=len(self.data) + steps - 1
        )
        pred_summary = pred_obj.summary_frame(alpha=0.05)
        
        lower = float(pred_summary['mean_ci_lower'].values[-1])
        upper = float(pred_summary['mean_ci_upper'].values[-1])
        
        # Calculate std from confidence interval
        # For 95% CI: upper = mean + 1.96*std, lower = mean - 1.96*std
        std = (upper - lower) / (2 * 1.96)
        
        return {
            'mean': mean_pred,
            'std': std,
            'lower_bound': lower,
            'upper_bound': upper,
            'method': 'prediction_interval',
            'confidence_level': 0.95
        }

def create_holt_winters_model(
    seasonal_periods: int = 60,
) -> HoltWintersUncertainty:

    return HoltWintersUncertainty(
        seasonal_periods=seasonal_periods,
        trend='add',
        seasonal='add',
        uncertainty_method=uncertainty_method
    )
