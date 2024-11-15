import numpy as np
import pandas as pd
import cvxpy as cp


import warnings

__all__ = [
    'gross_return',
    'drawdown',
    'volatility',
    'VaR_Hist',
    'CVaR_Hist',
    'ADTV',
    'correlation',
    'risk_contribution',
]
def gross_return(X):
    r'''
    calculate the contribution of single returns series. 

    .. math::
        \text{}(X) = (price[-1] - price[0]) / price[0]

    parameters
    ----------
    X: 1d-array
        Returns series, must have (T, 1) size.

    Returns
    -------
    value : float
        max drawdown of a returns series.

    '''
    a = np.array(X, ndmin=2)
    if a.shape[0] == 1 and a.shape[1] > 1:
        a = a.T
    if a.shape[0] > 1 and a.shape[1] > 1:
        raise ValueError("returns must have Tx1 size")
    cumulative_returns = np.cumprod(1 + a.flatten())  # Convert to 1D and calculate cumulative product

    return (cumulative_returns[-1] - cumulative_returns[0]) / cumulative_returns[0]

def drawdown(X):
    r'''
    calculate the max drawdown of single returns series. 

    .. math::
        \text{}(X) = \min \frac{returns_i-returns_{i-1}}{returns_i}

    parameters
    ----------
    X: 1d-array
        Returns series, must have (T, 1) size.

    Returns
    -------
    value : float
        max drawdown of a returns series.

    '''
    a = np.array(X, ndmin=2)
    if a.shape[0] == 1 and a.shape[1] > 1:
        a = a.T
    if a.shape[0] > 1 and a.shape[1] > 1:
        raise ValueError("returns must have Tx1 size")
    
    # Calculate cumulative returns
    cumulative_returns = np.cumprod(1 + a.flatten())  # Convert to 1D and calculate cumulative product
    
    # Calculate peak values
    peaks = np.maximum.accumulate(cumulative_returns)
    
    # Calculate drawdowns
    drawdowns = (peaks - cumulative_returns) / peaks
    
    # Maximum drawdown
    max_drawdown = np.max(drawdowns)
    
    return max_drawdown


def volatility(X):
    r'''
    calculate the volatility of single returns series. 

    .. math::
        \text{}(X) = \sum (returns_i - \sum returns_i/n)^2

    parameters
    ----------
    X: 1d-array
        Returns series, must have (T, 1) size.

    Returns
    -------
    value : float
        volatility of a returns series.

    '''
    a = np.array(X, ndmin=2)
    if a.shape[0] == 1 and a.shape[1] > 1:
        a = a.T
    if a.shape[0] > 1 and a.shape[1] > 1:
        raise ValueError("returns must have Tx1 size")
    
    vol = np.std(a, ddof=0)
    return vol

def VaR_Hist(X, alpha=0.05):
    r"""
    Calculate the Value at Risk (VaR) of a returns series.

    .. math::
        \text{VaR}_{\alpha}(X) = -\inf_{t \in (0,T)} \left \{ X_{t} \in
        \mathbb{R}: F_{X}(X_{t})>\alpha \right \}

    Parameters
    ----------
    X : 1d-array
        Returns series, must have Tx1 size.
    alpha : float, optional
        Significance level of VaR. The default is 0.05.
    Raises
    ------
    ValueError
        When the value cannot be calculated.

    Returns
    -------
    value : float
        VaR of a returns series.
    """

    a = np.array(X, ndmin=2)
    if a.shape[0] == 1 and a.shape[1] > 1:
        a = a.T
    if a.shape[0] > 1 and a.shape[1] > 1:
        raise ValueError("returns must have Tx1 size")

    # Flatten the array to 1D for processing
    returns = a.flatten()

    # Check if there are enough data points to calculate VaR
    if len(returns) < 2:
        raise ValueError("Not enough data points to calculate VaR.")

    # Sort returns to find the appropriate quantile
    sorted_returns = np.sort(returns)

    # Calculate the index for the desired quantile
    index = int(alpha * len(sorted_returns))

    # Ensure index is within bounds
    if index >= len(sorted_returns):
        raise ValueError("Alpha is too high; no data points available for this level.")

    # Calculate VaR as the negative of the sorted return at the calculated index
    var_value = -sorted_returns[index]

    return var_value

