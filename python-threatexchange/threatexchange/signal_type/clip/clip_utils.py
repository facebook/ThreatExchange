from typing import List

import numpy as np
from scipy import spatial

def cosine_distance(vector_a: np.ndarray, vector_b: np.ndarray) -> float:
    """
    Returns the cosine distance of two vectors.

    Args:
        vector_a (np.ndarray): A vector of floats
        vector_b (np.ndarray): A vector of floats

    Returns:
        (float) The cosine distance of the two vectors.
    """
    return spatial.distance.cosine(vector_a, vector_b)
