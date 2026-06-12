"""Transfer Entropy Integration Index (TEII) — consciousness integration metric."""

from __future__ import annotations

import numpy as np
from scipy.spatial.distance import cdist
from typing import List


class TransferEntropyCalculator:
    """
    Calculate Transfer Entropy Integration Index (TEII).
    
    Steps:
      1. Extract activation time series for all nodes
      2. Compute pairwise transfer entropy TE(i→j)
      3. Build effective connectivity matrix M
      4. Compute eigenvalues of M
      5. Integration = λ₁ / Σλ
    """

    def __init__(self, window: int = 500, k_neighbors: int = 5):
        self.window = window
        self.k_neighbors = k_neighbors

    def calculate(self, network, window: int = None) -> float:
        """
        Calculate TEII for the network.
        Returns integration index (0~1).
        """
        if window is None:
            window = self.window

        # Step 1: Extract activation time series
        activations = self._extract_activations(network, window)
        if activations is None or activations.shape[0] < 2:
            return 0.0

        N, T = activations.shape
        if T < 10:
            return 0.0

        # For large N, subsample to keep computation manageable
        max_nodes = min(N, 200)  # Cap at 200 nodes for TE computation
        if N > max_nodes:
            indices = np.random.choice(N, max_nodes, replace=False)
            activations = activations[indices]
            N = max_nodes

        # Step 2: Compute pairwise transfer entropy (approximate)
        # Use simplified mutual information as TE proxy
        M = np.zeros((N, N))
        for i in range(N):
            for j in range(i + 1, N):
                te_ij = self._estimate_te(activations[i], activations[j])
                te_ji = self._estimate_te(activations[j], activations[i])
                M[i, j] = te_ij
                M[j, i] = te_ji

        # Step 3: Make matrix non-negative and symmetric-ish
        M = np.abs(M)
        np.fill_diagonal(M, 0)

        # Step 4: Compute eigenvalues
        try:
            eigenvalues = np.linalg.eigvalsh(M)
        except np.linalg.LinAlgError:
            return 0.0

        # Step 5: Integration = largest eigenvalue / sum of all
        eigenvalues = np.abs(eigenvalues)
        total = eigenvalues.sum()
        if total < 1e-10:
            return 0.0

        integration = eigenvalues[-1] / total
        return float(min(1.0, max(0.0, integration)))

    def _extract_activations(self, network, window: int) -> np.ndarray:
        """
        Extract activation time series from all nodes.
        Returns shape=(N, window) array.
        """
        all_history = []
        for node in network.nodes.values():
            if node.activation_history:
                hist = node.activation_history[-window:]
                if len(hist) >= 10:
                    # Pad if needed
                    if len(hist) < window:
                        hist = np.pad(hist, (window - len(hist), 0), 'edge')
                    all_history.append(hist[-window:])

        if not all_history:
            return None

        return np.array(all_history)

    def _estimate_te(self, source: np.ndarray, target: np.ndarray,
                      lag: int = 1) -> float:
        """
        Estimate transfer entropy from source to target.
        Uses a simplified k-NN based mutual information estimator.
        """
        if len(source) < 10 or len(target) < 10:
            return 0.0

        # Use time-lagged mutual information as TE proxy
        # TE(X→Y) ≈ I(X_t; Y_{t+1} | Y_t)
        s_t = source[:-lag]
        t_now = target[lag:]
        t_past = target[:-lag]

        if len(s_t) < 5:
            return 0.0

        # Simple estimator: correlation-based TE proxy
        # Conditional MI approximation
        try:
            # Partial correlation: corr(s_t, t_now | t_past)
            # Residual of s_t after regressing on t_past
            if np.std(t_past) < 1e-10:
                res_s = s_t - np.mean(s_t)
            else:
                slope_s = np.cov(s_t, t_past)[0, 1] / np.var(t_past)
                res_s = s_t - slope_s * t_past

            # Residual of t_now after regressing on t_past
            if np.std(t_past) < 1e-10:
                res_t = t_now - np.mean(t_now)
            else:
                slope_t = np.cov(t_now, t_past)[0, 1] / np.var(t_past)
                res_t = t_now - slope_t * t_past

            # Mutual information between residuals
            if np.std(res_s) < 1e-10 or np.std(res_t) < 1e-10:
                return 0.0

            corr = np.corrcoef(res_s, res_t)[0, 1]
            if np.isnan(corr):
                return 0.0

            # MI ≈ -0.5 * log(1 - r²)
            mi = -0.5 * np.log(max(1e-10, 1 - corr ** 2))
            return float(max(0.0, mi))

        except Exception:
            return 0.0
