################
#########   status.py

import numpy as np

def classify(value: float, amber: float, red: float) -> str:
    if np.isnan(amber) or np.isnan(red):
        return "UNKNOWN"
    if value >= red:
        return "RED"
    if value >= amber:
        return "AMBER"
    return "GREEN"
