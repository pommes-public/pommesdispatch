import oemof.solph
import pandas as pd

from pommesdispatch.model_funcs import model_control


def return_model_and_parameters():
    """Create and parameterize a dispatch model using default values"""
    dm = model_control.DispatchModel()
    control_parameters = {
        "rolling_horizon": False,
        "aggregate_input": False,
        "countries": [
            "AT",
            "BE",
            "CH",
            "CZ",
            "DE",
            "DK1",
            "DK2",
            "FR",
            "NL",
            "NO1",
            "NO2",
            "NO3",
            "NO4",
            "NO5",
            "PL",
            "SE1",
            "SE2",
            "SE3",
            "SE4",
        ],
        "solver": "cbc",
        "solver_commandline_options": False,
        "fuel_cost_pathway": "NZE",
        "fuel_price_shock": "high",
        "emissions_cost_pathway": "long-term",
        "activate_emissions_limit": False,
        "emissions_pathway": "100_percent_linear",
        "activate_demand_response": False,
        "demand_response_approach": "DLR",
        "demand_response_scenario": "50",
        "save_production_results": True,
        "save_updated_market_values": False,
        "save_price_results": True,
        "write_lp_file": False,
    }

    time_parameters = {
        "start_time": "2017-01-01 00:00:00",
        "end_time": "2017-01-01 04:00:00",
        "freq": "60min",
    }

    input_output_parameters = {
        "path_folder_input": "tests/csv_files/",
        "path_folder_output": "tests/csv_files/",
    }

    all_parameters = {
        **control_parameters,
        **time_parameters,
        **input_output_parameters,
    }

    dm.update_model_configuration(
        control_parameters,
        time_parameters,
        input_output_parameters,
        nolog=True,
    )

    return dm, all_parameters


def set_up_rolling_horizon_run():
    """Set up a model for a rolling horizon run"""
    model_meta = {
        "overall_objective": 0,
        "overall_time": 0,
        "overall_solution_time": 0,
    }
    dm, all_parameters = return_model_and_parameters()
    dm.update_model_configuration({"rolling_horizon": True}, nolog=True)
    rolling_horizon_parameters = {
        "time_slice_length_wo_overlap_in_hours": 2,
        "overlap_in_hours": 1,
    }
    dm.add_rolling_horizon_configuration(
        rolling_horizon_parameters, nolog=True
    )

    iteration_results = {
        "storages_initial": pd.DataFrame(),
        "model_results": {},
        "dispatch_results": pd.DataFrame(),
        "power_prices": pd.DataFrame(),
    }

    return dm, iteration_results, model_meta


