
.. _formulas:

Mathematical formulation
------------------------

All constraints formulations can be found in the
`oemof.solph documentation <https://oemof-solph.readthedocs.io/en/latest/reference/oemof.solph.html>`_.
We'll provide a complete mathematical description for the parts we
used here soon.

Nomenclature
++++++++++++

.. csv-table:: Sets, variables and parameters
    :header: **name**, **type**, **description**
    :widths: 15, 15, 70

    ":math:`N`", "set", "| all nodes of the energy system.
    | This comprises Sources, Sinks, Buses, Transformers,
    | Generic Storages and optionally DSMSinks"
    ":math:`T`", "set", "| all time steps within the optimization timeframe
    | (and time increment, i.e. frequency) chosen"
    ":math:`F`", "set", "| all flows of the energy system.
    | A flow is a directed connection between node A and B
    | and has a value (i.e. capacity flow) for every time step"
    ":math:`TF`", "set", "all transformers (conversion units, such as generators)"
    ":math:`PGF`", "set", "all flows imposing a limit to the positive gradient"
    ":math:`NGF`", "set", "all flows imposing a limit to the negative gradient"
    ":math:`B`", "set", "all buses (fictious busbars to connect capacity resp. energy flows)"
    ":math:`S`", "set", "all storage units"
    ":math:`I(n)`", "set", "all inputs for node n"
    ":math:`O(n)`", "set", "all outputs for node n"
    ":math:`f(i,o,t)`", "variable", "Flow from node i (input) to node o (output) at time step t"
    ":math:`C`", "variable", "system costs"
    ":math:`p_{DE}(t)`", "variable", "power price for Germany"
    ":math:`P_{i}(n, t)`", "variable", "inflow into transformer n at time step t"
    ":math:`P_{o}(n, t)`", "variable", "outflow from transformer n at time step t"
    ":math:`E(s, t)`", "variable", "energy currently stored in storage s"
    ":math:`c_{var}(i, o, t)`", "parameter", "variable costs for flow from input i to output o at time step t"
    ":math:`\tau(t)`", "parameter", "time increment of the model for time step t"
    ":math:`D_{DE}(t)`", "parameter", "total load (for Germany)"
    ":math:`\eta_{o}(n, t)`", "parameter", "conversion efficiency for outflow"
    ":math:`\eta_{i}(n, t)`", "parameter", "conversion efficiency for inflow"
    ":math:`\Delta P_{pos}(i, o, t)`", "parameter", "| maximum allowed positive gradient for flow from input i to output o
    | at time step t (transition from t-1 to t)"
    ":math:`\Delta P_{neg}(i, o, t)`", "parameter", "| maximum allowed negative gradient for flow from input i to output o
    | at time step t (transition from t-1 to t)"
    ":math:`P_{nom}(i, o)`", "parameter", "| installed capacity (all except RES outside Germany)
    | or maximum achievable output value (RES outside Germany)"
    ":math:`f_{min}(i, o, t)`", "parameter", "normalized minimum output for flow from input i to output o"
    ":math:`f_{max}(i, o, t)`", "parameter", "normalized maximum output for flow from input i to output o"
    ":math:`E_{nom}(s)`", "parameter", "| nominal capacity of storage s (maximum achievable capacity
    | based on historic utilization, not the installed one)"
    ":math:`E_{min}(s, t)`", "parameter", "minimum allowed storage level for storage s"
    ":math:`E_{max}(s, t)`", "parameter", "maximum allowed storage level for storage s"
    ":math:`\beta(s, t)`", "parameter", "fraction of lost energy as share of :math:`E(s, t)`"
    ":math:`\gamma(s, t)`", "parameter", "fixed loss of energy relative to :math:`E_{nom}(s)` per time unit"
    ":math:`\delta(s, t)`", "parameter", "absolute fixed loss of energy per time unit"
    ":math:`\dot{E}_i(s, t)`", "parameter", "energy flowing into storage s at time step t"
    ":math:`\dot{E}_o(s, t)`", "parameter", "energy extracted from storage s at time step t"
    ":math:`\eta_i(s, t)`", "parameter", "conversion factor (i.e. efficiency) of storage s for storing energy"
    ":math:`\eta_o(s, t)`", "parameter", "| conversion factor (i.e. efficiency) of storage s for withdrawing
    | stored energy"
    ":math:`t_u`", "parameter", "time unit of losses :math:`\beta(t)`, :math:`\gamma(t)`, :math:`\delta(t)` and time increment :math:`\tau(t)`"
    ":math:`ef(i, o)`", "parameter", "emission factor in :math:`\frac {t \space CO_2}{MWh}`"
    ":math:`EL`", "parameter", "overall emission linit in :math:`t \space CO_2`"