def CVaR_Hist(X, alpha=0.05):
    r"""
    Calculate the Conditional Value at Risk (CVaR) of a returns series.

    .. math::
        \text{CVaR}_{\alpha}(X) = \text{VaR}_{\alpha}(X) +
        \frac{1}{\alpha T} \sum_{t=1}^{T} \max(-X_{t} -
        \text{VaR}_{\alpha}(X), 0)

    Parameters
    ----------
    X : 1d-array
        Returns series, must have Tx1 size.
    alpha : float, optional
        Significance level of CVaR. The default is 0.05.

    Raises
    ------
    ValueError
        When the value cannot be calculated.

    Returns
    -------
    value : float
        CVaR of a returns series.
    """

    # Ensure X is a 2D array with shape (T, 1)
    a = np.array(X, ndmin=2)
    if a.shape[0] == 1 and a.shape[1] > 1:
        a = a.T
    if a.shape[0] > 1 and a.shape[1] > 1:
        raise ValueError("Returns must have Tx1 size")
    
    # Flatten the array to 1D for processing
    returns = a.flatten()

    # Check if there are enough data points to calculate VaR
    if len(returns) < 2:
        raise ValueError("Not enough data points to calculate CVaR.")

    # Calculate VaR using the previously defined function
    var_value = VaR_Hist(returns, alpha)

    # Calculate losses that exceed VaR
    losses_exceeding_var = np.maximum(-returns - var_value, 0)

    # Calculate the number of observations that exceed VaR
    num_exceeding_var = np.sum(losses_exceeding_var > 0)

    # Calculate CVaR
    if num_exceeding_var == 0:
        return var_value  # If no losses exceed VaR, CVaR equals VaR

    cvar_value = var_value + (np.sum(losses_exceeding_var) / (alpha * len(returns)))

    return cvar_value

def calculate_correlation(returns):
    r"""
    Calculate the correlation matrix of asset returns.

    The correlation matrix is used in portfolio risk management to understand 
    the relationships between different asset returns.

    Parameters
    ----------
    returns : 2d-array
        A 2D array where each column represents the returns of an asset, 
        and each row represents a time period.

    Raises
    ------
    ValueError
        When the input does not have at least two assets.

    Returns
    -------
    correlation_matrix : 2d-array
        Correlation matrix of the asset returns.
    """

    # Ensure returns is a 2D array
    returns_array = np.array(returns)
    
    # Check if there are at least two assets (columns)
    if returns_array.ndim != 2 or returns_array.shape[1] < 2:
        raise ValueError("Input must be a 2D array with at least two assets.")

    # Calculate the correlation matrix using NumPy
    correlation_matrix = np.corrcoef(returns_array, rowvar=False)

    return correlation_matrix

def risk_contribution(weights, prices):
    # Calculate daily returns, ignoring NaNs
    returns = prices.pct_change().dropna(how='all')
    
    # Fill NaNs with the mean of the column (forward fill and backward fill can also be used)
    returns = returns.fillna(returns.mean())
    
    # Calculate the covariance matrix of the returns
    cov_matrix = returns.cov().values
    
    # Calculate portfolio variance
    portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
    portfolio_std_dev = np.sqrt(portfolio_variance)
    
    # Calculate marginal risk contributions
    marginal_contributions = np.dot(cov_matrix, weights) / portfolio_std_dev
    
    # Calculate individual risk contributions
    risk_contributions = weights * marginal_contributions
    
    return risk_contributions, portfolio_std_dev