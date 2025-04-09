"""
Default script template for the Python Meta Action Agent.

When importing packages, follow the format below to add a comment at the end of declaration 
and specify a version or a package name when the import name is different from expected python package.
This allows the agent to install the correct package version during configuration:
e.g. import paho.mqtt as np  # version=2.1.0 package=paho-mqtt

This script provides a structure for implementing on_create, on_receive, and on_destroy functions.
It includes a basic example using 'foo' and 'bar' concepts to demonstrate functionality.
Each function should return a dictionary object with result data, or None if no result is needed.
"""

# Install Libraries
import networkx as nx 
from dowhy.utils import plot, bar_plot
import pandas as pd
from dowhy import gcm
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use a non-interactive backend (useful for script execution)
import matplotlib.pyplot as plt

# Global variable to store the 'foo' and 'bar' values
foo_value = None
bar_value = None

def on_create(data: dict) -> dict | None:
    """
    Initialize the script with provided data.

    Args:
        data (dict): Initialization data containing 'foo' value.

    Returns:
        dict | None: Configuration dictionary with initialized 'foo' value.
    """
    global foo_value
    foo_value = data.get("foo", 0)
    return {
        "initialized_foo": foo_value
    }

def on_receive(data: dict) -> dict:
    """
    Process received event data, concatenating 'foo' and 'bar' to create 'foo_bar'.

    Args:
        data (dict): Received event data containing new 'bar' value.
        or data (list[dict]): Received event data when Proces as Batch is ticked
    Returns:
        dict or list[dict]: Result of processing the event data, including a 'foo_bar' value.
    """

    """Functions"""

    def convert_to_percentage(value_dictionary):
        """
        Convert attribution values to percentage values.
        
        This function calculates the percentage contribution of each value
        in the dictionary based on the absolute sum of all the dictionary values.
        
        Args:
            value_dictionary (dict): Dictionary with attribution values.
            
        Returns:
            dict: A dictionary with the same keys and their respective percentage values.
        
        Note:
            The conversion to percentages only makes sense for purely positive attributions.
        """
        total_absolute_sum = np.sum([abs(v) for v in value_dictionary.values()])
        return {k: abs(v) / total_absolute_sum * 100 for k, v in value_dictionary.items()}


    def get_readable_percentages_arrow(percentage_dict):
        """
        Format the arrow strength percentages for printing.
        
        Args:
            percentage_dict (dict): Dictionary where keys are tuples (source, target) 
                                    and values are percentage strengths.
        
        Returns:
            str: A formatted string representing each arrow and its corresponding percentage.
        """
        result = ""
        for (source, target), value in percentage_dict.items():
            # Format the float to 2 decimal places
            formatted_value = round(float(value), 2)
            result += f"{source} -> {target} = {formatted_value}%\n"
        return result


    def get_readable_percentages_iccs(percentage_dict):
        """
        Format the intrinsic causal influence (ICCs) percentages for printing.
        
        Args:
            percentage_dict (dict): Dictionary where keys are variable names and 
                                    values are percentage contributions.
        
        Returns:
            str: A formatted string showing each variable's contribution percentage.
        """
        result = ""
        for key, value in percentage_dict.items():
            # Format the float to 2 decimal places
            formatted_value = round(float(value), 2)
            result += f"{key} = {formatted_value}%\n"
        return result


    """Main Code"""    
    """
    Main function that:
    1. Reads the input data.
    2. Defines the causal model.
    3. Assigns generative models to the nodes.
    4. Fits the causal model to data.
    5. Computes and plots the causal graph and variance attribution.
    6. Returns a summary dictionary with readable results.
    
    Returns:
        dict: A dictionary with a key 'summary' containing the model results as a string.
    """
    
    ## Read only the test dataset
    df = pd.DataFrame(data)

    # --- Step 1: Define Causal Model ---
    # Create a directed graph representing the causal relationships
    causal_graph = nx.DiGraph(
        [
            # Air intake system relationships
            ('altitude', 'air_filter_pressure'),
            ('air_filter_pressure', 'egt_turbo_inlet'),
            ('air_filter_pressure', 'fuel_consumption'),
            
            # Primary mechanical relationships
            ('engine_load', 'engine_rpm'),
            ('engine_load', 'fuel_consumption'),
            ('engine_rpm', 'air_filter_pressure'),
            
            # Environmental influences
            ('altitude', 'engine_load'),
            ('ambient_temp', 'coolant_temp'),
            ('ambient_temp', 'egt_turbo_inlet'),
            
            # Fuel and combustion chain
            ('fuel_consumption', 'egt_turbo_inlet'),
            ('engine_load', 'egt_turbo_inlet'),
            
            # Cooling system relationships
            ('coolant_temp', 'egt_turbo_inlet'),
            ('engine_rpm', 'coolant_temp')
        ]
    )

    # Define the treatment and outcome variables.
    treatments = ['altitude', 
                  'ambient_temp', 
                  'engine_load', 
                  'engine_rpm', 
                  'air_filter_pressure', 
                  'coolant_temp', 
                  'fuel_consumption']
    outcomes = ['egt_turbo_inlet']

    # Create the structural causal model object using the defined causal graph.
    scm = gcm.StructuralCausalModel(causal_graph)

    # Automatically assign generative models (causal mechanisms) to each node based on the dataset.
    auto_assignment_summary = gcm.auto.assign_causal_mechanisms(scm, df)
    
    # --- Step 2: Fit Causal Models to Data ---
    # Fit the specified causal model to the dataset.
    gcm.fit(scm, df)

    # --- Step 3: Answer Causal Question ---

    # (A) Plotting the Causal Graph with Arrow Strength Percentages
    arrow_strengths = gcm.arrow_strength(
        scm, 
        target_node='egt_turbo_inlet'
    )

    plot(causal_graph,
         causal_strengths=convert_to_percentage(arrow_strengths),
         figure_size=[15, 10])
    
    # Retrieve and save the current figure as a PNG file.
    fig = plt.gcf()
    fig.savefig("causal_graph.png", format='png', dpi=300, bbox_inches='tight')
    plt.close(fig)

    # (B) Computing and Plotting Intrinsic Causal Influence (ICCs)
    iccs = gcm.intrinsic_causal_influence(
        scm,
        target_node='egt_turbo_inlet',
        num_samples_randomization=500
    )
    
    # Create a bar plot for the ICCs using percentage values.
    bar_plot(convert_to_percentage(iccs), ylabel='Variance attribution in %')
    
    # Retrieve and save the bar plot as a PNG file.
    fig = plt.gcf()
    fig.savefig("variance_attribution.png", format='png', dpi=300, bbox_inches='tight')
    plt.close(fig)

    # Create a summary string containing the results
    summary = f"""
    This is the result using dowhy.gcm on the data:

    - Treatments: {treatments}
    - Outcomes: {outcomes}

    Arrow Strengths:
    ----------------
    {get_readable_percentages_arrow(convert_to_percentage(arrow_strengths))}

    ICCs:
    -----
    {get_readable_percentages_iccs(convert_to_percentage(iccs))}
    """
    
    return {'summary': summary}

def on_destroy() -> dict | None:
    """
    Clean up resources when the script is being destroyed.

    Returns:
        dict | None: Final values of 'foo' and 'bar'.
    """
    global foo_value, bar_value
    return {
        "final_foo": foo_value,
        "final_bar": bar_value
    }