Target function
+++++++++++++++
The target function is build together by the ``_objective_expression`` terms of all
oemof.solph components used (`see the oemof.solph.models module <https://github.com/oemof/oemof-solph/blob/dev/src/oemof/solph/models.py>`_):


System costs: sum of the costs for all flows (commodity / fuel, emissions and operation costs):

.. math::

    & Min \space C = \sum_{(i,o)} \sum_t f(i, o, t) \cdot c_{var}(i, o, t) \\
    & \forall \space (i, o) \in \mathrm{F}, \space t \in \mathrm{T}

Constraints of the core model
+++++++++++++++++++++++++++++

The following constraints apply to a model in its basic formulation (i.e.
not including demand response and emissions limits):

* flow balance(s):

.. math::

    & \sum_{i \in I(n)} f(i, n, t) \cdot \tau(t)
    = \sum_{o \in O(n)} f(n, o, t) \cdot \tau(t) \\
    & \forall \space n \in \mathrm{B}, \space t \in \mathrm{T}

with :math:`\tau(t)` equalling to the time increment (defaults to 1 hour)

.. note::

    This is equal to an overall energy balance requirement, but build up
    decentrally from a balancing requirement of every bus, thus allowing for
    a flexible expansion of the system size.

The power price for Germany is derived from the dual values (shadow prices)
of the flow balance for the German electricity price:

.. math::

    p_{DE}(t) = \frac {\partial C}{\partial D_{DE}(t)}

* energy transformation:

.. math::
    & P_{i}(n, t) \times \eta_{o}(n, t) =
    P_{o}(n, t) \times \eta_{i}(n, t), \\
    & \forall \space t \in \mathrm{T}, \space n \in \mathrm{TF},
    \space i \in \mathrm{I(n)}, \space o \in \mathrm{O(n)}

with :math:`P_{i}(n, t)` as the inflow into the transformer node n,
:math:`P_{o}(n, t)` as the transformer outflow, :math:`\eta_{o}(n, t)` the
conversion efficiency for outputs and :math:`\eta_{i}(n, t)` the conversion
factors for inflows. We only use the conversion factor for outflows to account
for losses from the conversion (within the power plant).
:math:`\mathrm{TF}` is the set of transformers, i.e. any kind of energy conversion
unit. We use this for conventional generators, renewable energy sources (RES)
within the market premium scheme in Germany (with 100% efficiency -
used just to steer the price-based output in times, RES are price setting)
as well as interconnection line losses.

* gradient limits for generators

.. math::

    & f(i, o, t) - f(i, o, t-1) \leq \Delta P_{pos}(i, o, t) \\
    & \forall \space (i, o) \in \mathrm{PGF},
    \space t \in \mathrm{T} \\
    & \\
    & f(i, o, t-1) - f(i, o, t) \leq \Delta P_{neg}(i, o, t) \\
    & \forall \space (i, o) \in \mathrm{NGF},
    \space t \in \mathrm{T}

with :math:`\Delta P_{pos}(i, o, t)` equalling to the maximum allowed positive
an :math:`\Delta P_{neg}(i, o, t)` equalling to the maximum allowed negative
gradient and :math:`\mathrm{PGF}` resp. :math:`\mathrm{NGF}` being the set
of flows with positive or negative gradient limits (i.e. conventional
generators).

