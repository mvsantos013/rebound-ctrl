import json
import numpy as np
import matplotlib.pyplot as plt

KM = 1.496e+8 # au
    
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
    # Open simulation metadata
    with open('meta.json', 'r') as f:
        meta = json.loads(f.read())
        
    # Open simulation results
    with open('results.json', 'r') as f:
        results = json.loads(f.read())
    
    grid_options = meta['grid']             # Information of the grid.
    n_grid = grid_options['N']              # Grid size   
    particle = grid_options['particle']     # Information of the dynamic particle
    
    x_range = particle['a']                 # X range of the grid
    y_range = particle['e']                 # Y range of the grid
    
    
    # Megno chart
    megnos = results['results']['megnos'] 
    z_values = np.array(megnos).reshape(n_grid, n_grid)
    vmin, vmax = 1.9, 4.0
    plot_heatmap(
        x_range, y_range, z_values, 
        x_label='Semi-major axis $a$', y_label='Eccentricity $e$', z_label="Megno $\\langle Y \\rangle$", title='Megno', 
        vmin=vmin, vmax=vmax, figname='HD_73583_megno.png'
    )


    # Delta a chart for the dynamic particle in the simulation
    p_index = 1                                                     # Particle index
    delta_as = results['results']['delta_a']                        # List of delta a for each simulation
    delta_as_km = [abs(a[p_index]) * KM for a in delta_as]          # Convert delta a from AU to KM
    vmin, vmax = min(delta_as_km), max(delta_as_km)                 # Range of z values in chart
    z_values = np.array(delta_as_km).reshape(n_grid, n_grid)
    plot_heatmap(x_range, y_range, z_values, 
        x_label='Semi-major axis $a$ (AU)', y_label='Eccentricity $e$', z_label='delta a (KM)', title='HD 73583 c delta_a 100 years', 
        vmin=vmin, vmax=vmax, figname='HD_73583_c_delta_a.png'
    )
    
    # Delta e chart for the dynamic particle in the simulation
    p_index = 1                                                     # Particle index
    delta_es = results['results']['delta_e']                        # List of delta e for each simulation
    delta_es= [abs(e[p_index]) for e in delta_es]                   # Take absolute value of delta e
    vmin, vmax = min(delta_es), max(delta_es)                       # Range of z values in chart
    z_values = np.array(delta_es).reshape(n_grid, n_grid)
    plot_heatmap(x_range, y_range, z_values, 
        x_label='Semi-major axis $a$ (AU)', y_label='Eccentricity $e$', z_label='delta e', title='HD 73583 c delta_e 100 years', 
        vmin=vmin, vmax=vmax, figname='HD_73583_c_delta_e.png'
    )