from pommesdispatch.model_funcs import model_control
import logging


def return_model_and_parameters():
    """Create and parameterize a dispatch model using default values"""
    dm = model_control.DispatchModel()
    control_parameters = {
        "rolling_horizon": False,
        "aggregate_input": False,
        "countries": ['AT', 'BE', 'CH', 'CZ', 'DE', 'DK1', 'DK2', 'FR',
                      'NL',
                      'NO1', 'NO2', 'NO3', 'NO4', 'NO5', 'PL',
                      'SE1', 'SE2', 'SE3', 'SE4'],
        "solver": "gurobi",
        "fuel_cost_pathway": "middle",
        "activate_emissions_limit": False,
        "emissions_pathway": "100_percent_linear",
        "activate_demand_response": False,
        "demand_response_approach": "DLR",
        "demand_response_scenario": "50",
        "save_production_results": True,
        "save_price_results": True,
        "write_lp_file": False}

    time_parameters = {
        "start_time": "2017-01-01 00:00:00",
        "end_time": "2017-01-02 23:00:00",
        "freq": "60min"}

    input_output_parameters = {
        "path_folder_input": "./inputs/",
        "path_folder_output": "./results/"}

    all_parameters = {**control_parameters, **time_parameters,
                      **input_output_parameters}

    dm.update_model_configuration(control_parameters, time_parameters,
                                  input_output_parameters, nolog=True)

    return dm, all_parameters


class TestModelControl:
    """Test class for model_control.py"""

    def test_dispatch_model_constructor(self):
        """test constructor of class DispatchModel"""
        dm = model_control.DispatchModel()
        attributes = [
            "rolling_horizon", "aggregate_input", "countries",
            "solver", "fuel_cost_pathway",
            "activate_emissions_limit", "emissions_pathway",
            "activate_demand_response", "demand_response_approach",
            "demand_response_scenario", "save_production_results",
            "save_price_results", "write_lp_file",
            "start_time", "end_time", "freq",
            "path_folder_input", "path_folder_output", "om"]

        for attr in attributes:
            assert hasattr(dm, attr)
            assert getattr(dm, attr) is None

    def test_update_model_configuration(self):
        """test method update_model_configuration of class DispatchModel"""
        dm, all_parameters = return_model_and_parameters()

        for key, val in all_parameters.items():
            assert getattr(dm, key) == val

    def test_check_model_configuration(self):
        """test method check_model_configuration of class DispatchModel"""
        dm, all_parameters = return_model_and_parameters()
        dm.freq = None

        dm.initialize_logging()
        missing_parameters = dm.check_model_configuration()
        assert missing_parameters == ["freq"]

    def test_add_rolling_horizon_configuration(self):
        """test method add_rolling_horizon_configuration of DispatchModel"""
        dm, all_parameters = return_model_and_parameters()
        rolling_horizon_parameters = {
            "time_slice_length_wo_overlap_in_hours": 24,
            "overlap_in_hours": 12}

        dm.add_rolling_horizon_configuration(
            rolling_horizon_parameters, nolog=True)

        assert hasattr(dm, "time_series_start")
        assert hasattr(dm, "time_series_end")
        assert hasattr(dm, "time_slice_length_wo_overlap_in_time_steps")
        assert hasattr(dm, "overlap_in_time_steps")
        assert hasattr(dm, "time_slice_length_with_overlap")
        assert hasattr(dm, "overall_time_steps")
        assert hasattr(dm, "amount_of_time_slices")
        assert getattr(dm, "amount_of_time_slices") == 2

    def test_initialize_logging(self):
        """test method initialize_logging of class DispatchModel"""
        dm, all_parameters = return_model_and_parameters()
        filename = dm.initialize_logging()

        assert filename == (
            "dispatch_LP_start-2017-01-01_1-days_simple_complete")
