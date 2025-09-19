import pandapower as pp
import pandapower.plotting as plot
import matplotlib.pyplot as plt
from pandapower.plotting import simple_plotly
from pandapower.plotting import create_generic_coordinates
import plotly.graph_objects as go

# Step 1: Create an empty power network
net = pp.create_empty_network()

# Step 2: Define buses
bus_nuclear = pp.create_bus(net, vn_kv=220, name="Bus - Nuclear Plant")
bus_solar = pp.create_bus(net, vn_kv=220, name="Bus - Solar Plant")
bus_wind = pp.create_bus(net, vn_kv=220, name="Bus - Wind Plant")
bus_hydro = pp.create_bus(net, vn_kv=220, name="Bus - Hydro Plant")
bus_storage = pp.create_bus(net, vn_kv=220, name="Bus - Storage")
bus_load1 = pp.create_bus(net, vn_kv=220, name="Load Center 1 (Brighton)")
bus_load2 = pp.create_bus(net, vn_kv=220, name="Load Center 2")

# Step 3: Add an external grid (Slack Bus)
pp.create_ext_grid(net, bus=bus_nuclear, vm_pu=1.02, max_p_mw=10000, name="External Grid (Slack)")

# Step 4: Add updated generators    
num_nuclear = 25  # Number of nuclear reactors
num_solar = 4_759_059  # Number of solar panels
num_wind = 625  # Number of wind turbines
hydro_capacity = 76.64  # MW (constant)

nuclear_capacity = num_nuclear * 50  # MW per nuclear reactor
solar_capacity = num_solar * 0.00055  # MW per solar panel
wind_capacity = num_wind * 5  # MW per wind turbine

pp.create_gen(net, bus=bus_nuclear, p_mw=nuclear_capacity, vm_pu=1.02, name="Nuclear Plant")
pp.create_gen(net, bus=bus_solar, p_mw=solar_capacity, vm_pu=1.02, name="Solar Plant")
pp.create_gen(net, bus=bus_wind, p_mw=wind_capacity, vm_pu=1.02, name="Wind Plant")
pp.create_gen(net, bus=bus_hydro, p_mw=hydro_capacity, vm_pu=1.02, name="Run-of-the-River Hydro Plant")

# Step 5: Add loads
total_demand_mw = 1748.60
load1_demand = total_demand_mw * 0.6
load2_demand = total_demand_mw * 0.4

pp.create_load(net, bus=bus_load1, p_mw=load1_demand, q_mvar=250, name="Load Center 1 (Brighton)")
pp.create_load(net, bus=bus_load2, p_mw=load2_demand, q_mvar=150, name="Load Center 2")

# Step 6: Add storage
storage_capacity_kWh = 118034404
storage_capacity_MWh = storage_capacity_kWh * 0.001
storage_power_MW = 100
roundtrip_efficiency = 0.85
initial_soc = 0.5

pp.create_storage(
    net,
    bus=bus_storage,
    p_mw=storage_power_MW,
    max_e_mwh=storage_capacity_MWh,
    soc_percent=initial_soc * 100,
    efficiency=roundtrip_efficiency,
    name="Energy Storage"
)

# Step 7: Define upgraded transmission lines
upgraded_line_data = {"r_ohm_per_km": 0.005, "x_ohm_per_km": 0.01, "c_nf_per_km": 10, "max_i_ka": 3.0}
pp.create_std_type(net, data=upgraded_line_data, name="Upgraded_Line_Type")

# Add lines (including redundancy for Line 1)
pp.create_line(net, from_bus=bus_nuclear, to_bus=bus_load1, length_km=75, std_type="Upgraded_Line_Type", name="Nuclear to Brighton")
pp.create_line(net, from_bus=bus_wind, to_bus=bus_load1, length_km=50, std_type="Upgraded_Line_Type", name="Wind to Brighton")
pp.create_line(net, from_bus=bus_wind, to_bus=bus_load1, length_km=50, std_type="Upgraded_Line_Type", name="Wind to Brighton (Parallel)")
pp.create_line(net, from_bus=bus_solar, to_bus=bus_load1, length_km=30, std_type="Upgraded_Line_Type", name="Solar to Brighton")
pp.create_line(net, from_bus=bus_hydro, to_bus=bus_load1, length_km=150, std_type="Upgraded_Line_Type", name="Hydro to Brighton")
pp.create_line(net, from_bus=bus_storage, to_bus=bus_load1, length_km=20, std_type="Upgraded_Line_Type", name="Storage to Brighton")
pp.create_line(net, from_bus=bus_load1, to_bus=bus_load2, length_km=100, std_type="Upgraded_Line_Type", name="Brighton to Load Center 2")

# Step 8: Add shunt elements for reactive power stabilization
pp.create_shunt(net, bus=bus_solar, q_mvar=50, p_mw=0, name="Solar Shunt")
pp.create_shunt(net, bus=bus_load1, q_mvar=50, p_mw=0, name="Load1 Voltage Regulator")
pp.create_shunt(net, bus=bus_load2, q_mvar=30, p_mw=0, name="Load2 Voltage Regulator")