* minimum and maximum load requirements

.. math::

    & f(i, o, t) \geq f_{min}(i, o, t) \cdot P_{nom}(i, o) \\
    & \forall \space (i, o) \in \mathrm{F},
    \space t \in \mathrm{T} \\
    & \\
    & f(i, o, t) \leq f_{max}(i, o, t) \cdot P_{nom}(i, o) \\
    & \forall \space (i, o) \in \mathrm{F},
    \space t \in \mathrm{T}

with :math:`P_{nom}(i, o)` equalling to the installed resp. maximum capacity,
:math:`f_{min}(i, o, t)` as the normalized minimum flow value
and :math:`f_{max}(i, o, t)` as the normalized maximum flow value.

.. note::

    Whereas the maximum value is fixed and set to 1 for all units and time steps,
    the minimum value of some generator types may alter over time.
    This is especially true for combined heat and power (CHP) plants
    and industrial power plants (IPP), where a minimum load pattern
    is fed in, in order to serve the heating or process steam demand.

* storages

    * Storage roundtrip:

    .. math::

        E(s, |\mathrm{T}|) = E(s, -1)

with the last storage level :math:`E(s, |\mathrm{T}|)` equalling the
initial storage content :math:`E(s, -1)`.

    * Storage balance:

    .. math::

        & E(s, t) = E(s, t-1) \cdot (1 - \beta(s, t)) ^{\tau(t)/(t_u)} \\
        & - \gamma(s, t)\cdot E_{nom}(s) \cdot {\tau(t)/(t_u)}
        - \delta(t) \cdot {\tau(t)/(t_u)} \\
        & - \frac{\dot{E}_o(s, t)}{\eta_o(s, t)} \cdot \tau(t)
        + \dot{E}_i(s, t) \cdot \eta_i(s, t) \cdot \tau(t) \\
        & \forall \space s \in \mathrm{S}, \space t \in \mathrm{T}

with :math:`E_{nom}(s)` as the nominal storage capacity,
:math:`\beta(t)` as the relative loss of stored energy,
:math:`\gamma(t)` as the fixed loss of stored energy relative to the
nominal storage capacity,
:math:`\delta(t)` as the fixed losses in absolute terms and
:math:`t_u` the time unit to create dimensionless factors resp. exponents.

    * Storage level limits:

    .. math::

        & E_{min}(s, t) \leq E(s, t) \leq E_{max}(s, t) \\
        & \forall \space s \in \mathrm{S}, \space t \in \mathrm{T}

with :math:`E_{min}(s, t)` as the minimum and :math:`E_{max}(s, t)`
as the maximum allowed storage content for time step t.

Constraints for core model extensions
+++++++++++++++++++++++++++++++++++++

The following constraints can be optionally included in the model
formulation if the respective control parameter in the configuration file
are set accordingly, see :ref:`config`.

Emissions limit
===============

Limit the overall annual emissions (resp. emissions for the timeframe considered):

.. math::

    & \sum_{(i,o)} \sum_t f(i, o, t) \cdot \tau(t) \cdot ef(i, o) \leq EL \\
    & \space (i, o) \in \mathrm{F}

with :math:`ef(i, o)` as the specific emission factor and :math:`EL` as the
overall emission cap for the simulation time frame (usually one year).

Demand response constraints
===========================

Since demand response is one of the key interest points of *POMMES*, there
are three different implementations which can be chosen from:

    * *DIW*: Based on a paper by Zerrahn and Schill (2015), pp. 842-843.
    * *DLR*: Based on the PhD thesis of Gils (2015)
    * *oemof*: Created by Julian Endres. A fairly simple DSM representation
      which demands the energy balance to be levelled out in fixed cycles

    An evaluation of different modeling approaches has been carried out and
    presented at the INREC 2020 (Kochems 2020). Some of the results are as follows:

    * DLR: An extensive modeling approach for demand response which neither
      leads to an over- nor underestimization of potentials and balances
      modeling detail and computation intensity.
    * DIW: A solid implementation with the tendency of slight overestimization
      of potentials since a `shift_time` is not included. It may get
      computationally expensive due to a high time-interlinkage in constraint
      formulations.
    * oemof: A very computationally efficient approach which only requires the
      energy balance to be levelled out in certain intervals. If demand
      response is not at the center of the research and/or parameter
      availability is limited, this approach should be chosen.
      Note that approach `oemof` does allow for load shedding,
      but does not impose a limit on maximum amount of shedded energy.

