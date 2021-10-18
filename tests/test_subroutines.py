import oemof.solph
import pandas as pd

from pommesdispatch.model_funcs import subroutines, model_control, data_input


def create_inputs_model_and_nodes():
    """Create and return input data, a dispatch model and a node dict"""
    dm = model_control.DispatchModel()
    dm.update_model_configuration(
        {"path_folder_input": "./csv_files/",
         "fuel_cost_pathway": "middle",
         "start_time": "2017-01-01 00:00:00",
         "end_time": "2017-01-02 00:00:00",
         "freq": "60min",
         "emissions_pathway": "100_percent_linear",
         "aggregate_input": False,
         "activate_demand_response": False},
        nolog=True
    )
    input_data = data_input.parse_input_data(dm)
    node_dict = {}

    return input_data, dm, node_dict


class TestSubroutines:
    """Test class for subroutines.py"""

    def test_load_input_data(self):
        """test function load_input_data"""
        csv_file = subroutines.load_input_data(
            filename="transformers_minload_ts_2017_w_nans",
            path_folder_input='./csv_files/',
            countries=["DE", "AT", "FR"])

        assert csv_file.columns.all() == pd.Index(
            ['chp', 'chp_natgas', 'chp_lignite',
             'chp_hardcoal', 'ipp', 'FR_natgas',
             'AT_natgas']).all()
        assert csv_file.index.all() == pd.Index(
            ['2017-01-01 00:00:00',
             '2017-01-01 01:00:00']).all()

    def test_create_buses(self):
        """test function create_buses"""
        input_data, dm, node_dict = create_inputs_model_and_nodes()
        node_dict = subroutines.create_buses(input_data, node_dict)

        assert len(node_dict) == 6
        for node in node_dict.values():
            assert type(node) == oemof.solph.Bus

    def test_create_linking_transformers(self):
        """test function create_linking_transformers"""
        input_data, dm, node_dict = create_inputs_model_and_nodes()
        node_dict = subroutines.create_buses(input_data, node_dict)
        node_dict = subroutines.create_linking_transformers(
            input_data, dm, node_dict)

        assert len(node_dict) == 7
        assert type(node_dict["DE_link_AT"]) == oemof.solph.Transformer
        assert node_dict["DE_link_AT"].conversion_factors[
                   (node_dict["DE_bus_el"],
                    node_dict["AT_bus_el"])].default == 0.95
        assert node_dict["DE_link_AT"].inputs[node_dict[
            "DE_bus_el"]].nominal_value == 100000
        assert node_dict["DE_link_AT"].inputs[node_dict[
            "DE_bus_el"]].max == []

    def test_create_commodity_sources(self):
        """test function create_commodity_sources"""
        input_data, dm, node_dict = create_inputs_model_and_nodes()
        node_dict = subroutines.create_buses(input_data, node_dict)
        node_dict = subroutines.create_commodity_sources(
            input_data, dm, node_dict)

        assert len(node_dict) == 10
        assert type(node_dict["DE_source_hardcoal"]) == oemof.solph.Source
        assert node_dict["DE_source_hardcoal"].outputs[
                 node_dict["DE_bus_hardcoal"]].variable_costs.default == (
            17.853)
