import numpy as np
import pandas as pd
from skopt import gp_minimize
import matplotlib.pyplot as plt

def load_csv(file_path):
    """Utility function to simplify loading CSV files."""
    return pd.read_csv(file_path)

# Load data
solar_file_path = 'solar irradiation.xlsx'
demand_file_path = 'demand_data.csv'
wind_profile_file = 'Hourly_Wind_Profile_and_Turbine_Output.csv'

solar_data = pd.read_excel(solar_file_path, sheet_name='POWER_Point_Hourly_20200101_202')
demand_data = load_csv(demand_file_path)
wind_data = load_csv(wind_profile_file)

irradiation = solar_data['ALLSKY_SFC_SW_DWN(Wh/m^2)'].values
demand = demand_data['demand'].values
wind_speed = wind_data['Adjusted_WS140M'].values  
wind_power = wind_data['Turbine Output (KW)'].values  

# Ensure All Data Has 8760 Rows
def ensure_8760(data):
    if len(data) > 8760:
        return data[:8760]
    elif len(data) < 8760:
        return np.pad(data, (0, 8760 - len(data)), 'edge')
    return data

irradiation = ensure_8760(irradiation)
wind_speed = ensure_8760(wind_speed)
wind_power = ensure_8760(wind_power)
hourly_demand = ensure_8760(demand)

# Constants and Data
total_population = 2_938_200  # Brighton population
investment_per_capita = 3000  # €/person
total_investment = total_population * investment_per_capita

# Costs
cost_wind = 6.5e6  # Cost per wind turbine (€, 5MW)
cost_panels = 600  # Cost per solar panel (550W)
cost_smr = 250e6  # Cost per nuclear SMR (50 MW)
cost_storage_kwh = 100  # Cost per kWh of storage

# Other Parameters
area = 3832.2  # Area of Brighton (km^2)
hydro_power_per_km2 = 20  # kW/km^2
storage_efficiency = 0.85  # Roundtrip efficiency
storage_dispatch_time = 6  # Hours for full discharge
initial_storage_fraction = 0.5  # Initial storage at 50%
hydro_capacity = area * hydro_power_per_km2  # Total hydro capacity (kW)

def calc_energy_production(Nmills, Npanels, NSMR):
    """
    Calculate hourly energy production for wind, solar, nuclear, and hydro.
    """
    wind_production = Nmills * wind_power  
    solar_irradiance = irradiation / 1000  
    solar_production = Npanels * solar_irradiance * 0.55 * 2.8 * 0.197  

    nuclear_production = NSMR * 50 * 1000  
    hydro_production = np.full(8760, hydro_capacity)  

    return wind_production, solar_production, nuclear_production, hydro_production

def calc_all(Nmills, Npanels, NSMR):
    """
    Calculate gas consumption and track storage capacity over time.
    """
    storage_kwh = total_investment - (Nmills * cost_wind + Npanels * cost_panels + NSMR * cost_smr)
    
    if storage_kwh > 0:
        storage = storage_kwh * initial_storage_fraction
        wind, solar, nuclear, hydro = calc_energy_production(Nmills, Npanels, NSMR)
        total_production = wind + solar + nuclear + hydro
        gas_consumption = 0
        storage_values = []  

        for h in range(8760):  
            surplus = total_production[h] - hourly_demand[h]
            if surplus > 0:  
                storage = min(storage + surplus * storage_efficiency, storage_kwh)
            else:
                deficit = -surplus
                if storage >= deficit:
                    storage -= deficit
                else:
                    gas_consumption += (deficit - storage)
                    storage = 0
            
            storage_values.append(storage)  

        return gas_consumption, storage_values, total_production
    else:
        return 1e30, [], []

# Optimization Function
def optimization_function(params):
    Nmills, Npanels, NSMR = params
    return calc_all(Nmills, Npanels, NSMR)[0]  

# Bounds for Optimization
bounds = [
    (0, total_investment // cost_wind),
    (0, total_investment // cost_panels),
    (0, total_investment // cost_smr),
]

# Perform Optimization
result = gp_minimize(optimization_function, bounds, n_calls=50, random_state=42)

# Extract Optimal Configuration
Nmills, Npanels, NSMR = result.x
gas_consumption, storage_values, total_production = calc_all(Nmills, Npanels, NSMR)

# Compute Total Investment Breakdown
investment_wind = Nmills * cost_wind
investment_solar = Npanels * cost_panels
investment_nuclear = NSMR * cost_smr
investment_storage = total_investment - (investment_wind + investment_solar + investment_nuclear)

# Compute Total Demand and Generation
total_demand = np.sum(hourly_demand)
total_generation = np.sum(total_production)

# Print Results
print("\n--- Optimal Configuration ---")
print(f"Wind Turbines: {Nmills:.0f}")
print(f"Solar Panels: {Npanels:.0f}")
print(f"Nuclear SMRs: {NSMR:.0f}")

print("\n--- Investment Breakdown (€) ---")
print(f"Total Investment: {total_investment:.2f} €")
print(f"Investment in Wind: {investment_wind:.2f} €")
print(f"Investment in Solar: {investment_solar:.2f} €")
print(f"Investment in Nuclear: {investment_nuclear:.2f} €")
print(f"Investment in Storage: {investment_storage:.2f} €")

print("\n--- Energy Statistics ---")
print(f"Total Demand: {total_demand:.2f} kWh")
print(f"Total Generation: {total_generation:.2f} kWh")
print(f"Gas Consumption: {gas_consumption:.2f} kWh")
print(f"Final Storage Capacity: {storage_values[-1]:.2f} kWh")

# Visualization: Storage Capacity Over Time
def plot_storage(storage_values):
    """
    Plots the storage capacity over time.
    """
    plt.figure(figsize=(12, 6))
    plt.plot(storage_values, label="Storage Capacity (kWh)", color='purple')
    plt.xlabel("Hours")
    plt.ylabel("Stored Energy (kWh)")
    plt.title("Energy Storage Capacity Over Time")
    plt.legend()
    plt.show()

# Call function to visualize storage over time
plot_storage(storage_values)
