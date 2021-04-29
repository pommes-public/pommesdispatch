# -*- coding: utf-8 -*-
"""
Created on Mon May  6 09:32:10 2019

General desription
------------------
This file contains all function definitions for reading in input data
used for the fundamental model for power market optimization modelling 
from the Department Energy and Resources of TU Berlin.

These functions are imported by the main project file.

@author: Johannes Kochems, Johannes Giehl, Carla Spiller
"""

# Import necessary packages for function definitions
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from collections import OrderedDict
import pyomo.environ as po


def create_aggregated_energy_source_results(results):
    """ Function creates aggregated production results per energy source 
    as well as information on storage infeed and outfeed and load. 
    
    Parameters
    ----------    
    results : :obj:`pd.DataFrame`
        The results only for the electricity bus and only sequences 
        (i.e. timeseries data), not scalars
     
    Returns
    -------
    Power : :obj:`pd.DataFrame`
        A DataFrame containing the aggregated production results per energy source
        as well as information on storage infeed and outfeed and load
    
    """
    # 15.05.2019 / 20.10.2018, JK: Define labels for accessing results data per energy source
    # resp energy sink.
    energy_sources = ["uranium", "lignite", "hardcoal", "gas", "biomass", "waste", "water", \
                      "mixedfuels", "oil", "otherfossil", "windonshore", "windoffshore", "solarPV", "ROR", "storage_el", "shortage", "hydro"]
    
    energy_sources_dict = OrderedDict()
    
    # Obtain results data from The results DataFrame results (power_results['sequences']).
    # The results.columns.values attribute returns a tuple consisting of two elements, the first one, in turn is a tuple.
    # The first element contains the information from which node x to which node y the variable refers.
    # The second element is the information about the variable type, i.e. a flow variable.
    for source in energy_sources:
        energy_sources_dict[source] = [entry for entry in results.columns.values if (source in entry[0][0] and "DE_bus_el" in entry[0][1] and "flow" in entry[1])]
        
    energy_sinks = ["load", "excess"]
    
    energy_sinks_dict = OrderedDict()
    
    for sink in energy_sinks:
        energy_sinks_dict[sink] = [entry for entry in results.columns.values if ("DE_bus_el" in entry[0][0] and sink in entry[0][1] and "flow" in entry[1])]
        
    energy_sources_dict["storage_el_in"] = [entry for entry in results.columns.values if ("DE_bus_el" in entry[0][0] and "storage_el" in entry[0][1] and "flow" in entry[1])]
    
    # Store the aggregated production results per energy source / sink in a DataFrame
    Power = pd.DataFrame()
    for key, val in energy_sources_dict.items():
        Power[key] = results[val].sum(axis = 1)
        
    for key, val in energy_sinks_dict.items():
        Power[key] = results[val].sum(axis = 1)
    
    return Power


# 08.08.2019, JK: Introduced color settings here for easier interpretation.
def set_color_settings():
    """ Function to choose a colormode for production / merit order plots.
        
    Returns
    -------
    colordict : :obj:`dict`
        The colors to be used for production / merit order plots.   
    
    """
    colordict = {"uranium" : 'darkorange', 
                 "lignite" : 'saddlebrown', 
                 "hard_coal" : 'black', 
                 "gas" : 'darkgrey', 
                 "biomass" : 'green', 
                 "waste" : 'darkgreen', 
                 "water" : 'darkblue',
                 "mixed_fuels" : 'grey', 
                 "oil" : 'lightcoral', 
                 "otherfossil" : 'cadetblue', 
                 "windonshore" : 'dodgerblue', 
                 "windoffshore" : 'blue',
                 "solar" : 'yellow', 
                 "run_of_river" : 'lightblue', 
                 "storage_out" : 'pink', 
                 "shortage" : 'red'}
    
    return colordict


