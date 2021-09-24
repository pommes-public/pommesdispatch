
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
    ":math:`P_{i}(n, t)`", "variable", "inflow into transformer n at time step t"
    ":math:`P_{o}(n, t)`", "variable", "outflow from transformer n at time step t"
    ":math:`E(s, t)`", "variable", "energy currently stored in storage s"
    ":math:`c_{var}(i, o, t)`", "parameter", "variable costs for flow from input i to output o at time step t"
    ":math:`\tau(t)`", "parameter", "time increment of the model for time step t"
    ":math:`eta_{o}(n, t)`", "parameter", "conversion efficiency for outflow"
    ":math:`eta_{i}(n, t)`", "parameter", "conversion efficiency for inflow"
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
    ":math:`ef(i, o)`"


Target function
+++++++++++++++
The target function is build together by the ``_objective_expression`` terms of all
oemof.solph components used (
`see the oemof.solph.models module <https://github.com/oemof/oemof-solph/blob/dev/src/oemof/solph/models.py>`_):


Variable costs for all flows (commodity / fuel, emissions and operation costs):

.. math::

    & \sum_{(i,o)} \sum_t f(i, o, t) \cdot \c_{var}(i, o, t) \\
    & \forall \space i \in I(n), \space o \in O(n),
    \space n \in \mathrm{B}, \space t \in \mathrm{T}


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

* energy transformation:

.. math::
    & \P_{i}(n, t) \times \eta_{o}(n, t) =
    \P_{o}(n, t) \times \eta_{i}(n, t), \\
    & \forall \space t \in \mathrm{T}, \space n \in \mathrm{TF},
    \space i \in \mathrm{I(n)}, \space o \in \mathrm{O(n)}

with :math:`P_{i}(n, t)` as the inflow into the transformer node n,
:math:`P_{o}(n, t)` as the transformer outflow, :math:`eta_{o}(n, t)` the
conversion efficiency for outputs and :math:`eta_{i}(n, t)` the conversion
factors for inflows. We only use the conversion factor for outflows to account
for losses from the conversion (within the power plant).
:math:`mathrm{TF}` is the set of transformers, i.e. any kind of energy conversion
unit. We use this for conventional generators, renewable energy sources (RES)
within the market premium scheme in Germany (with 100% efficiency -
used just to steer the price-based output in times RES are price setting)
as well as interconnection line losses.

* gradient limits for generators

.. math::

    & f(i, o, t) - f(i, o, t-1) \leq \Delta \P_{pos}(i, o, t) \\
    & \forall \space (i, o) \in \mathrm{PGF},
    \space t \in \mathrm{T} \\
    & \\
    & f(i, o, t-1) - f(i, o, t) \leq \Delta \P_{neg}(i, o, t) \\
    & \forall \space (i, o) \in \mathrm{NGF},
    \space t \in \mathrm{T}

with :math:`\Delta P_{pos}(i, o, t)` equalling to the maximum allowed positive
an :math:`\Delta P_{neg}(i, o, t)` equalling to the maximum allowed negative
gradient and :math:`\mathrm{PGF}` resp. :math:`\mathrm{NGF}` being the set
of flows with positive or negative gradient limits (i.e. conventional
generators).

* minimum and maximum load requirements

.. math::

    & f(i, o, t) \geq \f_{min}(i, o, t) \cdot \P_{nom}(i, o) \\
    & \forall \space (i, o) \in \mathrm{F},
    \space t \in \mathrm{T} \\
    & \\
    & f(i, o, t) \leq \f_{max}(i, o, t) \cdot \P_{nom}(i, o) \\
    & \forall \space (i, o) \in \mathrm{F},
    \space t \in \mathrm{T}

with :math:`P_{nom}(i, o)` equalling to the installed resp. maximum capacity,
:math:`f_{min}(i, o, t)` as the normalized minimum flow value
and :math:`f_{max}(i, o, t)` as the normalized maximum flow value.

.. note::

    Whereas the maximum value is fixed and set to 1 for all units and time steps,
    the minimum value of some generator types may alter over time.
    This is especially true for combined heat an power (CHP) plants and
    and industrial power plants (IPP), where a minimum load pattern
    is fed in in order to serve the heating or process steam demand.

* storages

    * Storage roundtrip:

    .. math::

        E(s, |\mathrm{T}|) = E(s, -1)

with the last storage level :math:`E(s, |\mathrm{T}|)` equalling the
initial storage content :math:`E(s, -1)`.

    * Storage balance:

    .. math::

        & E(s, t) = E(s, t-1) \cdot (1 - \beta(s, t)) ^{\tau(t)/(t_u)} \\
        & - \gamma(s, t)\cdot \E_{nom}(s) \cdot {\tau(t)/(t_u)}
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

        & \E_{min}(s, t) \leq E(s, t) \leq \E_{max}(s, t) \\
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

    \sum_{(i,o)} \sum_t f(i, o, t) \cdot \tau(t) \cdot emission\_factor(i, o) \leq emission\_limit


Demand response constraints
===========================

The constraints used are taken from Zerrahn and Schill (2015, pp. 842-843), Gils (2015, pp. 67-70), Steurer (2017, pp. 80-82) and Ladwig (2018, pp. 90-93) respectively.
*See page [Modelling of demand response](modelling-of-demand-response) for details.*

## Power price calculation
In the LP dispatch model, the German day ahead power price is calculated. For this purpose, the **dual values of the bus balance constraint of the German electricity bus** are evaluated. These due to the underlying merit order rationale can be evaluated as the marginal costs of the last power plant producing.

# Bibliography
Gils, Hans Christian (2015): Balancing of Intermittent Renewable Power Generation by Demand Response and Thermal Energy Storage. Dissertation. Universität Stuttgart, Stuttgart.

Ladwig, Theresa (2018): Demand Side Management in Deutschland zur Systemintegration erneuerbarer Energien. Dissertation. Technische Universität Dresden, Dresden.

oemof (2019a): oemof documentation, oemof-solph, https://oemof.readthedocs.io/en/stable/oemof_solph.html, last accessed 04.01.2019.

oemof (2019b): oemof API, oemof.solph package, https://oemof.readthedocs.io/en/stable/api/oemof.solph.html, last accessed 04.01.2019.

Steurer, Martin (2017): Analyse von Demand Side Integration im Hinblick auf eine effiziente und umweltfreundliche Energieversorgung. Dissertation. Universität Stuttgart, Stuttgart. Institut für Energiewirtschaft und Rationelle Energieanwendung (IER).

Zerrahn, Alexander; Schill, Wolf-Peter (2015): On the representation of demand-side man-agement in power system models. In: Energy 84, S. 840–845. DOI: 10.1016/j.energy.2015.03.037.