For the sake of readability, the variables and parameters used for demand
response modeling are listed separately in the following table:

.. table:: Sets (S), Variables (V) and Parameters (P)
    :widths: 1, 1, 1, 1

    ================================= ==== ==================================================================== ==============
    symbol                            type explanation                                                          approach
    ================================= ==== ==================================================================== ==============
    :math:`DSM_{t}^{up}`              V    DSM up shift (capacity shifted upwards)                              oemof, DIW
    :math:`DSM_{h, t}^{up}`           V    DSM up shift (additional load) in hour t with delay time h           DLR
    :math:`DSM_{t}^{do, shift}`       V    DSM down shift (capacity shifted downwards)                          oemof
    :math:`DSM_{t, tt}^{do, shift}`   V    | DSM down shift (less load) in hour tt                              DIW
                                           | to compensate for upwards shifts in hour t
    :math:`DSM_{h, t}^{do, shift}`    V    DSM down shift (less load) in hour t with delay time h               DLR
    :math:`DSM_{h, t}^{balanceUp}`    V    | DSM down shift (less load) in hour t with delay time h             DLR
                                           | to balance previous upshift
    :math:`DSM_{h, t}^{balanceDo}`    V    | DSM up shift (additional load) in hour t with delay time h         DLR
                                           | to balance previous downshift
    :math:`DSM_{t}^{do, shed}`        V    DSM shedded (capacity shedded, i.e. not compensated for)             all
    :math:`\dot{E}_{t}`               V    Energy flowing in from (electrical) inflow bus                       all
    :math:`demand_{t}`                P    (Electrical) demand series (normalized)                              all
    :math:`demand_{max}`              P    Maximum demand value                                                 all
    :math:`h`                         P    | Maximum delay time for load shift (integer value                   DLR
                                           | from set of feasible delay times per DSM portfolio;
                                           | time until the energy balance has to be levelled out again;
                                           | roundtrip time of one load shifting cycle, i.e. time window
                                           | for upshift and compensating downshift)
    :math:`H_{DR}`                    S    | Set of feasible delay times for load shift                         DLR
                                           | of a certain DSM portfolio
    :math:`t_{shift}`                 P    | Maximum time for a shift in one direction,                         DLR
                                           | i. e. maximum time for an upshift *or* a downshift
                                           | in a load shifting cycle
    :math:`L`                         P    | Maximum delay time for load shift                                  DIW
                                           | (time until the energy balance has to be levelled out again;
                                           | roundtrip time of one load shifting cycle, i.e. time window
                                           | for upshift and compensating downshift)
    :math:`t_{she}`                   P    Maximum time for one load shedding process                           DLR, DIW
    :math:`E_{t}^{do}`                P    | Capacity  allowed for a load adjustment downwards                  all
                                           | (normalized; shifting + shedding)
    :math:`E_{t}^{up}`                P    Capacity allowed for a shift upwards (normalized)                    all
    :math:`E_{do, max}`               P    | Maximum capacity allowed for a load adjustment downwards           all
                                           | (shifting + shedding)
    :math:`E_{up, max}`               P    Maximum capacity allowed for a shift upwards                         all
    :math:`\tau`                      P    | interval (time within which the                                    oemof
                                           | energy balance must be levelled out)
    :math:`\eta`                      P    Efficiency for load shifting processes                               all
    :math:`\mathbb{T}`                P    Time steps of the model                                              all
    :math:`e_{shift}`                 P    | Boolean parameter indicating if unit can be used                   all
                                           | for load shifting
    :math:`e_{shed}`                  P    | Boolean parameter indicating if unit can be used                   all
                                           | for load shedding
    :math:`cost_{t}^{dsm, up}`        P    Variable costs for an upwards shift                                  all
    :math:`cost_{t}^{dsm, do, shift}` P    Variable costs for a downwards shift (load shifting)                 all
    :math:`cost_{t}^{dsm, do, shed}`  P    Variable costs for shedding load                                     all
    :math:`\Delta t`                  P    The time increment of the model                                      DLR, DIW
    :math:`\omega_{t}`                P    Objective weighting of the model for time step t                     all
    :math:`R_{shi}`                   P    | Minimum time between the end of one load shifting process          DIW
                                           | and the start of another
    :math:`R_{she}`                   P    | Minimum time between the end of one load shedding process          DIW
                                           | and the start of another
    :math:`n_{yearLimitShift}`        P    | Maximum allowed number of load shifts (at full capacity)           DLR
                                           | in the optimization timeframe
    :math:`n_{yearLimitShed}`         P    | Maximum allowed number of load sheds (at full capacity)            DLR
                                           | in the optimization timeframe
    :math:`t_{dayLimit}`              P    | Maximum duration of load shifts at full capacity per day           DLR
                                           | resp. in the last hours before the current"
    ================================= ==== ==================================================================== ==============


