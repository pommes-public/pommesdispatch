# -*- coding: utf-8 -*-
"""
General description
-------------------
These are supplementary routines used in the power market model POMMES.

Installation requirements
-------------------------
Python version >= 3.8

@author: Johannes Kochems
"""
import math
from datetime import datetime

import pandas as pd


def days_between(d1, d2):
    """Calculate the difference in days between two days

    Parameters
    ----------
    d1 : str
        The first date string
    d2 : str
        The second date string

    Returns
    -------
    day_diff: int
        The difference between the two dates in days
    """
    d1 = datetime.strptime(d1, "%Y-%m-%d %H:%M:%S")
    d2 = datetime.strptime(d2, "%Y-%m-%d %H:%M:%S")
    day_diff = abs((d2 - d1).days)

    return day_diff


def time_steps_between_timestamps(ts1, ts2, freq):
    """Calculate the difference in hours between two timesteps

    Parameters
    ----------
    ts1 : pd.Timestamp
        The first timestamp
    ts2 : pd.Timestamp
        The second timestamp
    freq: str
        The frequency information, e.g. '60min', '15min'

    Returns
    -------
    hour_diff: int
        The difference between the two dates in hours
    """
    time_steps_seconds = {"60min": (24, 3600), "15min": (96, 900)}

    diff = ts2 - ts1

    time_step_diff = diff.days * time_steps_seconds[freq][0] + math.floor(
        diff.seconds / time_steps_seconds[freq][1]
    )

    return time_step_diff


def convert_annual_limit(annual_limit, start_time, end_time):
    """Convert an annual limit to a sub- or multi-annual one

    Parameters
    ----------
    annual_limit: :obj:`float` or :obj:`pd.Series`of :class:`float`
        An annual limit (e.g. for emissions, investment budgets)
        if start_time and end_time are within the same year,
        or a pd.Series of annual limits indexed by years if start_time and
        end_time are not within one year

    start_time: :obj:`str`
        The first date string; start_time of the optimization run

    end_time: :obj:`str`
        The second date string; end_time of the optimization run

    Returns
    -------
    new_limit: :obj:`float`
        A sub-annual / multi-annual limit for the optimization timeframe
    """
    dt_start = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    dt_end = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
    start_year = dt_start.year
    end_year = dt_end.year

    new_limit = 0

    if start_year == end_year:
        day_diff = days_between(start_time, end_time)
        year_fraction = day_diff / float(365)
        if isinstance(annual_limit, float):
            new_limit = annual_limit * year_fraction
        else:
            new_limit = annual_limit[start_year] * year_fraction

    else:
        start_year_begin = str(start_year) + "-01-01 00:00:00"
        end_year_end = str(end_year) + "-12-31 23:59:59"
        day_diff_start = days_between(start_year_begin, start_time)
        day_diff_end = days_between(end_time, end_year_end)

        start_year_fraction = (365 - day_diff_start) / float(365)
        end_year_fraction = (365 - day_diff_end) / float(365)
        full_years = end_year - start_year - 1

        # Add annual limits for full years within optimization time frame
        for i in range(full_years):
            new_limit += annual_limit

        # Add limits for fractions of the start year and end year
        new_limit += (
            annual_limit * start_year_fraction
            + annual_limit * end_year_fraction
        )

    return new_limit


def convert_annual_costs_nominal_to_real(
    nominal_costs, inflation_rate=1.02, year=2022
):
    """Convert cost values of DataFrame from nominal to real terms

    Parameters
    ----------
    nominal_costs: :obj:`pd.DataFrame`
        Nominal costs data in annual resolution (years = columns)

    inflation_rate: :obj:`float`
        Inflation rate

    year: :obj:`int`
        Year for which the nominal costs shall be expressed

    Returns
    -------
    real_costs: :obj:`pd.DataFrame`
        Real costs data in annual resolution
    """
    real_costs = nominal_costs.copy()
    for column in real_costs.columns:
        if column != "label":
            try:
                real_costs[column] = real_costs[column].div(
                    inflation_rate ** (int(column) - year)
                )
            except TypeError:
                msg = (
                    "DataFrame format not as expected\n"
                    "Except for column 'label', "
                    "all other columns must be integer"
                )
                raise TypeError(msg)

    return real_costs


def convert_nominal_to_real_time_series(
    nominal_time_series, inflation_rate=1.02, year=2022
):
    """Convert time series values of DataFrame from nominal to real terms

    Parameters
    ----------
    nominal_time_series: :obj:`pd.DataFrame`
        Nominal time series data in hourly resolution

    inflation_rate: :obj:`float`
        Inflation rate

    year: :obj:`int`
        Year for which the nominal costs shall be expressed

    Returns
    -------
    real_time_series: :obj:`pd.DataFrame`
        Real time series data in hourly resolution
    """
    if not type(nominal_time_series.index.year == pd.DatetimeIndex):
        raise TypeError("Given time series must have a pd.DatetimeIndex!")

    time_series_year = nominal_time_series.index.year[0]
    real_time_series = nominal_time_series.div(
        inflation_rate ** (time_series_year - year)
    )

    return real_time_series
