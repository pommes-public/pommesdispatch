import pandas as pd
import yaml
from yaml.loader import SafeLoader

from pommesdispatch.model import dispatch_model
from tests.test_dispatch_model import create_test_config


def change_to_demand_response_config():
    """Change to a demand response configuration to test the full model run"""
    with open("tests/config.yml") as file:
        test_config = yaml.load(file, Loader=SafeLoader)

    test_config["control_parameters"]["activate_demand_response"] = True

    with open("tests/config_demand_response.yml", "w") as opf:
        yaml.dump(test_config, opf, default_flow_style=False)


class TestResultsProcessing:
    """Test class for results_processing.py"""

    def test_run_dispatch_model_with_demand_response(self):
        """test function run_dispatch_model for
        a model run including demand response"""
        create_test_config()
        change_to_demand_response_config()
        dispatch_model.run_dispatch_model(
            config_file="tests/config_demand_response.yml"
        )

        dispatch_results_de = pd.read_csv(
            (
                "tests/csv_files/dispatch_LP_start"
                + "-2017-01-01_0-days_simple_complete_production.csv"
            ),
            index_col=0,
        )

        demand_response_cols = [
            "('tcs+hoho_cluster_shift_only', 'dsm_up')",
            "('tcs+hoho_cluster_shift_only', 'dsm_do_shift')",
            "('tcs+hoho_cluster_shift_only', 'dsm_do_shed')",
            "('tcs+hoho_cluster_shift_only', 'dsm_storage_level')",
            "('hoho_cluster_shift_shed', 'dsm_up')",
            "('hoho_cluster_shift_shed', 'dsm_do_shift')",
            "('hoho_cluster_shift_shed', 'dsm_do_shed')",
            "('hoho_cluster_shift_shed', 'dsm_storage_level')",
            "('hoho_cluster_shift_only', 'dsm_up')",
            "('hoho_cluster_shift_only', 'dsm_do_shift')",
            "('hoho_cluster_shift_only', 'dsm_do_shed')",
            "('hoho_cluster_shift_only', 'dsm_storage_level')",
            "('tcs_cluster_shift_only', 'dsm_up')",
            "('tcs_cluster_shift_only', 'dsm_do_shift')",
            "('tcs_cluster_shift_only', 'dsm_do_shed')",
            "('tcs_cluster_shift_only', 'dsm_storage_level')",
            "('ind_cluster_shed_only', 'dsm_up')",
            "('ind_cluster_shed_only', 'dsm_do_shift')",
            "('ind_cluster_shed_only', 'dsm_do_shed')",
            "('ind_cluster_shed_only', 'dsm_storage_level')",
            "('ind_cluster_shift_shed', 'dsm_up')",
            "('ind_cluster_shift_shed', 'dsm_do_shift')",
            "('ind_cluster_shift_shed', 'dsm_do_shed')",
            "('ind_cluster_shift_shed', 'dsm_storage_level')",
            "('ind_cluster_shift_only', 'dsm_up')",
            "('ind_cluster_shift_only', 'dsm_do_shift')",
            "('ind_cluster_shift_only', 'dsm_do_shed')",
            "('ind_cluster_shift_only', 'dsm_storage_level')",
        ]

        assert dispatch_results_de.shape == (6, 56)
        for col in demand_response_cols:
            assert col in list(dispatch_results_de.columns)
        assert (
            round(
                dispatch_results_de[
                    "('hoho_cluster_shift_shed', 'dsm_do_shed')"
                ].sum(),
                0,
            )
            == 157
        )