In the following, the constraint formulations and objective terms
are given separately for each approach:

.. note::

    | The constraints and objective terms hold for all demand response units which are
    | aggregated to demand response clusters (with homogeneous costs and delay resp. shifting times).
    | For the sake of readability, the technology index is not displayed.
    | Furthermore, for some constraints there may be index violations which are taken care of by
    | limiting to the feasible time indices :math:`{0, 1, .., |T|}`. This is also not displayed for the sake of readability.
    | For the complete implementation and details, please refer to `the sink_dsm module of oemof.solph <https://github.com/oemof/oemof-solph/blob/master/src/oemof/solph/custom/sink_dsm.py>`_.

**approach `oemof`**:

* Constraints:

.. math::
    &
    (1) \quad DSM_{t}^{up} = 0 \\
    & \quad \quad \quad \quad \forall t \in \mathbb{T}
    \quad \textrm{if} \quad e_{shift} = \textrm{False} \\
    & \\
    &
    (2) \quad DSM_{t}^{do, shed} = 0 \\
    & \quad \quad \quad \quad \forall t \in \mathbb{T}
    \quad \textrm{if} \quad e_{shed} = \textrm{False} \\
    & \\
    &
    (3) \quad \dot{E}_{t} = demand_{t} \cdot demand_{max} + DSM_{t}^{up}
    - DSM_{t}^{do, shift} - DSM_{t}^{do, shed} \\
    & \quad \quad \quad \quad \forall t \in \mathbb{T} \\
    & \\
    &
    (4) \quad  DSM_{t}^{up} \leq E_{t}^{up} \cdot E_{up, max} \\
    & \quad \quad \quad \quad \forall t \in \mathbb{T} \\
    & \\
    &
    (5) \quad DSM_{t}^{do, shift} + DSM_{t}^{do, shed}
    \leq  E_{t}^{do} \cdot E_{do, max} \\
    & \quad \quad \quad \quad \forall t \in \mathbb{T} \\
    & \\
    &
    (6) \quad  \sum_{t=t_s}^{t_s+\tau} DSM_{t}^{up} \cdot \eta =
    \sum_{t=t_s}^{t_s+\tau} DSM_{t}^{do, shift} \\
    & \quad \quad \quad \quad \forall t_s \in \{k \in \mathbb{T}
    \mid k \mod \tau = 0\} \\

* Objective function term:

.. math::
    &
    (DSM_{t}^{up} \cdot cost_{t}^{dsm, up}
    + DSM_{t}^{do, shift} \cdot cost_{t}^{dsm, do, shift}
    + DSM_{t}^{do, shed} \cdot cost_{t}^{dsm, do, shed})
    \cdot \omega_{t} \\
    & \quad \quad \quad \quad \forall t \in \mathbb{T} \\

