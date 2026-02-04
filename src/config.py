import os

class Config:
    """Configuration (including defaults) for the autoscaler"""

    SEASONAL_PERIODS: int = int(os.getenv('SEASONAL_PERIODS', '1440'))
    MAX_HISTORY_SIZE: int = int(os.getenv('MAX_HISTORY_SIZE', '2880'))
    POD_CAPACITY: float = float(os.getenv('POD_CAPACITY', '500'))
    RISK_TOLERANCE: float = float(os.getenv('RISK_TOLERANCE', '0.5'))
    UNCERTAINTY_THRESHOLD: float = float(os.getenv('UNCERTAINTY_THRESHOLD', '100'))
    MIN_REPLICAS: int = int(os.getenv('MIN_REPLICAS', '1'))
    MAX_REPLICAS: int = int(os.getenv('MAX_REPLICAS', '20'))