class TestModelControl:
    """Test class for model_control.py"""

    def test_dispatch_model_constructor(self):
        """test constructor of class DispatchModel"""
        dm = model_control.DispatchModel()
        attributes = [
            "rolling_horizon",
            "aggregate_input",
            "countries",
            "solver",
            "fuel_cost_pathway",
            "fuel_price_shock",
            "activate_emissions_limit",
            "emissions_pathway",
            "activate_demand_response",
            "demand_response_approach",
            "demand_response_scenario",
            "save_production_results",
            "save_price_results",
            "write_lp_file",
            "start_time",
            "end_time",
            "freq",
            "path_folder_input",
            "path_folder_output",
            "om",
        ]

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
            "time_slice_length_wo_overlap_in_hours": 2,
            "overlap_in_hours": 1,
        }

        dm.add_rolling_horizon_configuration(
            rolling_horizon_parameters, nolog=True
        )

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
            "dispatch_LP_start-2017-01-01_0-days_simple_complete"
        )

    def test_show_configuration_log(self):
        """test method show_configuration_log of class DispatchModel"""
        dm, all_parameters = return_model_and_parameters()
        dm.initialize_logging()
        agg_string, dr_string = dm.show_configuration_log()

        assert agg_string == "Using the COMPLETE POWER PLANT DATA SET."
        assert dr_string == "Running a model WITHOUT DEMAND RESPONSE"

        dm.update_model_configuration(
            {
                "aggregate_input": True,
                "activate_demand_response": True,
                "demand_response_approach": "DLR",
                "demand_response_scenario": "50",
            },
            nolog=True,
        )

        agg_string, dr_string = dm.show_configuration_log()
        assert agg_string == "Using the AGGREGATED POWER PLANT DATA SET"
        assert dr_string == (
            "Using approach 'DLR' "
            "for DEMAND RESPONSE modeling\n"
            "Considering a 50% scenario"
        )

    def test_build_simple_model(self):
        """test method build_simple_model of class DispatchModel"""
        dm, all_parameters = return_model_and_parameters()
        assert dm.om is None
        dm.build_simple_model()

        assert type(dm.om) == oemof.solph.Model

        dm.update_model_configuration(
            {
                "activate_emissions_limit": True,
                "emissions_pathway": "100_percent_linear",
            },
            nolog=True,
        )
        dm.build_simple_model()

        assert dm.om.integral_limit_emission_factor_constraint.active is True

    def test_get_power_prices_from_duals(self):
        """test method get_power_prices_from_duals of class DispatchModel"""
        dm, all_parameters = return_model_and_parameters()
        dm.build_simple_model()
        dm.om.receive_duals()
        dm.om.solve(solver=dm.solver, solve_kwargs={"tee": False})
        power_prices = dm.get_power_prices_from_duals()

        assert type(power_prices) == pd.DataFrame
        assert power_prices.shape == (5, 1)
        assert power_prices.max().max() == 160.0

    def test_calculate_market_values_from_model(self):
        """test method calculate_market_values_from_model of DispatchModel"""
        dm, all_parameters = return_model_and_parameters()
        all_parameters["save_updated_market_values"] = True
        dm.build_simple_model()
        dm.om.receive_duals()
        dm.om.solve(solver=dm.solver, solve_kwargs={"tee": False})
        power_prices = dm.get_power_prices_from_duals()
        (
            market_values,
            market_values_hourly,
        ) = dm.calculate_market_values_from_model(power_prices)
        assert not market_values.loc[1].isna().all()
        assert (
            market_values_hourly.at[
                "2017-01-01 02:00:00", "DE_bus_windonshore"
            ]
            == 160.0
        )

    def test_build_rolling_horizon_model(self):
        """test method build_rolling_horizon_model of class DispatchModel"""
        dm, iteration_results, model_meta = set_up_rolling_horizon_run()

        assert dm.om is None

        for counter in range(getattr(dm, "amount_of_time_slices")):
            dm.build_rolling_horizon_model(counter, iteration_results)
            assert type(dm.om) == oemof.solph.Model
            assert hasattr(dm, "storage_labels")
            assert getattr(dm, "storage_labels") == ["DE_storage_el_PHS"]

    def test_solve_rolling_horizon_model(self):
        """test method solve_rolling_horizon_model of class DispatchModel"""
        dm, iteration_results, model_meta = set_up_rolling_horizon_run()

        for counter in range(getattr(dm, "amount_of_time_slices")):
            dm.build_rolling_horizon_model(counter, iteration_results)
            dm.solve_rolling_horizon_model(
                counter, iteration_results, model_meta, no_solver_log=True
            )
            assert iteration_results["power_prices"].shape == (
                2 * (counter + 1),
                1,
            )
            assert iteration_results["dispatch_results"].shape == (
                2 * (counter + 1),
                19,
            )
            assert model_meta["overall_objective"] > 0

    def test_retrieve_initial_states_rolling_horizon(self):
        """test method retrieve_initial_states_rolling_horizon"""
        dm, iteration_results, model_meta = set_up_rolling_horizon_run()
        storage_levels = [12432, 12308]

        for counter in range(getattr(dm, "amount_of_time_slices")):
            dm.build_rolling_horizon_model(counter, iteration_results)
            dm.solve_rolling_horizon_model(
                counter, iteration_results, model_meta, no_solver_log=True
            )
            dm.retrieve_initial_states_rolling_horizon(iteration_results)
            assert (
                round(
                    iteration_results["storages_initial"].at[
                        "DE_storage_el_PHS",
                        "initial_storage_level_last_iteration",
                    ]
                )
                == storage_levels[counter]
            )
