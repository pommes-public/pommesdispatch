import pandas as pd

from pommesdispatch.model_funcs import helpers
from pommesdispatch.model_funcs.helpers import (
    convert_annual_costs_nominal_to_real,
    convert_nominal_to_real_time_series,
)


class TestHelpers:
    """Test class for helpers.py"""

    def test_days_between(self):
        """test function days_between"""
        d1 = "2017-01-01 00:00:00"
        d2 = "2018-01-01 01:00:00"
        day_diff = helpers.days_between(d1, d2)
        assert day_diff == 365

    def test_time_steps_between_timestamps(self):
        """test function time_steps_between_timestamps"""
        ts1 = pd.Timestamp("2017-01-01 00:00:00")
        ts2 = pd.Timestamp("2018-01-01 01:00:00")
        freq = "60min"
        time_steps = helpers.time_steps_between_timestamps(ts1, ts2, freq)
        assert time_steps == 8761

    def test_convert_annual_limit(self):
        """test function convert_annual_limit"""
        annual_limit = 365.0
        start_time = "2017-01-01 00:00:00"
        end_time = "2017-01-03 23:00:00"
        limit = helpers.convert_annual_limit(
            annual_limit, start_time, end_time
        )
        assert limit == 2.0

    def test_convert_annual_limit_multi_years(self):
        """test function convert_annual_limit for multiple years"""
        annual_limit = 365.0
        start_time = "2017-01-01 00:00:00"
        end_time = "2018-01-03 23:00:00"
        limit = helpers.convert_annual_limit(
            annual_limit, start_time, end_time
        )
        assert limit == 368.0

    def test_convert_annual_costs_nominal_to_real(self):
        """test function convert_annual_costs_nominal_to_real"""
        inflation_rate = 1.02
        year = 2020

        nominal_costs = pd.DataFrame.from_dict(
            columns=range(2017, 2031),
            data={
                "DE_bus_biomass": [
                    4.0,
                    4.0,
                    4.0,
                    4.0,
                    4.08,
                    4.16,
                    4.24,
                    4.33,
                    4.42,
                    4.5,
                    4.59,
                    4.69,
                    4.78,
                    4.88,
                ],
                "DE_bus_hardcoal": [
                    11.0,
                    11.0,
                    11.0,
                    11.0,
                    11.22,
                    11.44,
                    11.67,
                    11.91,
                    12.14,
                    12.39,
                    12.64,
                    12.89,
                    13.15,
                    13.41,
                ],
            },
            orient="index",
        )

        real_costs = convert_annual_costs_nominal_to_real(
            nominal_costs, inflation_rate, year
        )
        for iter_year in range(2020, 2031):
            assert round(real_costs.at["DE_bus_biomass", iter_year], 0) == 4
            assert round(real_costs.at["DE_bus_hardcoal", iter_year], 0) == 11

    def test_convert_nominal_to_real_time_series(self):
        """test function convert_nominal_to_real_time_series"""
        inflation_rate = 1.02
        year = 2020

        nominal_time_series = pd.DataFrame(
            index=pd.date_range(
                start="2017-01-01 00:00", periods=14, freq="H"
            ),
            data={
                "DE_bus_biomass": [
                    4.0,
                    4.0,
                    4.0,
                    4.0,
                    4.08,
                    4.16,
                    4.24,
                    4.33,
                    4.42,
                    4.5,
                    4.59,
                    4.69,
                    4.78,
                    4.88,
                ],
                "DE_bus_hardcoal": [
                    11.0,
                    11.0,
                    11.0,
                    11.0,
                    11.22,
                    11.44,
                    11.67,
                    11.91,
                    12.14,
                    12.39,
                    12.64,
                    12.89,
                    13.15,
                    13.41,
                ],
            },
        )

        real_time_series = convert_nominal_to_real_time_series(
            nominal_time_series, inflation_rate, year
        )
        assert round(real_time_series["DE_bus_biomass"].sum(), 1) == 64.4
        assert round(real_time_series["DE_bus_hardcoal"].sum(), 1) == 177.1