**approach `DIW`**:

* Constraints:

.. math::
    &
    (1) \quad DSM_{t}^{up} = 0 \\
    & \quad \quad \quad \quad \forall t \in \mathbb{T}
    \quad \textrm{if} \quad e_{shift} = \textrm{False} \\
    & \\
    &
    (2) \quad DSM_{t}^{do, shed} = 0 \\
    & \quad \quad \quad \quad \forall t \in \mathbb{T}
    \quad \textrm{if} \quad e_{shed} = \textrm{False} \\
    & \\
    &
    (3) \quad \dot{E}_{t} = demand_{t} \cdot demand_{max} + DSM_{t}^{up} -
    \sum_{tt=t-L}^{t+L} DSM_{tt,t}^{do, shift} - DSM_{t}^{do, shed} \\
    & \quad \quad \quad \quad \forall t \in \mathbb{T} \\
    & \\
    &
    (4) \quad DSM_{t}^{up} \cdot \eta =
    \sum_{tt=t-L}^{t+L} DSM_{t,tt}^{do, shift} \\
    & \quad \quad \quad \quad \forall t \in \mathbb{T} \\
    & \\
    &
    (5) \quad DSM_{t}^{up} \leq E_{t}^{up} \cdot E_{up, max} \\
    & \quad \quad \quad \quad \forall t \in \mathbb{T} \\
    & \\
    &
    (6) \quad \sum_{t=tt-L}^{tt+L} DSM_{t,tt}^{do, shift}
    + DSM_{tt}^{do, shed} \leq E_{tt}^{do} \cdot E_{do, max} \\
    & \quad \quad \quad \quad \forall tt \in \mathbb{T} \\
    & \\
    &
    (7) \quad DSM_{tt}^{up} + \sum_{t=tt-L}^{tt+L} DSM_{t,tt}^{do, shift}
    + DSM_{tt}^{do, shed} \leq
    max \{ E_{tt}^{up} \cdot E_{up, max},
    E_{tt}^{do} \cdot E_{do, max} \} \\
    & \quad \quad \quad \quad \forall tt \in \mathbb{T} \\
    & \\
    &
    (8) \quad \sum_{tt=t}^{t+R_{shi}-1} DSM_{tt}^{up}
    \leq E_{t}^{up} \cdot E_{up, max} \cdot L \cdot \Delta t \\
    & \quad \quad \quad \quad \forall t \in \mathbb{T} \\
    & \\
    &
    (9) \quad \sum_{tt=t}^{t+R_{she}-1} DSM_{tt}^{do, shed}
    \leq E_{t}^{do} \cdot E_{do, max} \cdot t_{shed} \cdot \Delta t \\
    & \quad \quad \quad \quad \forall t \in \mathbb{T} \\

* Objective function term:

.. math::
    &
    (DSM_{t}^{up} \cdot cost_{t}^{dsm, up}
    + \sum_{tt=0}^{T} DSM_{t, tt}^{do, shift} \cdot
    cost_{t}^{dsm, do, shift}
    + DSM_{t}^{do, shed} \cdot cost_{t}^{dsm, do, shed})
    \cdot \omega_{t} \\
    & \quad \quad \quad \quad \forall t \in \mathbb{T} \\

**approach `DLR`**:

* Constraints:

