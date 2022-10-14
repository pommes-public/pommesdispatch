from pommesdispatch import cli
import yaml
from yaml.loader import SafeLoader


class TestCli:
    """Test class for cli.py"""

    def test_create_default_config(self):
        """test function create_default_config"""
        cli.create_default_config()
        with open("./config.yml") as file:
            test_config = yaml.load(file, Loader=SafeLoader)

        config_dict = {
            "control_parameters": {
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
                "solver": "gurobi",
                "solver_commandline_options": False,
                "fuel_cost_pathway": "NZE",
                "fuel_price_shock": "high",
                "emissions_cost_pathway": "long-term",
                "activate_emissions_limit": False,
                "emissions_pathway": "100_percent_linear",
                "activate_demand_response": False,
                "demand_response_approach": "DLR",
                "demand_response_scenario": "50",
                "save_updated_market_values": True,
                "save_production_results": True,
                "save_price_results": True,
                "write_lp_file": False,
            },
            "time_parameters": {
                "start_time": "2017-01-01 00:00:00",
                "end_time": "2017-01-02 23:00:00",
                "freq": "60min",
            },
            "input_output_parameters": {
                "path_folder_input": "./inputs/",
                "path_folder_output": "./results/",
            },
            "rolling_horizon_parameters": {
                "time_slice_length_wo_overlap_in_hours": 24,
                "overlap_in_hours": 12,
            },
            "solver_cmdline_options": {
                "lpmethod": 4,
                "preprocessing dual": -1,
                "solutiontype": 2,
                "threads": 12,
                "barrier convergetol": 1e-6,
            },
        }

        assert test_config == config_dict
