
    # -*- coding: utf-8 -*-
"""
Created on Thu May 2 13:44:03 2019

General desription
------------------
This file contains all function definitions used to include further constraints
within the fundamental model for power market optimization modelling 
from the Department Energy and Resources of TU Berlin.

Functions are imported by the main project file dependent on which constraints
shall be included.

NOTE: THERE MAY BE NO USE FOR THIS MODULE SOMEWHAT SOON.
SO IT PROPABLY WILL BE DROPPED SINCE IT IS MUCH MORE CONSISTENT WITH THE
OEMOF ARCHITECTURE TO INCLUDE CONSTRAINTS FOR THE INDIVIDUAL COMPONENT BLOCKS

@author: Johannes Kochems
"""


# Import necessary packages for function definitions
import pandas as pd

# 14.11.2018, JK: Pyomo import used to add own constraints
import pyomo.environ as po


### SEE COMMENT BELOW AND ABOVE ON USAGE


# NOTE: THE FUNCTION HERE WILL BE KEPT FOR NOW BUT SOMEWHAT SOON BE SUBSTITUTED
# THROUGH PREDEFINED COMPONENTS.
# It is only used by JK, so no need to change anything here.


# TODO: Further implementation (carried out on dev_dr):

# Next steps:
# - Further develop oemof.solph.custom component DR_sink which already has the respective contraints.
#   (several modelling approaches are included and will be compared against each other).
# - Include cost consideration / terms for the target function as well as investment coverage
# - Include parametrization    
def add_demand_response_constraints(om, path_dr, filename_dr, starttime, endtime, ActivateYearLimit=True, ActivateDayLimit=False):
    """ Add demand response constraints according to the modelling approach
    used in Gils, H.C. (2015): Balancing of Intermittent Renewable Power Generation by Demand Response and Thermal Energy Storage.
    
    At first, sets and parameters are defined.
    Then variables for demand response modelling are introduced.
    The actual constraints are formulated within subfunction definitions which return the constraint expression to this function.
    This function builds all the constraints needed and adds them to the overall optimization model.
    All sets, parameters, variables and constraints are defined using an additional Pyomo Block demand_response_block.
    
    As long as useful energy is not considered, these constraints are active for flows from electricity bus to end usage sink for (overall) final electricity demand.
    Later on, useful energy will be considered. This means, the constraints are active for flows from final energy electricity bus to end consumer transformer unit(s) 
    transformer unit.
    
    The basic approach in turn is taken from the oemof example "add_constraints.py" implemented by Simon Hilpert, showing how to integrate own restrictions.
    
    Parameters
    ----------
    om :
        the Pyomo optimization model for which contraints shall be added (i.e. add constraints after reading in nodes data)
    path_dr : :obj:`str`
        place where demand response input file containing demand response data can be found
    filename_dr : :obj:`str`
        filename of input file containing demand response data
    starttime : :obj:`str`
        start timestamp of optimization run (used for slicing demand response input data)
    endtime : :obj:`str`
        end timestamp of optimization run (used for slicing demand response input data)
    ActivateYearLimit : :obj:`boolean`
        boolean parameter controlling whether constraint for amount of yearly demand response activations shall be set or not (optional)
    ActivateDayLimit : :obj:`boolean`
        boolean parameter controlling whether constraint for amount of daily demand response activations shall be set or not (optional)
    
    Returns
    -------
    om:
        the optimization model including the demand response constraints added

    """
    
    ### Define demand response flows as Pyomo Set and Pyomo Block object that holds these
    
    # 16.11.2018, JK: Define demand_flows which are eligible for load flexibility
    # 19.11.2018, JK: To Do for later, when end user efficiency is introduced: Set constraints for FLOWS from electricity bus to end user transformers,
    # i.e. give the end users transformers names which can be systematically accessed.
    
    # 16.11.2018, JK: Define demand_flows which are eligible for load flexibility by accessing nodes via their labels
    # 18.12.2018, JK: A possible approach here would be to determine all flows starting from start node and via this approach identify all end nodes...
    start_nodes_list = [n for n in om.NODES if n.label == "DE_bus_el"]
    end_nodes_list = [n for n in om.NODES if n.label == "DE_load_el"]
