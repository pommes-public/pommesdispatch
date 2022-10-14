import pandas as pd
import yaml
from yaml.loader import SafeLoader

from pommesdispatch.model import dispatch_model


def create_test_config():
    """Create a test configuration to test the full model run"""
    content = """# Determine the model configuration

    # 1) Set overall workflow control parameters
    control_parameters:
        rolling_horizon: False
        aggregate_input: False
        countries: ['AT', 'DE']
        solver: "cbc"
        fuel_cost_pathway: "NZE"
        fuel_price_shock: "high"
        emissions_cost_pathway: "long-term"
        activate_emissions_limit: False
        emissions_pathway: "100_percent_linear"
        activate_demand_response: False
        demand_response_approach: "DLR"
        demand_response_scenario: "50"
        save_production_results: True
        save_update_market_values: False
        save_price_results: True
        write_lp_file: False

    # 2) Set model optimization time and frequency
    time_parameters:
        start_time: "2017-01-01 00:00:00"
        end_time: "2017-01-01 04:00:00"
        freq: "60min"

    # 3) Set input and output data paths
    input_output_parameters:
        path_folder_input: "tests/csv_files/"
        path_folder_output: "tests/csv_files/"

    # 4) Set rolling horizon parameters (optional)
    rolling_horizon_parameters:
        time_slice_length_wo_overlap_in_hours: 2
        overlap_in_hours: 1"""
    with open("tests/config.yml", "w") as opf:
        opf.write(content)


def change_to_rolling_horizon_config():
    """Change to a rolling horizon configuration to test the full model run"""
    with open("tests/config.yml") as file:
        test_config = yaml.load(file, Loader=SafeLoader)

    test_config["control_parameters"]["rolling_horizon"] = True

    with open("tests/config_rolling_horizon.yml", "w") as opf:
        yaml.dump(test_config, opf, default_flow_style=False)


class TestDispatchModel:
    """Test class for dispatch_model.py"""

    def test_run_dispatch_model(self):
        """test function run_dispatch_model for a simple model run"""
        create_test_config()
        dispatch_model.run_dispatch_model(config_file="tests/config.yml")

        power_prices = pd.read_csv(
            (
                "tests/csv_files/dispatch_LP_start"
                + "-2017-01-01_0-days_simple_complete_power-prices.csv"
            ),
            index_col=0,
        )
        dispatch_results = pd.read_csv(
            (
                "tests/csv_files/dispatch_LP_start"
                + "-2017-01-01_0-days_simple_complete_production.csv"
            ),
            index_col=0,
        )

        cols = [
            "(('AT_bus_el', 'None'), 'duals')",
            "(('DE_link_AT', 'AT_bus_el'), 'flow')",
            "(('DE_bus_el', 'DE_link_AT'), 'flow')",
            "(('DE_bus_el', 'DE_sink_el_excess'), 'flow')",
            "(('DE_bus_el', 'DE_sink_el_load'), 'flow')",
            "(('DE_bus_el', 'DE_storage_el_PHS'), 'flow')",
            "(('DE_bus_el', 'None'), 'duals')",
            "(('DE_solarPV_cluster_1', 'DE_bus_el'), 'flow')",
            "(('DE_solarPV_cluster_2', 'DE_bus_el'), 'flow')",
            "(('DE_source_biomassEEG', 'DE_bus_el'), 'flow')",
            "(('DE_source_el_shortage', 'DE_bus_el'), 'flow')",
            "(('DE_source_el_shortage_add_0', 'DE_bus_el'), 'flow')",
            "(('DE_source_el_shortage_add_1', 'DE_bus_el'), 'flow')",
            "(('DE_storage_el_PHS', 'DE_bus_el'), 'flow')",
            "(('DE_transformer_hardcoal_BNA0019', 'DE_bus_el'), 'flow')",
            "(('DE_transformer_hardcoal_BNA0147', 'DE_bus_el'), 'flow')",
            "(('DE_transformer_hardcoal_BNA0216a', 'DE_bus_el'), 'flow')",
            "(('DE_windoffshore_cluster_1', 'DE_bus_el'), 'flow')",
            "(('DE_windoffshore_cluster_2', 'DE_bus_el'), 'flow')",
            "(('DE_windonshore_cluster_1', 'DE_bus_el'), 'flow')",
            "(('DE_windonshore_cluster_2', 'DE_bus_el'), 'flow')",
        ]

        assert power_prices.shape == (5, 1)
        assert dispatch_results.shape == (5, 21)
        for col in cols:
            assert col in list(dispatch_results.columns)

    def test_run_dispatch_model_rolling_horizon(self):
        """test function run_dispatch_model for a rolling horizon model run"""
        create_test_config()
        change_to_rolling_horizon_config()
        dispatch_model.run_dispatch_model(
            config_file="tests/config_rolling_horizon.yml"
        )

        power_prices = pd.read_csv(
            (
                "tests/csv_files/dispatch_LP_start"
                + "-2017-01-01_0-days_RH_complete_power-prices.csv"
            ),
            index_col=0,
        )
        dispatch_results_de = pd.read_csv(
            (
                "tests/csv_files/dispatch_LP_start"
                + "-2017-01-01_0-days_RH_complete_production.csv"
            ),
            index_col=0,
        )

        cols = [
            "(('DE_bus_el', 'DE_link_AT'), 'flow')",
            "(('DE_bus_el', 'DE_sink_el_excess'), 'flow')",
            "(('DE_bus_el', 'DE_sink_el_load'), 'flow')",
            "(('DE_bus_el', 'DE_storage_el_PHS'), 'flow')",
            "(('DE_bus_el', 'None'), 'duals')",
            "(('DE_solarPV_cluster_1', 'DE_bus_el'), 'flow')",
            "(('DE_solarPV_cluster_2', 'DE_bus_el'), 'flow')",
            "(('DE_source_biomassEEG', 'DE_bus_el'), 'flow')",
            "(('DE_source_el_shortage', 'DE_bus_el'), 'flow')",
            "(('DE_source_el_shortage_add_0', 'DE_bus_el'), 'flow')",
            "(('DE_source_el_shortage_add_1', 'DE_bus_el'), 'flow')",
            "(('DE_storage_el_PHS', 'DE_bus_el'), 'flow')",
            "(('DE_transformer_hardcoal_BNA0019', 'DE_bus_el'), 'flow')",
            "(('DE_transformer_hardcoal_BNA0147', 'DE_bus_el'), 'flow')",
            "(('DE_transformer_hardcoal_BNA0216a', 'DE_bus_el'), 'flow')",
            "(('DE_windoffshore_cluster_1', 'DE_bus_el'), 'flow')",
            "(('DE_windoffshore_cluster_2', 'DE_bus_el'), 'flow')",
            "(('DE_windonshore_cluster_1', 'DE_bus_el'), 'flow')",
            "(('DE_windonshore_cluster_2', 'DE_bus_el'), 'flow')",
        ]

        assert power_prices.shape == (4, 1)
        assert dispatch_results_de.shape == (4, 19)
        for col in cols:
            assert col in list(dispatch_results_de.columns)
