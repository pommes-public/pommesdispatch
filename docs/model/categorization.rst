.. _characteristics:

Model categorization
--------------------
The model in brief can be characterized as a **bottom-up electricity market optimization model**.
In the following, a model characterization based on Hall and Buckley (2016) is introduced:

Model purpose and structure
+++++++++++++++++++++++++++

.. csv-table::
    :widths: 30 70
    :header: "**criterion**", "**manifestation**"

    "Purpose of the model", "| General: scenario analyses (forecasting)
    | Specific: power supply and power prices"
    "Structure of the model", "| Demand: exogenously (except for demand response)
    | Supply: RES exogenously; All other power sources endogenously optimized"
    "Geographical coverage", "| National: Federal Republic of Germany + imports / exports from
    | / to adjacent electric neighbors"
    "Sectoral coverage", "| Power market (effectively day-ahead) from a macroeconomic point of view
    | (no bidding simulation)"
    "Time horizon", "Short-term (<= 1 year)"
    "Time step", "Hourly"

Technological detail
++++++++++++++++++++

.. csv-table::
    :widths: 30 70
    :header: "**criterion**", "**manifestation**"

    "Renewable Techology inclusion", "Hydro (run of river), Solar, Wind, Biomass"
    "Storage Technology Inclusion ", "| Pumped-hydro energy storage, Reservoir energy storage,
    | (Battery energy storage)"
    "Demand Characteristic Inclusion", "| Aggregated demand for Industry, Residential Sector,
    | Commercial Sector and Transportation"
    "Cost Inclusion", "Fuel prices, Operations and Maintenance Costs, CO2-costs"

Mathematical description
++++++++++++++++++++++++

.. csv-table::
    :widths: 30 70
    :header: "**criterion**", "**manifestation**"

    "Analytical Approach", "Bottom-Up (fundamental)"
    "Underlying Methodology", "Optimization / Spreadsheet / Toolbox"
    "Mathematical Approach", "Linear programming"
    "Data Requirements", "Quantitative, Monetary, Disaggregated by technologies and bidding zones"

References
++++++++++
Hall, Lisa M.H.; Buckley, Alastair R. (2016):
A review of energy systems models in the UK. Prevalent usage and categorisation.
In: Applied Energy 169, S. 607–628. DOI:
`10.1016/j.apenergy.2016.02.044 <10.1016/j.apenergy.2016.02.044>`_.