#    end_nodes_list = [n for n in om.NODES if n.label in labels_end_nodes]
     
    # 16.12.2018, JK: Definition of Pyomo Sets in order to define parameters and variables for these...
    om.START_NODES = po.Set(initialize = start_nodes_list)
    om.END_NODES = po.Set(initialize = end_nodes_list)
    
    # 16.12.2018, JK: For the simple case, create start as well as end node for demand response flows
    DE_bus_el = start_nodes_list[0]
    DE_load_el = end_nodes_list[0]
    
    # 16.12.2018, JK: Create flows eligible for demand response
    # FLOW IS A DICTIONARY WITH (s, e) as keys and flow[s, e, t] as keys (s: start, e: end, t: timestep)
    demand_flow = om.flows[(DE_bus_el, DE_load_el)]
    
    # create a Pyomo (Simple) Block containing all Sets, Parameters and Constraints
    demand_response_block = po.Block()
    
    # define DRFLOWS (flows from electricity bus to demand sink(s)) for which constraints shall be active
    # 17.12.2018, JK: HINT: PYOMO SETS ARE INITIALIZED WHEN A PROBLEM INSTANCE IS CREATED, see: https://github.com/Pyomo/pyomo/blob/master/examples/pyomo/tutorials/set.py, accessed 17.12.2018
#    demand_response_block.DRFLOWS = po.Set(initialize = demand_flow)
    demand_response_block.DRFLOWS = [demand_flow]
    
    ### Define (additional) Pyomo Sets needed for demand response formulation from Gils (2015)
    
    # 16.11.2018, JK: Sets of load shifting units (X) and shifting times (H) -> TO BE IMPLEMENTED LATER ON!
    # 18.12.2018, JK: Load shifting units resp. flows should be defined through start and end nodes resp. flows above, so this is not needed here
#    om.X = po.RangeSet(0)
    om.H = po.RangeSet(0)
    
    
    # 19.12.2018, JK: Introduce boolean parameters, indicating whether plant is eligible for load shedding only
    om.load_shedding_only = po.Param(om.H)
    
    
    ### Define Pyomo Parameters needed for demand response formulation from Gils (2015)
    
    # 18.11.2018, JK: Addition of parameters according to implementation of model formulation from Gils (2015)
    # maximum (existing) shiftable load
    # 30.11.2018, JK: Use parameter input worksheet later here for setting the initial values
    om.P_exist = po.Param(within = po.NonNegativeReals, initialize = 100)
    
    # read in demand response availability data
    # 30.11.2018, JK: To Do: Put file into an Excel input file and parse the worksheets containing different information 
    # (parameters, availability time series and so on)
    # 16.12.2018, JK: Pyomo allows to read in data using the load statement -> formulation not quite right below but too time consuming...
#    data = po.DataPortal(model = om)
#    data.load(filename = path_dr+filename_dr, param = 's_flex_param', format='param')
    
    dr = pd.read_csv(path_dr+filename_dr, sep=";", decimal=".", parse_dates=True, index_col="timestamp")
    
    # availability parameters for downwards adjustments (s_flex) resp. upwards adjustments (s_free)
    # one value for every (hourly) timestep obtained from input data sheet
    # slicing according to optimization time frame
    s_flex_param = dr['availability up'][starttime:endtime]
    s_free_param = dr['availability down'][starttime:endtime]
    
    om.s_flex = po.Param(om.TIMESTEPS, within = po.NonNegativeReals, initialize = s_flex_param)
    om.s_free = po.Param(om.TIMESTEPS, within = po.NonNegativeReals, initialize = s_free_param)
    
    # average availability parameters (only one value)
    om.s_flex_mean = po.Param(initialize = s_flex_param.mean())
    om.s_free_mean = po.Param(initialize = s_free_param.mean())
    
    # load shifting time (time of complete cicle until energy bilance is levelled out again)
    om.t_shift = po.Param(within = po.NonNegativeIntegers, initialize = 4)
    # duration of a single load adjustment activity (may be shorter, since duration is not forced to that value, instead an ernergy limit for dr process is set)
    om.t_interfere = po.Param(within = po.NonNegativeIntegers, initialize = 1)
    
    # overall (annually) limit for load shifting processes (does not limit the absolute number of activations, but the energy shifted within one year)
    # 18.12.2018, JK: Maybe introduce method here for determining how many sub-annually load shifts are feasible
    om.n_year_limit = po.Param(within = po.NonNegativeIntegers, initialize = 1)
    # efficiency parameter for load shifting process (symmetrical)
    om.eta = po.Param(within = po.NonNegativeReals, initialize = 1.0)
    
    # variable costs of a load shifting process
    om.c_var_ls = po.Param(initialize = -1000)
