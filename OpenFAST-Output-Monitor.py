# Developed by Araz Hamayeli Mehrabani, Flensburg University of Applied Sciences, 1st February 2025

"""
OpenFAST Output Monitor

This script provides real-time and post-processing visualization
of OpenFAST `.out` files using Matplotlib.

Developed for academic and engineering workflows where quick
inspection of simulation outputs is required.
"""


import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import time
import os
import numpy as np
import matplotlib.ticker as ticker

# Load the data file
file_path = r"C:\Users\Araz\Desktop\DLC\animation\DLC12\OPT-20-295-Monopile.out" #change the path to where your output file is stored!
data_start_line = 6  
simulation_time_range = (60, 660)  #change the time range based on the simulation time
simulation_time_step = 0.5  # Timesteps are necessary, make sure to choose the correct value the same as it is in the simulation!

def wait_for_file(file_path, check_interval=1):
    while not os.path.exists(file_path):
        print("Waiting for file to be created...")
        time.sleep(check_interval)
    while os.stat(file_path).st_size == 0:
        print("Waiting for file to start writing...")
        time.sleep(check_interval)


def load_data():
    wait_for_file(file_path)
    # Read column names
    columns = pd.read_csv(file_path, sep='\s+', skiprows=data_start_line, nrows=0).columns.tolist()
    # Read units row
    units = pd.read_csv(file_path, sep='\s+', skiprows=data_start_line+1, nrows=1, header=None).iloc[0].tolist()
    # Read data, skipping the units row
    data = pd.read_csv(file_path, sep='\s+', skiprows=data_start_line+2, header=None, names=columns)
    data = data.apply(pd.to_numeric, errors='coerce')
    
    # defined time steps
    time_column = "Time"

    if time_column in data.columns:
        data = data[
            (data[time_column] >= simulation_time_range[0]) &
            (data[time_column] <= simulation_time_range[1])
        ].copy()

    return data.dropna(subset=["Time"]), dict(zip(columns, units))

# Define separate plot group dictionaries
plot_groups_1 = {
    "Optimus 20MW-295": (["Wind1VelX", "BldPitch1", "RotSpeed", "RotTorq", "RotPwr", "PtfmTDxt"], 
                [1, 1, 1, 0.001, 0.001, 0.001]),
    "Tip Clearance": (["Tip2Twr1", "Tip2Twr2", "Tip2Twr3"], 
                [0.001, 0.001, 0.001, 0.001])
}

#==============================================================================
'''uncomment plot_groups_2 below if you need to plot more groups 
if you did remember to add , plot_groups_2 in the plot_multiple_groups function at the end'''
#==============================================================================
# plot_groups_2 = {
#     "Loads on blade Root_I": (["RootFxb1", "RootFyb1", "RootFzb1", "RootMEdg1", "RootMFlp1", "RootMzb1"], 
#                 [0.001, 0.001, 0.001, 0.001, 0.001, 0.001]),
#     "Loads on blade Root_II": (["RootFxc1", "RootFyc1", "RootFzc1", "RootMzc1", "RootMzc2", "RootMzc3"], 
#                 [0.001, 0.001, 0.001, 0.001, 0.001, 0.001])
# }



#==============================================================================
'''uncomment plot_groups_3 below if you need to plot more groups
if you did remember to add , plot_groups_3 in the plot_multiple_groups function at the end'''
#==============================================================================
# plot_groups_3 = {
#     "Loads on Tower Top_I": (["YawBrFxp", "YawBrFyp", "YawBrFzp"], 
#                 [0.001, 0.001, 0.001]),
#     "Loads on Tower Top_II": (["YawBrMxp", "YawBrMyp", "YawBrMzp"], 
#                 [0.001, 0.001, 0.001])
# }
#==============================================================================


