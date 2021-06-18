# -*- coding: utf-8 -*-
"""
General description
-------------------
These are supplementary routines used in the power market model POMMES.
The rather generic routines are centrally collected and imported
by the different model variants.

Licensing information and Disclaimer
------------------------------------
This software is provided under MIT License (see licensing file).

A special thank you goes out to all the developers creating,
maintaining, and expanding packages used in this model,
especially to the oemof and pyomo developer groups!

In addition to that, a special thank you goes to all students
and student assistants which have contributed to the model itself
or its data inputs.

Installation requirements
-------------------------
Python version >= 3.8

@author: Johannes Kochems
"""

import math
from datetime import datetime


def days_between(d1, d2):
    """Calculate the difference in days between two days
    
    Parameters:
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


def timesteps_between_timestamps(ts1, ts2, freq):
    """Calculate the difference in hours between two timesteps
    
    Parameters:
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
    timesteps_seconds = {
        "60min": (24, 3600),
        "15min": (96, 900)
    }

    diff = ts2 - ts1

    timestep_diff = (
            diff.days * timesteps_seconds[freq][0]
            + math.floor(diff.seconds / timesteps_seconds[freq][1])
    )

    return timestep_diff