#    om.c_var_ls = po.Param(within = po.NonNegativeReals, initialize = 0)
    
    # fixed costs of a load shiftig process -> NOT USED YET
    om.c_fixed_ls = po.Param(within = po.NonNegativeReals, initialize = 0)
    
    # investment costs of a load shifting process -> NOT USED YET
    om.c_invest_ls = po.Param(within = po.NonNegativeReals, initialize = 0)
    
    
    
    ### Define Pyomo variables needed for demand response formulation from Gils (2015)
    
    # 17.12.2018, JK: Variables are defined for a subset of om.NODES (i.e. om.START_NODES resp. om.END_NODES)...
    # 17.12.2018, JK: An alternative would be to define variables dependent on flows since a set is introduced but this is implicitly done when constructing constraints...
    
    # load that is reduced or increased (flow variable, indexed by start node, end node as well as timestep)
    om.P_reduction = po.Var(om.START_NODES, om.END_NODES, om.TIMESTEPS, within = po.NonNegativeReals)
    om.P_increase = po.Var(om.START_NODES, om.END_NODES, om.TIMESTEPS, within = po.NonNegativeReals)
    
    # load that is balanced at a certain timestep (flow variable, indexed by start node, end node as well as timestep); initialized to 0
    om.P_balanceRed = po.Var(om.START_NODES, om.END_NODES, om.TIMESTEPS, within = po.NonNegativeReals, initialize = 0)
    om.P_balanceInc = po.Var(om.START_NODES, om.END_NODES, om.TIMESTEPS, within = po.NonNegativeReals, initialize = 0)
    
    # fictional demand response storage level; initialized to 0
    om.W_levelRed = po.Var(om.START_NODES, om.END_NODES, om.TIMESTEPS, within = po.NonNegativeReals, initialize = 0)
    om.W_levelInc = po.Var(om.START_NODES, om.END_NODES, om.TIMESTEPS, within = po.NonNegativeReals, initialize = 0)
    
    # adjusted load after load shift measures -> TO DO: INTEGRATE ADJUSTED LOAD AS WELL AS DR COSTS INTO TARGET FUNCTION
    # IMPORTANT HINTS FOR INTEGRATING TERMS INTO TARGET FUNCTION SEE BELOW.
    
    # 18.12.2018, JK: oemof.sloph rational: 
    # - parts of the objective function are created within oemof.solph.blocks, see: https://oemof.readthedocs.io/en/stable/_modules/oemof/solph/blocks.html, accessed 18.12.2018
    # - individual blocks, e.g. oemof.solph.blocks.Flow add up constraints as well as parts of the target function via functions _objective_expression(self)
    # - Actually, it therefore should be sufficient to define a new class "FlexFlow" which inherits from the class "Flow" with the function _objective_expression(self) being modified
    # - Demand satisfaction is implicitly specified by demanding that energy balance of buses must be levelled out, see: https://oemof.readthedocs.io/en/stable/_modules/oemof/solph/blocks.html#Bus, accessed 18.12.2018.
    
    # 18.12.2018, JK: CHECK WHETHER IT IS POSSIBLE TO OVERWRITE FLOW VALUES USING THE ADJUSTED LOAD...
    # For an alternative formulation see constraint 8) below...
    om.Load_adj = po.Var(om.START_NODES, om.END_NODES, om.TIMESTEPS, within = po.NonNegativeReals)
    
    
    # add Pyomo block to the optimization model
    # 19.11.2018, JK: Not sure, whether demand response Block should contain parameters as well as variables, but I guess so...
    # 13.12.2018, JK: Problem here: There are no flow elements within demand_response_block, so an Error occurs if component is constructed from data = None.
