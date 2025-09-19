import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Constants
HOURS_PER_YEAR = 8760
WEEK_HOURS = 168  # 1 week
SEASON_HOURS = [0, 2190, 4380, 6570]  # Approximate season start times

total_population = 2_938_200  # Brighton population
investment_per_capita = 3000  # €/person
total_investment = total_population * investment_per_capita

# Cost Data (in €)  
cost_wind = 6.5e6  # Per wind turbine (5MW)
cost_panels = 600  # Per solar panel (550W)
cost_smr = 250e6  # Per nuclear SMR (50 MW)
cost_storage_kwh = 100  # Per kWh of storage

# Installed Infrastructure
wind_turbines = 625
solar_panels = 4759059
nuclear_smrs = 5

# Energy Production (Constant sources)
nuclear_production = np.full(HOURS_PER_YEAR, 244382.352845001)  # kWh (constant nuclear generation)
hydro_capacity = np.full(HOURS_PER_YEAR, 76644.0)  # kWh (constant hydro generation)

def load_data():
    """Load hourly wind power, solar irradiation, and demand."""
    wind_data = pd.read_csv('Hourly_Wind_Profile_and_Turbine_Output.csv')
    demand_data = pd.read_csv('demand_data.csv')
    solar_data = pd.read_excel('solar irradiation.xlsx', sheet_name='POWER_Point_Hourly_20200101_202')
    
    wind_power = wind_data['Turbine Output (KW)'].values  # Wind turbine output
    irradiation = solar_data['ALLSKY_SFC_SW_DWN(Wh/m^2)'].values / 1000  # Convert to kWh/m²
    hourly_demand = demand_data['demand'].values
    
    return wind_power, irradiation, hourly_demand

def ensure_8760(data):
    """Ensure data has exactly 8760 hourly values."""
    if len(data) > HOURS_PER_YEAR:
        return data[:HOURS_PER_YEAR]
    elif len(data) < HOURS_PER_YEAR:
        return np.pad(data, (0, HOURS_PER_YEAR - len(data)), 'edge')
    return data

def calculate_energy_production(wind_power, irradiation):
    """Compute hourly energy production."""
    wind_energy = np.full(HOURS_PER_YEAR, wind_turbines) * wind_power[:HOURS_PER_YEAR]
    solar_energy = np.full(HOURS_PER_YEAR, solar_panels) * irradiation[:HOURS_PER_YEAR] * 0.55 * 2.8 * 0.197
    nuclear_energy = np.copy(nuclear_production)
    hydro_energy = np.copy(hydro_capacity)
    total_production = wind_energy + solar_energy + nuclear_energy + hydro_energy
    return total_production, wind_energy, solar_energy, nuclear_energy, hydro_energy

def simulate_energy_balance(total_production, hourly_demand):
    """Simulate energy balance, prioritizing storage over gas consumption."""
    storage_capacity = (total_investment - (wind_turbines * cost_wind + solar_panels * cost_panels + nuclear_smrs * cost_smr)) / cost_storage_kwh
    storage = storage_capacity * 0.5
    gas_consumption = np.zeros(HOURS_PER_YEAR)
    storage_values = []
    
    for h in range(HOURS_PER_YEAR):
        surplus = total_production[h] - hourly_demand[h]
        if surplus > 0:
            storage = min(storage + surplus * 0.85, storage_capacity)
        else:
            deficit = -surplus
            if storage >= deficit:
                storage -= deficit
            else:
                remaining_deficit = deficit - storage
                storage = 0
                gas_consumption[h] = max(0, remaining_deficit)
        storage_values.append(storage)
    
    return gas_consumption, storage_values

def plot_results(wind_energy, solar_energy, nuclear_energy, hydro_energy, gas_consumption, storage_values, hourly_demand):
    """Plot seasonal stack plots, storage evolution, and final energy mix."""
    # Seasonal Stack Plots
    for i, season in enumerate(['Winter', 'Spring', 'Summer', 'Fall']):
        start = SEASON_HOURS[i]
        end = start + WEEK_HOURS
        plt.figure(figsize=(10,5))
        plt.stackplot(range(WEEK_HOURS), wind_energy[start:end], solar_energy[start:end], nuclear_energy[start:end], hydro_energy[start:end], gas_consumption[start:end], labels=['Wind', 'Solar', 'Nuclear', 'Hydro', 'Gas'])
        plt.plot(hourly_demand[start:end], color='red', label='Demand', linewidth=1.5)
        plt.xlabel('Hours')
        plt.ylabel('Power Generation (kWh)')
        plt.title(f'Energy Generation Mix - {season}')
        plt.legend()
        plt.show()
    
    # Final Generation Mix Pie Chart
    energy_totals = [np.sum(wind_energy), np.sum(solar_energy), np.sum(nuclear_energy), np.sum(hydro_energy), np.sum(gas_consumption)]
    plt.figure(figsize=(6,6))
    plt.pie(energy_totals, labels=['Wind', 'Solar', 'Nuclear', 'Hydro', 'Gas'], autopct='%1.1f%%')
    plt.title('Final Generation Mix')
    plt.show()
    
    # Storage Evolution (One Week)
    plt.figure(figsize=(10,5))
    plt.plot(storage_values[:WEEK_HOURS], label='Storage Capacity (kWh)')
    plt.xlabel('Hours')
    plt.ylabel('Storage Level (kWh)')
    plt.title('Storage Capacity Evolution (1 week)')
    plt.legend()
    plt.show()

def main():
    """Main function to load data, compute energy production, simulate balance, and generate plots."""
    wind_power, irradiation, hourly_demand = load_data()
    wind_power = ensure_8760(wind_power)
    irradiation = ensure_8760(irradiation)
    hourly_demand = ensure_8760(hourly_demand)
    
    total_production, wind_energy, solar_energy, nuclear_energy, hydro_energy = calculate_energy_production(wind_power, irradiation)
    gas_consumption, storage_values = simulate_energy_balance(total_production, hourly_demand)
    
    plot_results(wind_energy, solar_energy, nuclear_energy, hydro_energy, gas_consumption, storage_values, hourly_demand)

if __name__ == "__main__":
    main()