def get_power_prices_from_duals(om, datetime_index):
    """ Function to obtain the power price results for a LP model formulation 
    (dispatch) from the dual value of the Bus.balance constraint of the 
    electricity bus. NOTE: Prices are other than 0 if constraint is binding
    and equal to 0 if constraint is not binding, i.e. if plenty of production
    surplus is available at no cost.
    
    The formulation for accessing duals, taken from pyomo documentation
    https://pyomo.readthedocs.io/en/latest/working_models.html#accessing-duals
    and adapted for the modelling purposes here
    It is accessing an IndexedConstraint from pyomo.core.base.constraint
    
    Parameters:
    -----------
    om: :class:`oemof.solph.models.Model`
        The mathematical model formulation (including its dual values)
        
    datetime_index: :obj:`pd.date_range`
        The datetime_index of the energy system
    
    Returns:
    --------
    power_prices: :obj:`pd.DataFrame`
        
    """
    # 12.08.2019, JK: Introdude a (throwaway) list to store power prices
    power_prices_list = []    
    
    # 13.08.2019, JK: Choose the Bus.balance constraint
    # (There is only one which is indexed by buses as well as timesteps)
    constr = [c for c in om.component_objects(po.Constraint, active = True) if c.name == "Bus.balance"][0]
    
    # 13.08.2019, JK: Add the dual values of the electricity bus to the power prices list
    power_prices_list = [om.dual[constr[index]] for index in constr if index[0].label == "DE_bus_el"]
    power_prices = pd.DataFrame(data = power_prices_list, index = datetime_index, columns = ["Power price"])

    return power_prices


def draw_production_plot(Power,
                         RollingHorizon):
    
    """ Function draws a nice stackplot of the production results.
    Load is plotted too, as dashed line.
    
    Parameters
    ----------
    Power : :obj:`pd.DataFrame`
        A DataFrame containing the aggregated production results per energy source
        as well as information on storage infeed and outfeed and load
    
    RollingHorizon : :obj:`boolean`
        If True, a rolling horizon approach is applied which can be 
        controlled by manipulating the input Excel file
        
    colormode : :obj:`str`
        The colormode to be chosen. It is possible to choose "default" or
        "custom"

    Returns
    -------
    nothing
    
    """
    labels = Power.columns.values
    y = [Power[el] for el in labels]
    y = y[:-3]
    
    # 08.08.2019, JK: Set color settings for the plot for easier interpretation
    colors = set_color_settings().values()

    _ = plt.style.use('ggplot')
    fig, ax = plt.subplots(figsize = (10,5))
    _ = ax.stackplot(Power.index, y, colors = colors, labels = labels)
#    _ = ax.stackplot(Power.index, [Power["Load"], Power["Excess"]], alpha = 0.5)
    _ = ax.plot(Power['load'], linestyle = 'dashed', color = 'black', label = 'load')
    _ = ax.legend(bbox_to_anchor = [1.1, 0.05, 0, 1])
    _ = plt.title('Power plant dispatch')
    _ = plt.axis(xmin = Power.index[0], xmax = Power.index[-1])
    _ = plt.xlabel('time')
    _ = plt.xticks(rotation=45)
    _ = plt.ylabel('capacity in MW')
    _ = ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    _ = plt.tight_layout()
    
    return None

# TODO: Draw further graphs below showing shortage / excess, storage infeed and outfeed as well as net imports and exports
# WORK IN PROGRESS HERE -> @YW: Would you please tidy up this? (Priority is not so large)  
def draw_production_plot_new(Power,
                             RollingHorizon):
    
    """ Function draws a nice stackplot of the production results.
    Load is plotted too, as dashed line.
    
    WORK IN PROGRESS
    
    Parameters
    ----------
    Power : :obj:`pd.DataFrame`
        A DataFrame containing the aggregated production results per energy source
        as well as information on storage infeed and outfeed and load
    
    RollingHorizon : :obj:`boolean`
        If True, a rolling horizon approach is applied which can be 
        controlled by manipulating the input Excel file
    
    Europe : :obj:`boolean`
        If True, a European dispatch is simulated and net exports as well as
        net imports are displayed here
        
    colormode : :obj:`str`
        The colormode to be chosen. It is possible to choose "default" or
        "custom"

    Returns
    -------
    nothing
    
    """
    labels = Power.columns.values
    y1 = [Power[el] for el in labels]
    y1 = y1[:-3]
    
    # 08.08.2019, JK: Set color settings for the plot for easier interpretation
    colors = set_color_settings().values()

    _ = plt.style.use('ggplot')
    
    # if Europe:
    fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize = (10,20), sharex=True)
    # else:
    #     fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize = (10,15), sharex=True)
    
    fig.suptitle('Power plant dispatch', size = 16)
    fig.subplots_adjust(top=2.5)
    
    _ = ax1.stackplot(Power.index, y1, colors = colors, labels = labels)