#    om.add_component("DR_Block", demand_response_block)
    
    
    
    ### Define Pyomo constraints needed for demand response formulation from Gils (2015)
    
    # MEMO FOR JK (delete later on): For original model formulation using gurobipy see jupyter notebook "UC_Meus_2018_Flex_Gils_2015_V05.ipynb"
    
    # 17.12.2018, JK: Introduced some adaptions for timesteps prior to t = 0 as well as for the last timesteps when load adjustments cannot be compensated for 
    # (i.e. introduced of if-conditions for handling this)
    # see: https://oemof.readthedocs.io/en/stable/_modules/oemof/solph/blocks.html#Flow, accessed 17.12.2018.
    
    
    # 19.12.2018, JK: energy balance rule only for load shifting, not for load shedding -> Take care of proper code identation when introducing this (see comments below)!
#    if not om.load_shedding_only:
# BEGIN: CODE IDENTATION
        
    # No 1a) demand response energy balance rules (for initial load reduction)
    def energy_balance_rule_red(om, s, e, t):
        """ Formulate Pyomo demand response energy balance rule for initial load reduction.
        """
        # Avoid timesteps prior to t = 0
        if t - om.t_shift >= 0:
            expr = (om.P_balanceRed[s, e, t] == om.P_reduction[s, e, t - om.t_shift] / om.eta)
        else:
            expr = om.P_balanceRed[s, e, t] == 0
        return expr
    
    # 23.11.2018, JK: Constraint should hold for flows within the Set DRFLOWS and for every timestep within om.TIMESTEPS -> Check whether syntax produces this
    demand_response_block.energy_balance_red =  po.Constraint(demand_response_block.DRFLOWS, om.TIMESTEPS, rule = energy_balance_rule_red)

    # No 1b) demand response energy balance rules (for initial load increase)
    def energy_balance_rule_inc(om, s, e, t):
        """ Formulate Pyomo demand response energy balance rule for initial load increase.
        """
        # Avoid timesteps prior to t = 0
        if t - om.t_shift >= 0:
            expr = (om.P_balanceInc[s, e, t] == om.P_increase[s, e, t - om.t_shift] * om.eta)
        else:
            expr = om.P_balanceInc[s, e, t] == 0
        return expr
    
    demand_response_block.energy_balance_inc =  po.Constraint(demand_response_block.DRFLOWS, om.TIMESTEPS, rule = energy_balance_rule_inc)
    
    
    # No. 2a) demand response availability constraints (for initial load reduction)
    def availability_red_rule(om, s, e, t):
        """ Formulate Pyomo demand response (time-dependent) availability rule for initial load reduction.
        """
        if t + om.t_shift <= len(om.TIMESTEPS):
            expr = (om.P_reduction[s, e, t] + om.P_balanceInc[s, e, t] <= om.P_exist * om.s_flex[t])
        # No load shift feasible which cannot be compensated within optimization timeframe
        else:
            expr = om.P_reduction[s, e, t] == 0
        return expr
    
    demand_response_block.availability_down =  po.Constraint(demand_response_block.DRFLOWS, om.TIMESTEPS, rule = availability_red_rule)

# END: CODE IDENTATION

        
    # No. 2b) demand response availability constraints (for initial load increase)
    def availability_inc_rule(om, s, e, t):
        """ Formulate Pyomo demand response (time-dependent) availability rule for initial load increase.
        """
        if t + om.t_shift <= len(om.TIMESTEPS):
            expr = (om.P_increase[s, e, t] + om.P_balanceRed[s, e, t] <= om.P_exist * om.s_free[t])
        # No load shift feasible which cannot be compensated within optimization timeframe
        else:
            expr = om.P_increase[s, e, t] == 0
        return expr
    
    demand_response_block.availability_up =  po.Constraint(demand_response_block.DRFLOWS, om.TIMESTEPS, rule = availability_inc_rule)


    # 19.12.2018, JK: demand response storage rules only for load shifting, not for load shedding -> Take care of proper code identation when introducing this (see comments below)!
