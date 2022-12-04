import os
import rebound
import math
import time
import json
import numpy as np
import pandas as pd
import multiprocessing
import matplotlib.pyplot as plt
from datetime import datetime, timezone

simulations_finished = multiprocessing.Value('i', 0)                 # Number of simulations finished   

class GridSimulation():
    def __init__(self, inputs):
        self.inputs = inputs
        self.simulation_id = inputs['id']
        self.simulation_type = inputs['simulation_type']             # Simulation type (default or grid)
        self.cores = inputs['cores']                                 # Number of processor cores to use
        self.integrator = inputs['integrator']                       # Integrator to use
        self.years = inputs['years']                                 # 100 years
        self.number_of_logs = inputs['num_logs']                     # Number of logs
        self.ejection_max_distance = inputs['ejection_max_distance'] # Max distance from center of mass
        self.timestep = inputs['timestep']                           # Timestep of the simulation
        self.grid_options = inputs['grid']                           # Grid options
        self.start_time = time.time()
        self.num_simulations = self.grid_options['N'] ** 2           # Number of simulations
        self.D = max(int(self.num_simulations / self.number_of_logs), 1)  # Number of simulations per log line                           
    
    def prepare_params(self):
        n_grid = self.grid_options['N']
        
        # Identify attributes ranges
        ranges = {}
        particle = self.grid_options['particle']
        for attr in particle:
            if(type(particle[attr]) == list):
                ranges[attr] = np.linspace(particle[attr][0], particle[attr][1], n_grid)
        x_attr, y_attr = list(ranges.keys())
        
        # Create parameters for each simulation
        params = []
        for y in ranges[y_attr]:
            for x in ranges[x_attr]:
                particles = self.inputs['particles'].copy()
                particles.append({**particle, x_attr: x, y_attr: y})
                params.append(particles)
                
        return params
    
    def run(self, particles):
        ''' Run simulation based on parameters. '''
        sim = rebound.Simulation()                             # Create simulation object
        sim.integrator = self.integrator                       # Set integrator
        sim.dt = self.timestep * (2*math.pi)                   # Set timestep

        for particle in particles:
            for attr in particle:
                particle[attr] = float(particle[attr])
            sim.add(**particle)                                # Add particle to the simulation

        sim.move_to_com()                                      # Move objects to the center of momentum frame

        sim.init_megno(seed=0)                                 # Setup Megno chaos indicator
        sim.exit_max_distance = self.ejection_max_distance     # Max distance from center of mass
        
        error = None
        try:
            sim.integrate(self.years * (2*math.pi))              # Run simulation
        except Exception as e:
            error = e
    
        result = self.calculate_result(sim, error, particles)
        
        # After every D simulations, log the progress
        global simulations_finished
        with simulations_finished.get_lock():
            simulations_finished.value = simulations_finished.value + 1
            should_log = simulations_finished.value % self.D == 0
            if(should_log):
                progress = simulations_finished.value / (self.num_simulations) * 100
                time_elapsed = time.time() - self.start_time
                eta = 100 * time_elapsed / progress - time_elapsed if progress else 0
                print(f'{simulations_finished.value}/{self.num_simulations} ({progress:.2f}% | {time_elapsed/60:.2f} min | {eta/60:.2f} min ETA)')
        
        return result

    def calculate_result(self, sim, error, particles):
        ''' Calculate result of the simulation. '''

        # Final orbit data by particle
        orbits = []
        i = 0
        for final_orbit in sim.calculate_orbits():
            inital_orbit = particles[i+1]
            orbit = {
                'a': final_orbit.a,
                'e': final_orbit.e,
                'inc': final_orbit.inc,
                'Omega': final_orbit.Omega,
                'omega': final_orbit.omega,
                'M': final_orbit.M,
                'delta_a': final_orbit.a - inital_orbit.get('a', 0),
                'delta_e': final_orbit.e - inital_orbit.get('e', 0)
            }
            orbits.append(orbit)
            i += 1
        
        # Check if there was an error 
        if(error):                                                  
            megno = 10.0
            return megno, orbits
        
        megno = sim.calculate_megno()
        return megno, orbits
    
    
    def export_results(self, results):
        end_time = time.time()
        
        # General result
        result = {
            'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
            'end_time': datetime.fromtimestamp(end_time).isoformat(),
            'duration_time': (end_time - self.start_time) / 60 / 60,
            'status': 'finished',
        }
        
        megnos = []
        particles_orbits = [[] for _ in results[0][1]] 
        for sim_result in results:
            megno, orbits = sim_result
            megnos.append(megno)
            
            i = 0
            for orbit in orbits:
                particles_orbits[i].append(orbit)
                i += 1
            
        # Exports results.json file    
        with open('results/results.json', 'w') as f:
            json.dump(result, f, indent=4)
            
        # Exports megnos.csv file    
        df = pd.DataFrame(megnos, columns=['megno'])
        df.to_csv('results/megnos.csv', index=False, header=True)
        
        # Exports orbits file for each particle
        i = 1
        for particle_data in particles_orbits:
            df = pd.DataFrame(particle_data)
            df.to_csv(f'results/orbits_p{i:03d}.csv', index=False, header=True)
            i += 1