#    _ = ax.stackplot(Power.index, [Power["Load"], Power["Excess"]], alpha = 0.5)
    _ = ax1.plot(Power['load'], linestyle = 'dashed', color = 'black', label = 'load')
    _ = ax1.legend(bbox_to_anchor = [1.1, 0.05, 0, 1])
    _ = plt.axis(xmin = Power.index[0], xmax = Power.index[-1])
    _ = plt.xlabel('time')
    _ = plt.xticks(rotation=45)
    _ = plt.ylabel('capacity in MW')
#    _ = ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    _ = plt.tight_layout()
    
    y2 = [Power['storage_el'].mul(-1), Power['storage_el_in']]
    _ = ax2.stackplot(Power.index, y2, labels = ['storage_el', 'storage_in'])
    _ = ax2.legend(bbox_to_anchor = [1.1, 0.05, 0, 1])
#    _ = ax2.set_ylim(-1000, 1000)
    
    y3 = [Power['shortage'].mul(-1), Power['excess']]
    _ = ax3.stackplot(Power.index, y3, labels = ['shortage', 'excess'])
    _ = ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    _ = ax3.legend(bbox_to_anchor = [1.1, 0.05, 0, 1])
#    plt.axis(ymin = min(Power['storage_el']), ymax = max((Power['storage_el']))
    
    # TODO: Uncomment and add this when European simulation is up and running
    # if Europe:
    #     pass
#        y4 = [Power['net_exports'].mul(-1), Power['net_imports']]
#        _ = ax4.stackplot(Power.index, y3, labels = ['net_exports', 'net_imports'])
#        _ = ax4.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
#        _ = ax4.legend(bbox_to_anchor = [1.1, 0.05, 0, 1])
    
    return None


# TODO: Tidy up the plot -> @YW: Would you please do that?
def draw_price_plot(Power,
                    power_prices):
    """ Function plots power price results as well as load values on a common
    axis for a mixed-integer model formulation.
    
    Parameters
    ----------
    Power : :obj:`pd.DataFrame`
        A DataFrame containing the aggregated production results per energy source
        as well as information on storage infeed and outfeed and load
        
     power_prices : :obj:`pd.DataFrame`
        A DataFrame containing the marginal costs values of power plants as
        well as the maximum for determining the electricity price (MILP) /
        A DataFrame containing the dual values of the Electricity bus
        which may be interpreted as the power price (LP)

    Returns
    -------
    nothing
    
    """
    # Plot power price and residual load on common axis
    fig, ax1 = plt.subplots(figsize = (10,5))
    ax1 = power_prices.plot(label = "power price", color = "b", ax = ax1)
    _ = plt.ylabel("power price in €/MWh")
    _ = plt.title("Power price time series")
    _ = plt.axis(xmin = Power.index[0], xmax = Power.index[-1])
    _ = ax1.legend(bbox_to_anchor = [1.3, 0.85, 0.1, 0.1])
    _ = plt.xlabel('time')
#    _ = plt.xticks(rotation=45)
#    _ = ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    
    ax2 = ax1.twinx()
    ax2 = Power['load'].plot(label = "load", color = "r", ax = ax2)
    _ = plt.ylabel("Load in MW")
#    _ = ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    _ = ax2.legend(bbox_to_anchor = [1.3, 0.95, 0.1, 0.1])
    _ = plt.tight_layout()
    
    return None