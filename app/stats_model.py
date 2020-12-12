import pandas as pd


def describe_series_stats(timeseries: pd.Series) -> dict:
    """
    Basic statistics for a timeseries, namely high, low, and mean.

    :param timeseries:  pd.Series   timeseries in consideration

    :return: dictionary containing high, low, and mean of the timeseries
    """
    return {'High': max(timeseries), 'Low': min(timeseries), 'Mean': sum(timeseries) / len(timeseries)}


def pearson_correlation(ts1: pd.Series, ts2: pd.Series):
    """
    Computes the Pearson Correlation Coefficient of two timeseries

    :param ts1: first timeseries
    :param ts2: second timeseries
    :return: float  Person correlation coefficient
    """
    if len(ts1) != len(ts2):
        raise Exception('Please ensure the lengths of both time series are equal!')
    mean_x = sum(ts1) / len(ts1)
    mean_y = sum(ts2) / len(ts2)
    covariance_x_y = sum(map(lambda x_i, y_i: (x_i - mean_x) * (y_i - mean_y), ts1, ts2))
    variance_x = sum(map(lambda x_i: (x_i - mean_x) ** 2, ts1))
    variance_y = sum(map(lambda y_i: (y_i - mean_y) ** 2, ts2))
    return covariance_x_y / ((variance_x * variance_y) ** (1 / 2))
