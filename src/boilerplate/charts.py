import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
            
KM = 1.496e+8 # au
    
def main():
    # Get simulation metadata
    with open('meta.json', 'r') as f:
        meta = json.loads(f.read())
        
    # Create charts folder
    if(not os.path.exists('charts')):
        os.makedirs('charts')
    
    if(meta['simulation_type'] == 'default'):
        plot_charts_for_default_simulation(meta)
    elif(meta['simulation_type'] == 'grid'):
        plot_charts_for_grid_simulation(meta)


def plot_charts_for_default_simulation(meta):
    pass


def plot_charts_for_grid_simulation(meta):
    grid_options = meta['grid']             # Information of the grid.
    n_grid = grid_options['N']              # Grid size   
    particle = grid_options['particle']     # Information of the dynamic particle
    
    x_range = particle['a']                 # X range of the grid
    y_range = particle['e']                 # Y range of the grid
    
    # Megno chart
    megnos = pd.read_csv('results/megnos.csv')['megno']
    z_values = np.array(megnos).reshape(n_grid, n_grid)
    plot_heatmap(
        x_range, y_range, z_values, vmin=1.9, vmax=4.0,
        x_label='Semi-major axis $a$', 
        y_label='Eccentricity $e$', 
        z_label="Megno $\\langle Y \\rangle$", 
        title='Megno', 
        figname='charts/megno.png'
    )

    p_index = len(meta['particles']) - 1                            # Dynamic particle index
    dynamic_particle_data = pd.read_csv(f'results/orbits_p{p_index+1:03d}.csv')

    # Delta a chart for the dynamic particle 
    delta_as = dynamic_particle_data['delta_a']                     # List of delta a for each simulation
    delta_as_km = [abs(a) * KM for a in delta_as]                   # Convert delta a from AU to KM
    vmin, vmax = min(delta_as_km), max(delta_as_km)                 # Range of z values in chart
    z_values = np.array(delta_as_km).reshape(n_grid, n_grid)
    plot_heatmap(x_range, y_range, z_values, vmin=vmin, vmax=vmax,
        x_label='Semi-major axis $a$ (AU)', 
        y_label='Eccentricity $e$', 
        z_label='delta a (KM)', 
        title='delta_a', 
        figname='charts/delta_a.png'
    )
    
    # Delta e chart for the dynamic particle
    delta_es = dynamic_particle_data['delta_a']                     # List of delta a for each simulation
    delta_es = [abs(e) for e in delta_es]                           # Convert delta a from AU to KM
    vmin, vmax = min(delta_es), max(delta_es)                       # Range of z values in chart
    z_values = np.array(delta_es).reshape(n_grid, n_grid)
    plot_heatmap(x_range, y_range, z_values, vmin=vmin, vmax=vmax,
        x_label='Semi-major axis $a$ (AU)', 
        y_label='Eccentricity $e$', 
        z_label='delta $e$', 
        title='delta_e', 
        figname='charts/delta_e.png'
    )
    

def plot_heatmap(x_range, y_range, z_values, x_label, y_label, z_label, title, vmin, vmax, figname='result.png'):
    ''' This function plots a heatmap and saves the figure.'''
    fig = plt.figure(figsize=(7,5))
    ax = plt.subplot(111)
    ax.set_title(title)
    ax.set_xlim(x_range[0], x_range[1])
    ax.set_xlabel(x_label)
    ax.set_ylim(y_range[0], y_range[1])
    ax.set_ylabel(y_label)
    im = ax.imshow(z_values, interpolation="none", vmin=vmin, vmax=vmax, cmap="jet", origin="lower", aspect='auto', extent=x_range + y_range)
    cb = plt.colorbar(im, ax=ax)
    cb.set_label(z_label)
    fig.savefig(figname)
    
    
if(__name__ == '__main__'):
    main()