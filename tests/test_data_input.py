import oemof.solph

from pommesdispatch.model_funcs import data_input, model_control


def create_dispatch_model():
    """Create a dispatch model and attribute it with some information"""
    dm = model_control.DispatchModel()
    dm.update_model_configuration(
        {"path_folder_input": "./csv_files/",
         "fuel_cost_pathway": "middle",
         "start_time": "2017-01-01 00:00:00",
         "end_time": "2017-01-02 00:00:00",
         "emissions_pathway": "100_percent_linear",
         "aggregate_input": False,
         "activate_demand_response": False},
        nolog=True
    )
    return dm


class TestDataInput:
    """Test class for data_input.py"""

    def test_parse_input_data(self):
        """test function parse_input_data"""
        dm = create_dispatch_model()
        input_data = data_input.parse_input_data(dm)
        assert len(input_data.keys()) == 25
        input_data_keys = [
            'linking_transformers', 'linking_transformers_ts',
            'sinks_excess', 'sinks_demand_el',
            'sinks_demand_el_ts', 'sources_shortage',
            'sources_renewables_fluc', 'costs_market_values',
            'buses', 'sources_commodity', 'sources_renewables',
            'sources_renewables_ts', 'storages_el',
            'transformers', 'transformers_minload_ts',
            'transformers_renewables', 'costs_fuel',
            'costs_ramping', 'costs_carbon', 'costs_operation',
            'costs_operation_renewables',
            'costs_operation_storages', 'emission_limits',
            'min_loads_dh', 'min_loads_ipp'
        ]
        for el in input_data_keys:
            assert el in input_data.keys()

    def test_add_components(self):
        """Test function add_components"""
        dm = create_dispatch_model()
        input_data = data_input.parse_input_data(dm)
        node_dict = data_input.add_components(input_data, dm)
        node_dict_keys = [
            'DE_bus_el', 'DE_bus_hardcoal', 'DE_bus_solarPV',
            'DE_bus_windonshore', 'DE_bus_windoffshore',
            'AT_bus_el', 'DE_link_AT', 'DE_source_hardcoal',
            'DE_source_solarPV', 'DE_source_windoffshore',
            'DE_source_windonshore', 'DE_source_el_shortage',
            'DE_source_biomassEEG', 'DE_sink_el_load',
            'DE_sink_el_excess',
            'DE_transformer_hardcoal_BNA0232b',
            'DE_solarPV_cluster_1', 'DE_solarPV_cluster_2',
            'DE_windonshore_cluster_1',
            'DE_windonshore_cluster_2',
            'DE_windoffshore_cluster_1',
            'DE_windoffshore_cluster_2'
        ]
        node_dict_dtypes = [oemof.solph.Source, oemof.solph.Sink,
                            oemof.solph.Bus, oemof.solph.Transformer]
        for key, value in node_dict.items():
            assert key in node_dict_keys
            assert type(value) in node_dict_dtypes

    def test_add_limits(self):
        """Test function add_limits for adding an emissions limit"""
        dm = create_dispatch_model()
        input_data = data_input.parse_input_data(dm)
        emissions_limit = data_input.add_limits(
            input_data,
            dm.emissions_pathway,
            dm.start_time,
            dm.end_time)

        assert round(emissions_limit) == 853425
