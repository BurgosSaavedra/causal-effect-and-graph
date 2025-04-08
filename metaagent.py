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
import dowhy
from dowhy import CausalModel
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

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

    ## Read only the test dataset
    df = pd.DataFrame(data)

    # Create causal graph
    G = nx.DiGraph()

    # Define edges with logical grouping
    edges = [
        # Air intake system
        ('operating_altitude', 'air_filter_pressure'),
        ('air_filter_pressure', 'egt_turbo_inlet'),
        ('air_filter_pressure', 'fuel_consumption'),
        
        # Primary mechanical relationships
        ('payload_weight', 'engine_load'),
        ('haul_road_gradient', 'engine_load'),
        ('engine_load', 'engine_rpm'),
        ('engine_load', 'fuel_consumption'),
        ('engine_rpm', 'vehicle_speed'),
        ('engine_rpm', 'air_filter_pressure'),
        
        # Environmental influences
        ('operating_altitude', 'engine_load'),
        ('ambient_temp', 'engine_coolant_temp'),
        ('ambient_temp', 'egt_turbo_inlet'),
        
        # Fuel and combustion chain
        ('fuel_consumption', 'egt_turbo_inlet'),
        ('engine_load', 'egt_turbo_inlet'),
        
        # Temperature cascade through exhaust system
        ('egt_turbo_inlet', 'egt_turbo_outlet'),
        ('egt_turbo_outlet', 'egt_stack'),
        
        # Cooling system relationships
        ('engine_coolant_temp', 'egt_turbo_inlet'),
        ('engine_rpm', 'engine_coolant_temp')
    ]

    # Add edges to graph
    G.add_edges_from(edges)

    def analyze_causal_effect(df, G, treatment, outcome):
        try:
            model = CausalModel(
                data=df,
                graph=G,
                treatment=treatment,
                outcome=outcome
            )
            
            identified_estimand = model.identify_effect(proceed_when_unidentifiable=True)
            estimate = model.estimate_effect(
                identified_estimand,
                method_name="backdoor.linear_regression",
                control_value=0,
                treatment_value=1
            )
            
            return float(estimate.value)
        except:
            return np.nan

    # Analyze causal relationships
    treatments = ['air_filter_pressure', 'engine_coolant_temp', 'engine_load', 
                'ambient_temp', 'engine_rpm', 'fuel_consumption']
    outcomes = ['egt_turbo_inlet', 'egt_turbo_outlet', 'egt_stack']

    print("\nCausal Effect Analysis:")
    print("=====================")

    # Create a dictionary to store valid causal effects
    causal_effects = {}
    effect_data = []

    for treatment in treatments:
        for outcome in outcomes:
            if treatment != outcome:
                effect = analyze_causal_effect(df, G, treatment, outcome)
                print(f"Effect: {effect}")
                if not np.isnan(effect):
                    causal_effects[(treatment, outcome)] = effect
                    effect_data.append({
                        'Treatment': treatment,
                        'Outcome': outcome,
                        'Effect': effect
                    })
                    print(f"\n{treatment.replace('_', ' ').title()} → {outcome.replace('_', ' ').title()}:")
                    print(f"Causal Effect: {effect:.3f}")
    print("End of the game") #
    return {}

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