def plot_multiple_groups(*all_plot_groups, real_time=True, interval=100):
    global data, units
    data, units = load_data()
    figures = []
    animations = []  # Critical for garbage collection

    plt.ion()  # Enable interactive mode

    try:
        for plot_groups in all_plot_groups:
            group_items = list(plot_groups.items())
            num_groups = len(group_items)
            fig, axes = plt.subplots(num_groups, 1, figsize=(10, 6 * num_groups), constrained_layout=True)
            figures.append(fig)

            if num_groups == 1:
                axes = [axes]

            if real_time:
                # Real-time animation logic
                lines_dict = {}
                time_vals = np.arange(
                    simulation_time_range[0], 
                    simulation_time_range[1] + simulation_time_step, 
                    simulation_time_step
                )

                for ax, (group_name, (cols, scales)) in zip(axes, group_items):
                    ax.set_xlim(simulation_time_range)
                    ax.set_title(group_name)
                    ax.grid(True)
                    lines = []
                    for col, scale in zip(cols, scales):
                        unit = f" {units.get(col, '-')}" if col in units else ""
                        line, = ax.plot([], [], label=f"{col}{unit} ({scale})")
                        lines.append((line, col, scale))
                    ax.legend(loc="upper left", bbox_to_anchor=(1, 1))
                    
                    ax.set_xlabel("Time (s)")
                    ax.set_ylabel("Scaled Values")
                    
                    lines_dict[group_name] = (ax, lines)

                def make_update_func(current_lines, current_time_vals):
                    def update(frame):
                        global data
                        data, _ = load_data()
                        if data.empty:
                            return []
                        for group_name, (ax, lines) in current_lines.items():
                            y_min, y_max = np.inf, -np.inf
                            for line, col, scale in lines:
                                if col in data.columns and not data[col].empty:
                                    scaled = data[col].iloc[:len(current_time_vals)] * scale
                                    line.set_data(current_time_vals[:len(scaled)], scaled)
                                    y_min = min(y_min, scaled.min())
                                    y_max = max(y_max, scaled.max())
                        # Add a margin to the y-axis limits (e.g., 5% above and below the data range)
                            margin = 0.05  # 5% margin
                            if np.isfinite(y_min) and np.isfinite(y_max):
                                y_range = y_max - y_min
                                ax.set_ylim(y_min - margin * y_range, y_max + margin * y_range)
                                # Dynamically adjust major and minor tick intervals
                                ideal_ticks = 6  # Aim for ~6 major ticks
                                tick_step = round(y_range / ideal_ticks, -int(np.floor(np.log10(y_range / ideal_ticks))))  # Rounded step

                                ax.yaxis.set_major_locator(ticker.MultipleLocator(tick_step))
                                ax.yaxis.set_minor_locator(ticker.MultipleLocator(tick_step / 5))  # Minor ticks 5x finer

                # Add horizontal grid lines for better readability
                                ax.grid(True, which='major', linestyle='--', linewidth=0.7, alpha=0.7)  # Major grid
                                ax.grid(True, which='minor', linestyle=':', linewidth=0.5, alpha=0.5)  # Minor grid
                            ax.relim()
                            ax.autoscale_view()
                        return []
                    return update


                ani = FuncAnimation(
                    fig, 
                    make_update_func(lines_dict, time_vals), 
                    interval=interval, 
                    blit=False,
                    cache_frame_data=False  # Reduce memory leaks
                )
                animations.append(ani)

                # Handling the closing of figures gracefully
                def on_close(event):
                    # Stop the animation and cleanup
                    for ani in animations:
                        ani.event_source.stop()
                    plt.close(fig)

                fig.canvas.mpl_connect('close_event', on_close)

            else:
                # Static plotting implementation
                time_vals = np.arange(
                    simulation_time_range[0], 
                    simulation_time_range[1] + simulation_time_step, 
                    simulation_time_step
                )[:len(data)]

                for ax, (group_name, (cols, scales)) in zip(axes, group_items):
                    ax.set_xlim(simulation_time_range)
                    ax.set_title(group_name)
                    ax.grid(True)
                    for col, scale in zip(cols, scales):
                        if col in data.columns:
                            unit = f" {units.get(col, '-')}" if col in units else ""
                            ax.plot(time_vals, data[col] * scale, label=f"{col}{unit} ({scale})")
                    ax.legend(loc="upper left", bbox_to_anchor=(1, 1))
                    ax.set_xlabel("Time (s)")
                    ax.set_ylabel("Scaled Values")

        plt.show(block=True)  # Keep figures responsive

    except Exception as e:
        print(f"Error during animation: {e}")

    finally:
        # Cleanup on exit (ensuring resources are released even if errors occur)
        for ani in animations:
            ani.event_source.stop()
        for fig in figures:
            plt.close(fig)

if __name__ == "__main__":
    plot_multiple_groups(plot_groups_1, real_time=True)  # Test real-time mode

    # add , plot_groups_3 if you need to plot more groups
    # add , plot_groups_2 if you need to plot more groups