#    if not om.load_shedding_only:
# BEGIN: CODE IDENTATION    
    
    # No. 3a) demand response fictional storage level cosntraints (for load increase)
    def dr_storage_red_rule(om, s, e, t):
        """ Formulate Pyomo demand response storage level rule for load reduction.
        """
        # Avoid timesteps prior to t = 0; timeincrement can be neglegted for hourly timesteps
        if t > 0:
            expr = (om.timeincrement[t] * (om.P_reduction[s, e, t] - om.P_balanceRed[s, e, t] * om.eta) == om.W_levelRed[s, e, t] - om.W_levelRed[s, e, t-1])
        else:
            expr = om.W_levelRed[s, e, t] == 0
        return expr
    
    demand_response_block.dr_storage_red =  po.Constraint(demand_response_block.DRFLOWS, om.TIMESTEPS, rule = dr_storage_red_rule)
    
    # No. 3b) demand response fictional storage level cosntraints (for load increase)
    def dr_storage_inc_rule(om, s, e, t):
        """ Formulate Pyomo demand response storage level rule for load increase.
        """
        # Avoid timesteps prior to t = 0; timeincrement can be neglegted for hourly timesteps
        if t > 0:
            expr = (om.timeincrement[t] * (om.P_increase[s, e, t] * om.eta - om.P_balanceInc[s, e, t]) == om.W_levelInc[s, e, t] - om.W_levelInc[s, e, t-1])
        else:
            expr = om.W_levelInc[s, e, t] == 0
        return expr
    
    demand_response_block.dr_storage_inc =  po.Constraint(demand_response_block.DRFLOWS, om.TIMESTEPS, rule = dr_storage_inc_rule)
    
    # No. 4a) demand response storage level limit (for load reduction)
    def dr_storage_limit_red_rule(om, s, e, t):
        """ Formulate Pyomo demand response storage level limit rule for load reduction.
        """
        expr = (om.W_levelRed[s, e, t] <= om.P_exist * om.s_flex_mean * om.t_interfere)
        return expr
    
    demand_response_block.dr_storage_limit_red =  po.Constraint(demand_response_block.DRFLOWS, om.TIMESTEPS, rule = dr_storage_limit_red_rule)
    
    # No. 4b) demand response storage level limit (for load increase)
    def dr_storage_limit_inc_rule(om, s, e, t):
        """ Formulate Pyomo demand response storage level limit rule for load increase.
        """
        expr = (om.W_levelInc[s, e, t] <= om.P_exist * om.s_free_mean * om.t_interfere)
        return expr
    
    demand_response_block.dr_storage_limit_inc =  po.Constraint(demand_response_block.DRFLOWS, om.TIMESTEPS, rule = dr_storage_limit_inc_rule)   