.. math::
    &
    (1) \quad DSM_{h, t}^{up} = 0 \\
    & \quad \quad \quad \quad \forall h \in H_{DR}, t \in \mathbb{T}
    \quad \textrm{if} \quad e_{shift} = \textrm{False} \\
    & \\
    &
    (2) \quad DSM_{t}^{do, shed} = 0 \\
    & \quad \quad \quad \quad \forall t \in \mathbb{T}
    \quad \textrm{if} \quad e_{shed} = \textrm{False} \\
    & \\
    &
    (3) \quad \dot{E}_{t} = demand_{t} \cdot demand_{max} \\
    & \quad \quad \quad \quad + \displaystyle\sum_{h=1}^{H_{DR}}
    (DSM_{h, t}^{up}
    + DSM_{h, t}^{balanceDo} - DSM_{h, t}^{do, shift}
    - DSM_{h, t}^{balanceUp}) - DSM_{t}^{do, shed} \\
    & \quad \quad \quad \quad \forall t \in \mathbb{T} \\
    & \\
    &
    (4) \quad DSM_{h, t}^{balanceDo} =
    \frac{DSM_{h, t - h}^{do, shift}}{\eta} \\
    & \quad \quad \quad \quad \forall h \in H_{DR}, t \in [h..T] \\
    & \\
    &
    (5) \quad DSM_{h, t}^{balanceUp} =
    DSM_{h, t-h}^{up} \cdot \eta \\
    & \quad \quad \quad \quad \forall h \in H_{DR}, t \in [h..T] \\
    & \\
    &
    (6) \quad DSM_{h, t}^{do, shift} = 0
    \quad \forall h \in H_{DR} \\
    & \quad \quad \quad \quad \forall t \in [T - h..T] \\
    & \\
    &
    (7) \quad DSM_{h, t}^{up} = 0
    \quad \forall h \in H_{DR}  \\
    & \quad \quad \quad \quad \forall t \in [T - h..T] \\
    & \\
    &
    (8) \quad \displaystyle\sum_{h=1}^{H_{DR}} (DSM_{h, t}^{do, shift}
    + DSM_{h, t}^{balanceUp}) + DSM_{t}^{do, shed}
    \leq E_{t}^{do} \cdot E_{max, do} \\
    & \quad \quad \quad \quad \forall t \in \mathbb{T} \\
    & \\
    &
    (9) \quad \displaystyle\sum_{h=1}^{H_{DR}} (DSM_{h, t}^{up}
    + DSM_{h, t}^{balanceDo})
    \leq E_{t}^{up} \cdot E_{max, up} \\
    & \quad \quad \quad \quad \forall t \in \mathbb{T} \\
    & \\
    &
    (10) \quad \Delta t \cdot \displaystyle\sum_{h=1}^{H_{DR}}
    (DSM_{h, t}^{do, shift} - DSM_{h, t}^{balanceDo} \cdot \eta)
    = W_{t}^{levelDo} - W_{t-1}^{levelDo} \\
    & \quad \quad \quad \quad  \forall t \in [1..T] \\
    & \\
    &
    (11) \quad \Delta t \cdot \displaystyle\sum_{h=1}^{H_{DR}}
    (DSM_{h, t}^{up} \cdot \eta - DSM_{h, t}^{balanceUp})
    = W_{t}^{levelUp} - W_{t-1}^{levelUp} \\
    & \quad \quad \quad \quad  \forall t \in [1..T] \\
    & \\
    &
    (12) \quad W_{t}^{levelDo} \leq \overline{E}_{t}^{do}
    \cdot E_{max, do} \cdot t_{shift} \\
    & \quad \quad \quad \quad \forall t \in \mathbb{T} \\
    & \\
    &
    (13) \quad W_{t}^{levelUp} \leq \overline{E}_{t}^{up}
    \cdot E_{max, up} \cdot t_{shift} \\
    & \quad \quad \quad \quad \forall t \in \mathbb{T} \\
    & \\
    &
    (14) \quad \displaystyle\sum_{t=0}^{T} DSM_{t}^{do, shed}
    \leq E_{max, do} \cdot \overline{E}_{t}^{do} \cdot t_{shed}
    \cdot n^{yearLimitShed} \\
    & \\
    &
    (15) \quad \displaystyle\sum_{t=0}^{T} \sum_{h=1}^{H_{DR}}
    DSM_{h, t}^{do, shift}
    \leq E_{max, do} \cdot \overline{E}_{t}^{do} \cdot t_{shift}
    \cdot n^{yearLimitShift} \\
    & \quad \quad \textrm{(optional constraint)} \\
    & \\
    &
    (16) \quad \displaystyle\sum_{t=0}^{T} \sum_{h=1}^{H_{DR}}
    DSM_{h, t}^{up}
    \leq E_{max, up} \cdot \overline{E}_{t}^{up} \cdot t_{shift}
    \cdot n^{yearLimitShift} \\
    & \quad \quad \textrm{(optional constraint)} \\
    & \\
    &
    (17) \quad \displaystyle\sum_{h=1}^{H_{DR}} DSM_{h, t}^{do, shift}
    \leq E_{max, do} \cdot \overline{E}_{t}^{do}
    \cdot t_{shift} -
    \displaystyle\sum_{t'=1}^{t_{dayLimit}} \sum_{h=1}^{H_{DR}}
    DSM_{h, t - t'}^{do, shift} \\
    & \quad \quad \quad \quad \forall t \in [t-t_{dayLimit}..T] \\
    & \quad \quad \textrm{(optional constraint)} \\
    & \\
    &
    (18) \quad \displaystyle\sum_{h=1}^{H_{DR}} DSM_{h, t}^{up}
    \leq E_{max, up} \cdot \overline{E}_{t}^{up}
    \cdot t_{shift} -
    \displaystyle\sum_{t'=1}^{t_{dayLimit}} \sum_{h=1}^{H_{DR}}
    DSM_{h, t - t'}^{up} \\
    & \quad \quad \quad \quad \forall t \in [t-t_{dayLimit}..T] \\
    & \quad \quad \textrm{(optional constraint)}  \\
    & \\
    &
    (19) \quad \displaystyle\sum_{h=1}^{H_{DR}} (DSM_{h, t}^{up}
    + DSM_{h, t}^{balanceDo}
    + DSM_{h, t}^{do, shift} + DSM_{h, t}^{balanceUp})
    + DSM_{t}^{do, shed} \\
    & \quad \quad \leq \max \{E_{t}^{up} \cdot E_{max, up},
    E_{t}^{do} \cdot E_{max, do} \} \\
    & \quad \quad \quad \quad \forall t \in \mathbb{T} \\
    & \quad \quad \textrm{(optional constraint)}  \\

* Objective function term:

.. math::
    &
    (\sum_{h=1}^{H_{DR}} (DSM_{h, t}^{up} + DSM_{h, t}^{balanceDo})
    \cdot cost_{t}^{dsm, up} \\
    & + \sum_{h=1}^{H_{DR}} (DSM_{h, t}^{do, shift}
    + DSM_{h, t}^{balanceUp})
    \cdot cost_{t}^{dsm, do, shift} \\
    & + DSM_{t}^{do, shed} \cdot cost_{t}^{dsm, do, shed})
    \cdot \omega_{t} \\
    & \quad \quad \quad \quad \forall t \in \mathbb{T} \\

References
++++++++++
Gils, Hans Christian (2015): `Balancing of Intermittent Renewable Power Generation by Demand Response and Thermal Energy Storage`, Stuttgart,
`http://dx.doi.org/10.18419/opus-6888 <http://dx.doi.org/10.18419/opus-6888>`_, accessed 24.09.2021, pp. 67-70.

Kochems, Johannes (2020): Demand response potentials for Germany: potential clustering and comparison of modeling approaches, presentation at the 9th international Ruhr Energy Conference (INREC 2020), 10th September 2020,
`https://github.com/jokochems/DR_modeling_oemof/blob/master/Kochems_Demand_Response_INREC.pdf <https://github.com/jokochems/DR_modeling_oemof/blob/master/Kochems_Demand_Response_INREC.pdf>`_, accessed 24.09.2021.

Zerrahn, Alexander and Schill, Wolf-Peter (2015): On the representation of demand-side management in power system models,
in: Energy (84), pp. 840-845, `10.1016/j.energy.2015.03.037 <https://doi.org/10.1016/j.energy.2015.03.037>`_,