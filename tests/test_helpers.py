import pandas as pd

from pommesdispatch.model_funcs import helpers


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
        annual_limit = 365.0
        start_time = "2017-01-01 00:00:00"
        end_time = "2017-01-03 23:00:00"
        limit = helpers.convert_annual_limit(annual_limit, start_time,
                                             end_time)
        assert limit == 2.0