# END: CODE IDENTATION 


    # 23.11.2018, JK: Optional demand response constraints
    # Do if yearly limit for demand response processes is active
    if ActivateYearLimit:
        
        # 19.12.2018, JK: No need to check this for load shedding only because it is true in any case...
        
        # No. 5a) demand response storage level limit (for load reduction)
        def dr_yearly_limit_red_rule(om, s, e, t):
            """ Formulate Pyomo demand response rule for absolute overall yearly load reduction limit.
            """
            expr = (sum(om.P_reduction[s, e, t] for t in om.TIMESTEPS) <= om.P_exist * om.s_flex_mean * om.t_interfere * om.n_year_limit)
            return expr
        
        demand_response_block.dr_yearly_limit_red =  po.Constraint(demand_response_block.DRFLOWS, om.TIMESTEPS, rule = dr_yearly_limit_red_rule) 
        
        # No. 5b) demand response storage level limit (for load increase)
        def dr_yearly_limit_inc_rule(om, s, e, t):
            """ Formulate Pyomo demand response rule for absolute overall yearly load increase limit.
            """
            expr = (sum(om.P_increase[s, e, t] for t in om.TIMESTEPS) <= om.P_exist * om.s_free_mean * om.t_interfere * om.n_year_limit)
            return expr
        
        demand_response_block.dr_yearly_limit_inc =  po.Constraint(demand_response_block.DRFLOWS, om.TIMESTEPS, rule = dr_yearly_limit_inc_rule)
    
    # Do if daily limit for demand response processes is active    
    if ActivateDayLimit:
        
        # 19.12.2018, JK: No need to check this for load shedding only because it is true in any case...
        
        # 17.12.2018, JK: TO DO: ADD ADAPTIONS HERE IN ORDER TO INTEGRATE DEMAND RESPONSE
        # No. 6a) demand response storage level limit (for load reduction)
        def dr_daily_limit_red_rule(om, s, e, t):
            """ Formulate Pyomo demand response rule for absolute overall daily load reduction limit.
            """
            if t >= om.t_day_limit:
                expr = (om.P_reduction[s, e, t] <= om.P_exist * om.s_flex_mean * om.t_interfere - \
                        sum(om.P_reduction[s, e, t-t_dash] for t_dash in range(1, om.t_day_limit+1)) for t in om.TIMESTEPS)
            else:
                expr = False # 18.12.2018, JK: Alternative here is not yet properly defined. But low priority as long as annual energy above limit is working.
            return expr
        
        demand_response_block.dr_yearly_limit_red =  po.Constraint(demand_response_block.DRFLOWS, om.TIMESTEPS, rule = dr_yearly_limit_red_rule) 
        
        # No. 6b) demand response storage level limit (for load increase)
        def dr_yearly_limit_inc_rule(om, s, e, t):
            """ Formulate Pyomo demand response rule for absolute overall daily load increase limit.
            """
            if t >= om.t_day_limit:
                expr = (om.P_increase[s, e, t] <= om.P_exist * om.s_free_mean * om.t_interfere - \
                        sum(om.P_increase[s, e, t-t_dash] for t_dash in range(1, om.t_day_limit+1)) for t in om.TIMESTEPS)
            else:
                expr = False # 18.12.2018, JK: Alternative here is not yet properly defined. But low priority as long as annual energy limit above is working.
            return expr
        
        demand_response_block.dr_yearly_limit_inc =  po.Constraint(demand_response_block.DRFLOWS, om.TIMESTEPS, rule = dr_yearly_limit_inc_rule)
        
    ### Addition to model from Gils (2015) from here on

    # 19.12.2018, JK: No need to check this for load shedding only because it is true in any case...
    
    # No. 7) logical constraint to ensure that there is no load increase and load decrease at the same time
    def dr_logical_constraint_rule(om, s, e, t):
        """ Define Pyomo logical demand response rule to ensure that there is no load increase as well as load decrease at the same time.
        """
        expr = (om.P_increase[s, e, t] + om.P_balanceRed[s, e, t] + om.P_reduction[s, e, t] + om.P_balanceInc[s, e, t] <= om.P_exist)
        return expr
        
    demand_response_block.dr_logical_constraint =  po.Constraint(demand_response_block.DRFLOWS, om.TIMESTEPS, rule = dr_logical_constraint_rule)
    
    # No. 8) constraint for calculating adjusted load (which yet has to be included in overall energy balance condition, i.e. adaption of oemof.solph needed here)
#    def dr_adj_load_rule(om, s, e, t):
#        """ Define Pyomo logical demand response rule to ensure that there is no load increase as well as load decrease at the same time.
#        """
#        expr = (om.Load_adj[s, e, t] == om.flow[s, e, t] + (om.P_increase[s, e, t] + om.balanceRed[s, e, t]) - (om.P_reduction[s, e, t] - om.P_balanceInc[s, e, t]))
#        return expr
#        
#    demand_response_block.dr_adj_load_constraint =  po.Constraint(demand_response_block.DRFLOWS, om.TIMESTEPS, rule = dr_adj_load_rule)
    
    def dr_adj_load_rule(om, s, e, t):
        """ Define Pyomo logical demand response rule to ensure that there is no load increase as well as load decrease at the same time.
        """
        expr = (om.flow[s, e, t] == om.flow[s, e, t] + (om.P_increase[s, e, t] + om.balanceRed[s, e, t]) - (om.P_reduction[s, e, t] - om.P_balanceInc[s, e, t]))
        return expr
        
    demand_response_block.dr_adj_load_constraint =  po.Constraint(demand_response_block.DRFLOWS, om.TIMESTEPS, rule = dr_adj_load_rule)
    
    # 19.12.2018, JK: force several parameters to 0 for load shedding -> Take care of proper code identation when introducing this (see comments below)!
#    if not om.load_shedding_only:
# BEGIN: CODE IDENTATION
#        om.P_reduction == 0
        
# END: CODE IDENTATION    
    
    
    return om

#    for (s, e), t in (demand_response_block.DRFLOWS), om.TIMESTEPS:
#        print(om.Load_adj[t])