# Step 9: Run load flow analysis
try:
    pp.runpp(net, max_iteration=50, init="auto", tolerance_mva=1e-5, enforce_q_lims=True, algorithm="nr")
    
    # Display results
    print("=== Bus Voltages (p.u.) ===")
    print(net.res_bus[["vm_pu", "va_degree"]])
    
    print("\n=== Line Loading (%) ===")
    print(net.res_line[["loading_percent"]])
    
    print("\n=== Generator Outputs (MW) ===")
    print(net.res_gen[["p_mw", "q_mvar"]])
    
    print("\n=== Load Data (MW) ===")
    print(net.res_load[["p_mw", "q_mvar"]])
except Exception as e:
    print(f"Error: {e}")
    
create_generic_coordinates(net)

# Step 1: Manually assign coordinates to buses
# (You can adjust these coordinates for a better layout)
net.bus.loc[bus_nuclear, 'x'], net.bus.loc[bus_nuclear, 'y'] = 0, 0
net.bus.loc[bus_solar, 'x'], net.bus.loc[bus_solar, 'y'] = 2, 2
net.bus.loc[bus_wind, 'x'], net.bus.loc[bus_wind, 'y'] = -2, 2
net.bus.loc[bus_hydro, 'x'], net.bus.loc[bus_hydro, 'y'] = -2, -2
net.bus.loc[bus_storage, 'x'], net.bus.loc[bus_storage, 'y'] = 2, -2
net.bus.loc[bus_load1, 'x'], net.bus.loc[bus_load1, 'y'] = 4, 0
net.bus.loc[bus_load2, 'x'], net.bus.loc[bus_load2, 'y'] = 6, 0

# Step 2: Generate base plot
fig = simple_plotly(
    net,
    respect_switches=True,
    line_width=2.0
)

# Step 3: Add line loading annotations
for line_idx, line in net.line.iterrows():
    from_bus = net.bus.loc[line.from_bus]
    to_bus = net.bus.loc[line.to_bus]
    loading = net.res_line.loc[line_idx, "loading_percent"]
    # Calculate midpoint for annotation
    midpoint_x = (from_bus['x'] + to_bus['x']) / 2
    midpoint_y = (from_bus['y'] + to_bus['y']) / 2

    # Add text annotation
    fig.add_trace(go.Scatter(
        x=[midpoint_x],
        y=[midpoint_y],
        text=[f"{loading:.2f}%"],
        mode="text",
        textfont=dict(color="red", size=12),
        showlegend=False
    ))

# Step 4: Customize the layout
fig.update_layout(
    title="Enhanced Network Line Plot",
    xaxis_title="X Coordinate",
    yaxis_title="Y Coordinate",
    legend=dict(
        x=1, y=1,
        bgcolor="rgba(255,255,255,0.5)",
        bordercolor="Black",
        borderwidth=1
    ),
    plot_bgcolor="rgba(240,240,240,1)"
)

# Step 5: Show the plot
fig.show()


# Voltage profile data
buses = ["Nuclear", "Solar", "Wind", "Hydro", "Storage", "Load1", "Load2"]
voltages = [1.02, 1.02, 1.02, 1.02, 1.017, 1.017, 1.006]

# Create the plot
plt.figure(figsize=(10, 6))
plt.bar(buses, voltages, color='blue', alpha=0.7, edgecolor='black')
plt.axhline(y=1.05, color='green', linestyle='--', label='Upper Limit (1.05 p.u.)')
plt.axhline(y=0.95, color='red', linestyle='--', label='Lower Limit (0.95 p.u.)')

# Title and labels
plt.title("Voltage Profile Across Buses", fontsize=14)
plt.xlabel("Buses", fontsize=12)
plt.ylabel("Voltage (p.u.)", fontsize=12)
plt.ylim(0.9, 1.1)
plt.legend()
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()

# Save the plot
plt.savefig("voltage_profile.png")
plt.show()

# Line loading data
lines = [
    "Nuclear-Brighton",
    "Wind-Brighton",
    "Wind-Brighton (Parallel)",
    "Solar-Brighton",
    "Hydro-Brighton",
    "Storage-Brighton",
    "Brighton-Load2",
]
loadings = [68.45, 74.38, 74.38, 60.35, 9.08, 8.61, 62.80]

# Create the plot
plt.figure(figsize=(10, 6))
plt.barh(lines, loadings, color='orange', alpha=0.7, edgecolor='black')
plt.axvline(x=100, color='red', linestyle='--', label='Capacity Limit (100%)')

# Title and labels
plt.title("Line Loading Percentages", fontsize=14)
plt.xlabel("Loading (%)", fontsize=12)
plt.ylabel("Transmission Lines", fontsize=12)
plt.legend()
plt.grid(axis='x', linestyle='--', alpha=0.7)
plt.tight_layout()

# Save the plot
plt.savefig("line_loading.png")
plt.show()
